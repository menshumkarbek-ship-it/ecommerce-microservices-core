import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _  # 🌐 Translation Engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings loaded from .env
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-development-key')

# Convert DEBUG string from .env to boolean (default to False if not set)
DEBUG = os.getenv('DEBUG', 'False').strip().lower() == 'true'

# Parse comma-separated string from .env into a list
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # 🌐 Multi-language engine
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # 🌐 Language context
                'shop.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
# 🛰️ Enable the asynchronous server gateway interface routing matrix
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration loaded dynamically from .env
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'mobile_shop_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==========================================
# 🌐 INTERNATIONALIZATION & MULTI-LANGUAGE
# ==========================================

LANGUAGE_CODE = 'en'  # Default Language

LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
    ('ky', _('Kyrgyz')),
]

# Directory where translation files (.po / .mo) will be stored
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# ==========================================
# 📁 MEDIA & STATIC FILES
# ==========================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Base url to serve media files
MEDIA_URL = '/media/'

# Path where media files are physically stored on your computer
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Session key for the shopping cart
CART_SESSION_ID = 'techvault_cart'

# ==========================================
# 📑 DRF & API DOCUMENTATION SETTINGS
# ==========================================

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TechVault Core E-Commerce API',
    'DESCRIPTION': 'Core API catalog for products, categories, and inventory management.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# 🏎️ LOCAL RECONFIGURED CACHING INFRASTRUCTURE (For running without Docker)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'techvault-catalog',
    }
}

# ==========================================
# ⚡ CELERY & REDIS TASK QUEUE SETTINGS
# ==========================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Force Redis driver to use RESP2 protocol to prevent HELLO command errors
CELERY_BROKER_TRANSPORT_OPTIONS = {'protocol_version': 2}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# 🔒 HTTPS & PRODUCTION SECURITY SETTINGS
# ==========================================

if not DEBUG:
    # Force HTTP requests to redirect to HTTPS
    SECURE_SSL_REDIRECT = True

    # Send cookies over HTTPS only
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HTTP Strict Transport Security (HSTS)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Inform Django it is behind a reverse proxy (Render / Vercel router)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
