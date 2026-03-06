"""
Django settings for CBT project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

CBT_SITE_NAME = os.getenv('CBT_SITE_NAME', 'Sistem CBT')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Parse database options from environment variable
import json
db_options = {}
try:
    db_options_str = os.getenv('DB_OPTIONS', "{'charset': 'utf8mb4'}")
    db_options = json.loads(db_options_str.replace("'", '"'))
except json.JSONDecodeError:
    db_options = {'charset': 'utf8mb4'}

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
        "CONN_HEALTH_CHECKS": os.getenv('DB_CONN_HEALTH_CHECKS', 'True').lower() in ('true', '1', 'yes'),
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

USE_TZ = os.getenv('USE_TZ', 'True').lower() in ('true', '1', 'yes')


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
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'CBT System <noreply@cbt.com>')


# =============================================================================
# CELERY & REDIS CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'Asia/Jakarta')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# =============================================================================
# SECURITY SETTINGS (Production)
# =============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


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

ENABLE_SCREENSHOT_PROCTORING = os.getenv('ENABLE_SCREENSHOT_PROCTORING', 'False').lower() in ('true', '1', 'yes')
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
