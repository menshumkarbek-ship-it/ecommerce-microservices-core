import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _  # 🌐 Translation Engine
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Convert DEBUG string from .env to boolean (default to False if not set)
DEBUG = os.getenv('DEBUG', 'False').strip().lower() == 'true'

# Require an explicit secret outside local development.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-development-key'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG=False.')

# Parse comma-separated string from .env into a list. Must be set in
# production (e.g. ALLOWED_HOSTS=your-app.onrender.com) — an empty list
# with DEBUG=False makes Django reject every request, so a forgotten env
# var fails closed instead of silently accepting any Host header.
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]

# 🔒 Django admin is mounted at a non-default path (instead of /admin/) to keep
# it off the beaten path for bots/scanners. Override via .env if needed; the
# trailing slash matters since it's used directly in a urls.py path().
ADMIN_URL = os.getenv('ADMIN_URL', 'system-console/').strip().strip('/') + '/'

# Public domain the site is served from (no scheme, no trailing slash) —
# used to build absolute URLs for the sitemap and robots.txt. Override via
# .env once the real Render service/custom domain is known.
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'techvault-c6us.onrender.com').strip().strip('/')

# The storefront has no customer accounts/login of its own (view-only catalog).
# Staff/managers authenticate through Django's admin login form, wherever
# ADMIN_URL happens to mount it, so @login_required views (the in-app product/
# category/contact management panel) send anonymous visitors there and back.
LOGIN_URL = 'admin:login'

# Send staff back to the storefront home after signing out, instead of
# rendering Django admin's own (jazzmin-styled, visually inconsistent)
# "logged out" confirmation page.
LOGOUT_REDIRECT_URL = 'shop:home'

INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'storages',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',   
    'django.contrib.sitemaps',
    'rest_framework',
    'drf_spectacular',
    'shop',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # 🌐 Language context
                'shop.context_processors.is_admin',
                'shop.context_processors.contact_settings',
                'shop.context_processors.site_identity',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
# 🛰️ Enable the asynchronous server gateway interface routing matrix
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration loaded dynamically from .env
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]

# Base url to serve media files
MEDIA_URL = '/media/'

# Path where media files are physically stored on your computer (used only
# when R2 isn't configured — see STORAGES below).
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudflare R2 (S3-compatible) for uploaded product/about images: a host's
# local disk doesn't survive redeploys, so this must live somewhere durable
# in production. Falls back to local disk automatically when the R2 env
# vars aren't set, so local dev needs no bucket.
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': R2_BUCKET_NAME,
            'access_key': os.getenv('R2_ACCESS_KEY_ID'),
            'secret_key': os.getenv('R2_SECRET_ACCESS_KEY'),
            'endpoint_url': os.getenv('R2_ENDPOINT_URL'),
            'custom_domain': os.getenv('R2_PUBLIC_DOMAIN') or None,
            'default_acl': None,
            'querystring_auth': False,
        },
    } if R2_BUCKET_NAME else {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    # whitenoise.storage.CompressedManifestStaticFilesStorage adds
    # content-hashed filenames + gzip/brotli compression for static assets.
    # Django 6 only reads this via STORAGES (the legacy STATICFILES_STORAGE
    # setting is no longer honored, so setting only that name silently did
    # nothing).
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

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
