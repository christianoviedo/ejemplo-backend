from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [
        ('admin', 'Admin'),
        ('gestor', 'Gestor'),
        ('consulta', 'Consulta'),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='consulta')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Bodega(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, default='')
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Bodega'
        verbose_name_plural = 'Bodegas'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, default='')
    unidad = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f'{self.sku} - {self.nombre}'


class Stock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stocks')
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='stocks')
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        unique_together = ('producto', 'bodega')
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return f'{self.producto.sku} en {self.bodega.nombre}: {self.cantidad}'


class Movimiento(models.Model):
    TIPOS = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('transferencia', 'Transferencia'),
    ]
    tipo = models.CharField(max_length=15, choices=TIPOS)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    bodega_origen = models.ForeignKey(
        Bodega, null=True, blank=True, on_delete=models.PROTECT,
        related_name='movimientos_salida',
    )
    bodega_destino = models.ForeignKey(
        Bodega, null=True, blank=True, on_delete=models.PROTECT,
        related_name='movimientos_entrada',
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    nota = models.TextField(blank=True, default='')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='movimientos')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.tipo} - {self.producto.sku} - {self.cantidad}'
