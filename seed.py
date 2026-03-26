"""
Script para poblar la BD con datos de ejemplo.
Ejecutar: python seed.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bodega.settings')
django.setup()

from django.db import transaction
from api.models import User, Bodega, Producto, Stock, Movimiento

print("Limpiando datos previos...")
Movimiento.objects.all().delete()
Stock.objects.all().delete()
Producto.objects.all().delete()
Bodega.objects.all().delete()
User.objects.all().delete()

print("Creando usuarios...")
admin = User.objects.create_superuser(
    username='admin',
    password='admin123',
    email='admin@bodega.cl',
    role='admin',
    first_name='Admin',
    last_name='Sistema',
)
gestor = User.objects.create_user(
    username='gestor1',
    password='gestor123',
    email='gestor@bodega.cl',
    role='gestor',
    first_name='María',
    last_name='González',
)
consulta = User.objects.create_user(
    username='consulta1',
    password='consulta123',
    email='consulta@bodega.cl',
    role='consulta',
    first_name='Juan',
    last_name='Pérez',
)

print("Creando bodegas...")
b_central = Bodega.objects.create(
    nombre='Bodega Central',
    descripcion='Bodega principal de almacenamiento',
    activa=True,
)
b_norte = Bodega.objects.create(
    nombre='Bodega Norte',
    descripcion='Sucursal zona norte',
    activa=True,
)
b_sur = Bodega.objects.create(
    nombre='Bodega Sur',
    descripcion='Sucursal zona sur',
    activa=True,
)
b_taller = Bodega.objects.create(
    nombre='Taller',
    descripcion='Bodega de insumos para taller',
    activa=True,
)

print("Creando productos...")
productos_data = [
    ('TORN-M8-50',  'Tornillo M8x50mm',         'unidad',  'Tornillo métrico de acero'),
    ('TORN-M6-30',  'Tornillo M6x30mm',          'unidad',  'Tornillo métrico M6'),
    ('TUERCA-M8',   'Tuerca M8',                 'unidad',  'Tuerca hexagonal M8'),
    ('CABLE-14',    'Cable eléctrico 14AWG',      'metro',   'Cable cobre THW 14AWG'),
    ('CABLE-12',    'Cable eléctrico 12AWG',      'metro',   'Cable cobre THW 12AWG'),
    ('ACEITE-10W',  'Aceite Motor 10W-40',        'litro',   'Aceite multigrado 10W-40'),
    ('ACEITE-HID',  'Aceite Hidráulico ISO 46',   'litro',   'Aceite hidráulico ISO 46'),
    ('FILTRO-A1',   'Filtro de Aire A1',          'unidad',  'Filtro de aire industrial'),
    ('FILTRO-H1',   'Filtro Hidráulico H1',       'unidad',  'Filtro hidráulico retorno'),
    ('GUANTE-M',    'Guante de Seguridad Talla M','par',     'Guante nitrilo talla M'),
    ('GUANTE-L',    'Guante de Seguridad Talla L','par',     'Guante nitrilo talla L'),
    ('CASCO-B',     'Casco Seguridad Blanco',     'unidad',  'Casco ANSI Z89.1 blanco'),
    ('RODAMIENTO-6205', 'Rodamiento 6205',        'unidad',  'Rodamiento rígido de bolas 6205'),
    ('RODAMIENTO-6206', 'Rodamiento 6206',        'unidad',  'Rodamiento rígido de bolas 6206'),
    ('GRASA-LIT',   'Grasa Litio Multipropósito','kilogramo','Grasa litio NLGI 2'),
]

productos = {}
for sku, nombre, unidad, desc in productos_data:
    p = Producto.objects.create(sku=sku, nombre=nombre, unidad=unidad, descripcion=desc)
    productos[sku] = p

print("Registrando movimientos de entrada (stock inicial)...")
entradas_central = [
    ('TORN-M8-50', 5000), ('TORN-M6-30', 3000), ('TUERCA-M8', 4000),
    ('CABLE-14', 500),    ('CABLE-12', 300),
    ('ACEITE-10W', 200),  ('ACEITE-HID', 150),
    ('FILTRO-A1', 80),    ('FILTRO-H1', 60),
    ('GUANTE-M', 200),    ('GUANTE-L', 150),   ('CASCO-B', 50),
    ('RODAMIENTO-6205', 100), ('RODAMIENTO-6206', 80), ('GRASA-LIT', 40),
]

with transaction.atomic():
    for sku, qty in entradas_central:
        Movimiento.objects.create(
            tipo='entrada',
            producto=productos[sku],
            bodega_destino=b_central,
            cantidad=qty,
            nota='Stock inicial carga masiva',
            usuario=admin,
        )
        stock, _ = Stock.objects.get_or_create(producto=productos[sku], bodega=b_central, defaults={'cantidad': 0})
        stock.cantidad += qty
        stock.save()

print("Registrando transferencias a bodegas secundarias...")
transferencias = [
    # (sku, origen, destino, cantidad, nota)
    ('TORN-M8-50', b_central, b_norte, 500,  'Reposición mensual norte'),
    ('TORN-M8-50', b_central, b_sur,   500,  'Reposición mensual sur'),
    ('TORN-M6-30', b_central, b_norte, 300,  'Reposición mensual norte'),
    ('CABLE-14',   b_central, b_taller,100,  'Dotación inicial taller'),
    ('CABLE-12',   b_central, b_taller, 50,  'Dotación inicial taller'),
    ('ACEITE-10W', b_central, b_taller, 50,  'Aceite para mantenimiento'),
    ('ACEITE-HID', b_central, b_taller, 30,  'Aceite hidráulico taller'),
    ('FILTRO-A1',  b_central, b_taller, 20,  'Filtros para taller'),
    ('GUANTE-M',   b_central, b_norte,  40,  'EPP norte'),
    ('GUANTE-L',   b_central, b_norte,  30,  'EPP norte'),
    ('CASCO-B',    b_central, b_norte,  10,  'EPP norte'),
    ('RODAMIENTO-6205', b_central, b_taller, 20, 'Rodamientos taller'),
]

with transaction.atomic():
    for sku, origen, destino, qty, nota in transferencias:
        Movimiento.objects.create(
            tipo='transferencia',
            producto=productos[sku],
            bodega_origen=origen,
            bodega_destino=destino,
            cantidad=qty,
            nota=nota,
            usuario=gestor,
        )
        s_origen = Stock.objects.get(producto=productos[sku], bodega=origen)
        s_origen.cantidad -= qty
        s_origen.save()
        s_destino, _ = Stock.objects.get_or_create(producto=productos[sku], bodega=destino, defaults={'cantidad': 0})
        s_destino.cantidad += qty
        s_destino.save()

print("Registrando algunas salidas (consumo)...")
salidas = [
    ('GUANTE-M',  b_central, 30, 'Consumo mensual operaciones'),
    ('GUANTE-L',  b_central, 20, 'Consumo mensual operaciones'),
    ('CASCO-B',   b_central,  5, 'Reposición cascos dañados'),
    ('ACEITE-10W',b_taller,  15, 'Cambio aceite maquinaria'),
    ('FILTRO-A1', b_taller,   5, 'Cambio filtros mes'),
    ('CABLE-14',  b_taller,  30, 'Instalación sala eléctrica'),
    ('RODAMIENTO-6205', b_taller, 4, 'Reemplazo rodamientos torno'),
]

with transaction.atomic():
    for sku, bodega, qty, nota in salidas:
        Movimiento.objects.create(
            tipo='salida',
            producto=productos[sku],
            bodega_origen=bodega,
            cantidad=qty,
            nota=nota,
            usuario=gestor,
        )
        stock = Stock.objects.get(producto=productos[sku], bodega=bodega)
        stock.cantidad -= qty
        stock.save()

print("\n✓ Datos de ejemplo cargados exitosamente.")
print("\nUsuarios creados:")
print("  admin     / admin123    (rol: admin)")
print("  gestor1   / gestor123   (rol: gestor)")
print("  consulta1 / consulta123 (rol: consulta)")
print(f"\nBodegas: {Bodega.objects.count()}")
print(f"Productos: {Producto.objects.count()}")
print(f"Registros de stock: {Stock.objects.count()}")
print(f"Movimientos: {Movimiento.objects.count()}")
