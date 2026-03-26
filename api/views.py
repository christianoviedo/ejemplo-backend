from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, serializers as drf_serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Bodega, Movimiento, Producto, Stock, User
from .permissions import IsAdmin, IsGestorOrAdmin
from .serializers import (
    BodegaSerializer,
    CustomTokenObtainPairSerializer,
    MovimientoCreateSerializer,
    MovimientoSerializer,
    ProductoSerializer,
    StockSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by('id')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer


class BodegaViewSet(viewsets.ModelViewSet):
    queryset = Bodega.objects.all().order_by('id')
    serializer_class = BodegaSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('id')
    serializer_class = ProductoSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]


class StockViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Stock.objects.select_related('producto', 'bodega').all()
        bodega = self.request.query_params.get('bodega')
        search = self.request.query_params.get('search')

        if bodega:
            qs = qs.filter(bodega_id=bodega)
        if search:
            qs = qs.filter(
                Q(producto__sku__icontains=search) | Q(producto__nombre__icontains=search)
            )
        return qs


class MovimientoViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):

    def get_permissions(self):
        if self.action == 'create':
            return [IsGestorOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return MovimientoCreateSerializer
        return MovimientoSerializer

    def get_queryset(self):
        qs = Movimiento.objects.select_related(
            'producto', 'bodega_origen', 'bodega_destino', 'usuario'
        ).all()

        tipo = self.request.query_params.get('tipo')
        bodega_origen = self.request.query_params.get('bodega_origen')
        bodega_destino = self.request.query_params.get('bodega_destino')
        producto = self.request.query_params.get('producto')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if tipo:
            qs = qs.filter(tipo=tipo)
        if bodega_origen:
            qs = qs.filter(bodega_origen_id=bodega_origen)
        if bodega_destino:
            qs = qs.filter(bodega_destino_id=bodega_destino)
        if producto:
            qs = qs.filter(producto_id=producto)
        if fecha_desde:
            qs = qs.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__date__lte=fecha_hasta)

        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            movimiento = serializer.save(usuario=self.request.user)
            _actualizar_stock(movimiento)


def _actualizar_stock(movimiento):
    tipo = movimiento.tipo
    producto = movimiento.producto
    cantidad = movimiento.cantidad

    if tipo == 'entrada':
        # Garantiza que exista el registro antes de bloquearlo
        Stock.objects.get_or_create(
            producto=producto,
            bodega=movimiento.bodega_destino,
            defaults={'cantidad': 0},
        )
        stock = Stock.objects.select_for_update().get(
            producto=producto,
            bodega=movimiento.bodega_destino,
        )
        stock.cantidad += cantidad
        stock.save()

    elif tipo == 'salida':
        try:
            stock = Stock.objects.select_for_update().get(
                producto=producto,
                bodega=movimiento.bodega_origen,
            )
        except Stock.DoesNotExist:
            raise drf_serializers.ValidationError(
                {'error': 'No hay stock registrado para este producto en la bodega de origen.'}
            )
        if stock.cantidad < cantidad:
            raise drf_serializers.ValidationError(
                {'error': f'Stock insuficiente. Disponible: {stock.cantidad}.'}
            )
        stock.cantidad -= cantidad
        stock.save()

    elif tipo == 'transferencia':
        try:
            stock_origen = Stock.objects.select_for_update().get(
                producto=producto,
                bodega=movimiento.bodega_origen,
            )
        except Stock.DoesNotExist:
            raise drf_serializers.ValidationError(
                {'error': 'No hay stock registrado para este producto en la bodega de origen.'}
            )
        if stock_origen.cantidad < cantidad:
            raise drf_serializers.ValidationError(
                {'error': f'Stock insuficiente en origen. Disponible: {stock_origen.cantidad}.'}
            )
        stock_origen.cantidad -= cantidad
        stock_origen.save()

        Stock.objects.get_or_create(
            producto=producto,
            bodega=movimiento.bodega_destino,
            defaults={'cantidad': 0},
        )
        stock_destino = Stock.objects.select_for_update().get(
            producto=producto,
            bodega=movimiento.bodega_destino,
        )
        stock_destino.cantidad += cantidad
        stock_destino.save()
