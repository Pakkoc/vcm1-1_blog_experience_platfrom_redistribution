#!/bin/bash
# Railway startup script

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
gunicorn config.wsgi:application
