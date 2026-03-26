from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    BodegaViewSet,
    CustomTokenObtainPairView,
    MovimientoViewSet,
    ProductoViewSet,
    StockViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('bodegas', BodegaViewSet, basename='bodega')
router.register('productos', ProductoViewSet, basename='producto')
router.register('stock', StockViewSet, basename='stock')
router.register('movimientos', MovimientoViewSet, basename='movimiento')

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
