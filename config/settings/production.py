"""
Production settings for experiencer-platform project.
For Railway deployment.
"""

from .base import *
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS: Allow all hosts by default for Railway
ALLOWED_HOSTS = ['*']

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

# Security settings - Disabled for Railway deployment
# Enable these in production with proper domain setup
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Static files - WhiteNoise configuration
STATIC_ROOT = '/app/staticfiles'
STATIC_URL = '/static/'

# WhiteNoise - Serve static files without collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
