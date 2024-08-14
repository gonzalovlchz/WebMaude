#!/bin/bash

# Ejecutar migraciones
/app/.venv/bin/python manage.py migrate

# Iniciar Gunicorn
exec gunicorn -w 3 WebMaude.wsgi:application -b 0.0.0.0:8000
