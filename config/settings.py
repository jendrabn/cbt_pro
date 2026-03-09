"""
Django settings for CBT project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes", "on")


def _env_list(name, default=""):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _env_json(name, default):
    raw_value = os.getenv(name, default)
    try:
        return json.loads(str(raw_value).replace("'", '"'))
    except json.JSONDecodeError:
        return json.loads(str(default).replace("'", '"'))


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

CBT_SITE_NAME = os.getenv('CBT_SITE_NAME', 'Sistem CBT')
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '628xxxxxxxxxx')

DEBUG = _env_bool('DEBUG', True)

ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = _env_list('CSRF_TRUSTED_ORIGINS')
USE_X_FORWARDED_HOST = _env_bool('USE_X_FORWARDED_HOST', not DEBUG)

if _env_bool('SECURE_PROXY_SSL_HEADER_ENABLED', not DEBUG):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.users",
    "apps.subjects",
    "apps.questions",
    "apps.exams",
    "apps.attempts",
    "apps.monitoring",
    "apps.results",
    "apps.proctoring",
    "apps.notifications",
    "apps.analytics",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.branding_context",
                "apps.core.context_processors.asset_version_context",
                "apps.core.context_processors.auth_feature_context",
                "apps.notifications.context_processors.topbar_notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

db_options = _env_json('DB_OPTIONS', "{'charset': 'utf8mb4'}")

DATABASES = {
    "default": {
        "ENGINE": os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        "NAME": os.getenv('DB_NAME', 'cbt_database'),
        "USER": os.getenv('DB_USER', 'root'),
        "PASSWORD": os.getenv('DB_PASSWORD', ''),
        "HOST": os.getenv('DB_HOST', 'localhost'),
        "PORT": os.getenv('DB_PORT', '3306'),
        "OPTIONS": db_options,
        "CONN_MAX_AGE": int(os.getenv('DB_CONN_MAX_AGE', '600')),
        "CONN_HEALTH_CHECKS": _env_bool('DB_CONN_HEALTH_CHECKS', True),
    }
}


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'id')

TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Jakarta')

USE_I18N = True

USE_TZ = _env_bool('USE_TZ', True)


# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / os.getenv('STATIC_ROOT', 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')


# =============================================================================
# FRONTEND INTEGRATIONS
# =============================================================================

TINYMCE_API_KEY = os.getenv('TINYMCE_API_KEY', '').strip()


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'CBT System <noreply@cbt.com>')


# =============================================================================
# IMPORT PROCESSING
# =============================================================================

USER_IMPORT_MAX_ROWS = int(os.getenv("USER_IMPORT_MAX_ROWS", "5000"))
USER_IMPORT_CHUNK_SIZE = int(os.getenv("USER_IMPORT_CHUNK_SIZE", "250"))
QUESTION_IMPORT_MAX_ROWS = int(os.getenv("QUESTION_IMPORT_MAX_ROWS", "10000"))
QUESTION_IMPORT_CHUNK_SIZE = int(os.getenv("QUESTION_IMPORT_CHUNK_SIZE", "200"))


# =============================================================================
# CELERY & REDIS CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'Asia/Jakarta')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SYNC_FALLBACK = _env_bool("CELERY_TASK_SYNC_FALLBACK", True)


# =============================================================================
# SECURITY SETTINGS (Production)
# =============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', True)
    CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', True)
    SECURE_BROWSER_XSS_FILTER = _env_bool('SECURE_BROWSER_XSS_FILTER', True)
    SECURE_CONTENT_TYPE_NOSNIFF = _env_bool('SECURE_CONTENT_TYPE_NOSNIFF', True)
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
    SECURE_HSTS_PRELOAD = _env_bool('SECURE_HSTS_PRELOAD', False)
    X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')


# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}


# =============================================================================
# PROCTORING SETTINGS
# =============================================================================

ENABLE_SCREENSHOT_PROCTORING = _env_bool('ENABLE_SCREENSHOT_PROCTORING', False)
SCREENSHOT_INTERVAL_SECONDS = int(os.getenv('SCREENSHOT_INTERVAL_SECONDS', '300'))
MAX_VIOLATIONS_ALLOWED = int(os.getenv('MAX_VIOLATIONS_ALLOWED', '3'))


# =============================================================================
# DJANGO DEFAULTS
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "accounts.User"


# =============================================================================
# AUTHENTICATION SETTINGS
# =============================================================================

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.UsernameOrEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
