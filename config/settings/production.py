"""
Production settings for experiencer-platform project.
For Railway deployment.
"""

from .base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Database Configuration
# Railway provides DATABASE_URL when PostgreSQL is added
import os
import dj_database_url

# Use PostgreSQL if DATABASE_URL is set, otherwise fallback to SQLite
database_url = config('DATABASE_URL', default=None)

if database_url:
    # PostgreSQL (Production)
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite Fallback
    db_path = config('DATABASE_PATH', default='/tmp/db.sqlite3')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }
    }

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
