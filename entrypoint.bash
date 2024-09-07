#!/bin/bash

# Apply migrations first to ensure the database schema is up-to-date
/app/.venv/bin/python manage.py makemigrations
/app/.venv/bin/python manage.py migrate

# Create a superuser if it doesn't already exist
export DJANGO_SUPERUSER_PASSWORD='root'
/app/.venv/bin/python manage.py createsuperuser --noinput --username root --email '' || true

# Start Gunicorn or Django's development server
# Uncomment the following line to use Gunicorn in production
/app/.venv/bin/python -m gunicorn --env "SCRIPT_NAME=/web" -w 3 WebMaude.wsgi:application -b 0.0.0.0:8000

# For development, use Django's built-in server
#/app/.venv/bin/python manage.py runserver 0.0.0.0:8000
