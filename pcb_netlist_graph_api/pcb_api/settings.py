from __future__ import annotations

import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-not-for-production")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS: list[str] = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.postgres",
    "strawberry_django",
    "catalog",
]

MIDDLEWARE: list[str] = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "pcb_api.urls"
WSGI_APPLICATION = "pcb_api.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "pcbdb"),
        "USER": os.environ.get("POSTGRES_USER", "pcb"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "pcb"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
