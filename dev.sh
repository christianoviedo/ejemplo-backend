#!/usr/bin/env bash
set -e

# ── Verificar .env ────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "No existe .env — copiando desde .env.example..."
  cp .env.example .env
  echo "Edita .env con tus valores reales y vuelve a ejecutar."
  exit 1
fi

# ── Entorno virtual ───────────────────────────────────────────────────────────
if [ ! -d .venv ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# ── Dependencias ──────────────────────────────────────────────────────────────
echo "Instalando dependencias..."
pip install -q -r requirements.txt

# ── Base de datos ─────────────────────────────────────────────────────────────
echo "Aplicando migraciones..."
python manage.py migrate --run-syncdb

# ── Superusuario (solo si no existe ninguno) ──────────────────────────────────
USER_COUNT=$(python manage.py shell -c "from api.models import User; print(User.objects.filter(is_superuser=True).count())" 2>/dev/null)
if [ "$USER_COUNT" = "0" ]; then
  echo ""
  echo "No hay superusuario — creando uno ahora:"
  python manage.py createsuperuser
fi

# ── Servidor ──────────────────────────────────────────────────────────────────
echo ""
echo "API disponible en http://127.0.0.1:8000/"
echo "Admin en       http://127.0.0.1:8000/admin/"
echo ""
python manage.py runserver
