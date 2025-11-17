#!/bin/bash
# Railway startup script

# Set production settings
export DJANGO_SETTINGS_MODULE=config.settings.production

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
gunicorn config.wsgi:application
