#!/bin/bash

# Ejecutar migraciones
/app/.venv/bin/python manage.py migrate

export DJANGO_SUPERUSER_PASSWORD='root'
/app/.venv/bin/python manage.py createsuperuser --noinput --username root --email ''

# Iniciar Gunicorn
/app/.venv/bin/python -m gunicorn -w 3 WebMaude.wsgi:application -b 0.0.0.0:8000
