#!/bin/bash
set -e

echo "⏳ Esperando base de datos..."
until python3 -c "
import os, psycopg2, dj_database_url
conf = dj_database_url.config(default=os.environ['DATABASE_URL'])
psycopg2.connect(
    dbname=conf['NAME'],
    user=conf['USER'],
    password=conf['PASSWORD'],
    host=conf['HOST'],
    port=conf.get('PORT', 5432),
)
" 2>/dev/null; do
  sleep 1
done
echo "✓ Base de datos disponible"

echo "⏳ Aplicando migraciones..."
python3 manage.py migrate --noinput

echo "⏳ Recolectando archivos estáticos..."
python3 manage.py collectstatic --noinput

echo "🚀 Iniciando Gunicorn..."
exec gunicorn bodega.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
