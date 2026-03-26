from decimal import Decimal

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Bodega, Movimiento, Producto, Stock, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'username', 'email', 'first_name', 'last_name')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bodega
        fields = ('id', 'nombre', 'descripcion', 'activa')


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ('id', 'sku', 'nombre', 'descripcion', 'unidad', 'activo')


class StockSerializer(serializers.ModelSerializer):
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    bodega_nombre = serializers.CharField(source='bodega.nombre', read_only=True)
    unidad = serializers.CharField(source='producto.unidad', read_only=True)

    class Meta:
        model = Stock
        fields = ('id', 'producto', 'bodega', 'cantidad', 'producto_sku', 'producto_nombre', 'bodega_nombre', 'unidad')


class MovimientoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    bodega_origen_nombre = serializers.SerializerMethodField()
    bodega_destino_nombre = serializers.SerializerMethodField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Movimiento
        fields = (
            'id', 'tipo',
            'producto', 'producto_nombre', 'producto_sku',
            'bodega_origen', 'bodega_origen_nombre',
            'bodega_destino', 'bodega_destino_nombre',
            'cantidad', 'nota',
            'usuario', 'usuario_username', 'fecha',
        )

    def get_bodega_origen_nombre(self, obj):
        return obj.bodega_origen.nombre if obj.bodega_origen else None

    def get_bodega_destino_nombre(self, obj):
        return obj.bodega_destino.nombre if obj.bodega_destino else None


class MovimientoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = ('tipo', 'producto', 'bodega_origen', 'bodega_destino', 'cantidad', 'nota')

    def validate_cantidad(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('La cantidad debe ser mayor a cero.')
        return value

    def validate(self, data):
        tipo = data.get('tipo')
        bodega_origen = data.get('bodega_origen')
        bodega_destino = data.get('bodega_destino')

        if tipo == 'entrada':
            if not bodega_destino:
                raise serializers.ValidationError(
                    {'bodega_destino': 'La bodega de destino es requerida para movimientos de entrada.'}
                )
            if bodega_origen is not None:
                raise serializers.ValidationError(
                    {'bodega_origen': 'La bodega de origen debe ser nula para movimientos de entrada.'}
                )

        elif tipo == 'salida':
            if not bodega_origen:
                raise serializers.ValidationError(
                    {'bodega_origen': 'La bodega de origen es requerida para movimientos de salida.'}
                )
            if bodega_destino is not None:
                raise serializers.ValidationError(
                    {'bodega_destino': 'La bodega de destino debe ser nula para movimientos de salida.'}
                )

        elif tipo == 'transferencia':
            if not bodega_origen:
                raise serializers.ValidationError(
                    {'bodega_origen': 'La bodega de origen es requerida para transferencias.'}
                )
            if not bodega_destino:
                raise serializers.ValidationError(
                    {'bodega_destino': 'La bodega de destino es requerida para transferencias.'}
                )
            if bodega_origen == bodega_destino:
                raise serializers.ValidationError(
                    {'bodega_destino': 'La bodega de origen y destino no pueden ser la misma.'}
                )

        return data
