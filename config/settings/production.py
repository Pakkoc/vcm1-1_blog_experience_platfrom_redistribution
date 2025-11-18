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
    # SQLite Fallback with Railway Volume support
    # Railway 볼륨 마운트 경로 (1단계에서 설정한 Mount Path와 일치해야 함)
    VOLUME_MOUNT_PATH = '/data'

    # Railway 환경(볼륨이 마운트된 환경)인지 확인하여 경로를 동적으로 결정
    if os.path.exists(VOLUME_MOUNT_PATH):
        # Railway 볼륨 경로 사용 (영구 저장)
        db_path = os.path.join(VOLUME_MOUNT_PATH, 'db.sqlite3')
    else:
        # 로컬 또는 볼륨 없는 환경 - 임시 경로 사용
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
