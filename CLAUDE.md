# Backend — Sistema de Gestión de Bodega

## Stack

- Python 3.11+ / Django 5.x / Django REST Framework 3.x
- Auth: `djangorestframework-simplejwt`
- CORS: `django-cors-headers`
- DB: PostgreSQL vía `psycopg2-binary` + `dj-database-url`

## Estructura

```
bodega/          proyecto Django (settings, urls raíz, wsgi)
api/             única app: models, serializers, views, permissions, urls
```

## Comandos frecuentes

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py makemigrations api
```

## Modelo de datos

| Modelo      | Campos clave                                                                 |
|-------------|------------------------------------------------------------------------------|
| User        | AbstractUser + `role`: `admin` \| `gestor` \| `consulta`                    |
| Bodega      | nombre, descripcion, activa                                                  |
| Producto    | sku (unique), nombre, descripcion, unidad, activo                            |
| Stock       | producto FK + bodega FK (unique_together), cantidad DecimalField             |
| Movimiento  | tipo (entrada/salida/transferencia), producto, bodega_origen/destino (null), cantidad, nota, usuario, fecha (auto) |

## Endpoints

| Método | URL                        | Acceso            |
|--------|----------------------------|-------------------|
| POST   | /api/auth/token/           | público           |
| POST   | /api/auth/token/refresh/   | público           |
| *      | /api/users/                | solo admin        |
| GET    | /api/bodegas/              | autenticado       |
| POST/PUT/PATCH/DELETE | /api/bodegas/  | solo admin        |
| GET    | /api/productos/            | autenticado       |
| POST/PUT/PATCH/DELETE | /api/productos/ | solo admin       |
| GET    | /api/stock/                | autenticado       |
| GET    | /api/movimientos/          | autenticado       |
| POST   | /api/movimientos/          | gestor + admin    |

### Filtros disponibles

- `GET /api/stock/?bodega=<id>&search=<sku_o_nombre>`
- `GET /api/movimientos/?tipo=&bodega_origen=&bodega_destino=&producto=&fecha_desde=&fecha_hasta=`

## Roles y permisos

- `IsAdmin` → `api/permissions.py`: `role == 'admin'`
- `IsGestorOrAdmin` → `api/permissions.py`: `role in ('gestor', 'admin')`
- El campo `role` se incluye en el JWT payload y en el body de `/api/auth/token/`

## Lógica de stock (crítica)

`api/views._actualizar_stock()` corre dentro de `transaction.atomic()`:

- **entrada**: `get_or_create` el registro de Stock en `bodega_destino`, luego `select_for_update` y suma
- **salida**: `select_for_update` en `bodega_origen`; lanza `ValidationError` si no existe o stock insuficiente
- **transferencia**: resta con lock en origen, crea si no existe y suma con lock en destino

No modificar este patrón sin considerar concurrencia: el `get_or_create` seguido de `select_for_update().get()` es intencional para evitar deadlocks en inserciones concurrentes.

## Convenciones

- Errores de negocio devueltos como `ValidationError` con mensajes en español
- `MovimientoViewSet` expone solo `list` y `create` (sin update/delete por diseño)
- `StockViewSet` expone solo `list`
- No hay soft delete: se usa `is_active` / `activo` como flag
- Sin Celery, Redis ni caché — MVP síncrono
