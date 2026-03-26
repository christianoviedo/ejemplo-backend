from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Bodega, Movimiento, Producto, Stock, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (('Rol', {'fields': ('role',)}),)
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')


@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    list_filter = ('activa',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'unidad', 'activo')
    list_filter = ('activo',)
    search_fields = ('sku', 'nombre')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'bodega', 'cantidad')
    list_filter = ('bodega',)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'producto', 'bodega_origen', 'bodega_destino', 'cantidad', 'usuario', 'fecha')
    list_filter = ('tipo', 'bodega_origen', 'bodega_destino')
    readonly_fields = ('fecha',)
