"""
Django settings for servicetrack project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url
import cloudinary


def _csv_env(name, default=''):
    return [v for v in config(name, default=default, cast=Csv()) if v]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = _csv_env('ALLOWED_HOSTS', default='localhost,127.0.0.1')

# Allow Railway's auto-generated *.up.railway.app hosts
RAILWAY_PUBLIC_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='')
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'channels',
    'accounts',
    'servicedesk',
    'teams',
    'notifications',
    'analytics',
    'rest_framework',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',       # <-- serves static files in prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'servicetrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'servicetrack.wsgi.application'

ASGI_APPLICATION = 'servicetrack.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
#
# Railway (and most PaaS) provide a DATABASE_URL env var.
# We prefer that, then fall back to individual POSTGRES_* vars,
# and finally to SQLite for local dev.

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    # Railway / managed Postgres — parse the URL automatically
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
elif config('DB_ENGINE', default='') == 'postgres':
    # Explicit individual Postgres env vars (for manual setups)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB', default='servicedesk'),
            'USER': config('POSTGRES_USER', default='servicedesk'),
            'PASSWORD': config('POSTGRES_PASSWORD', default='servicedesk'),
            'HOST': config('POSTGRES_HOST', default='localhost'),
            'PORT': config('POSTGRES_PORT', default='5432'),
        }
    }
else:
    # Local development — SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: serve static files with compression + long-term caching
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

# CORS
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=DEBUG, cast=bool)
CORS_ALLOWED_ORIGINS = _csv_env('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = _csv_env('CSRF_TRUSTED_ORIGINS')

# Security — trust the proxy's forwarded headers (Railway, Render, etc.)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# Channel Layers (using in-memory for development)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Cloudinary — all user-uploaded media (attachments, profile pictures)
# WhiteNoise continues to serve Django admin/static files.
cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME', default=''),
    api_key=config('CLOUDINARY_API_KEY', default=''),
    api_secret=config('CLOUDINARY_API_SECRET', default=''),
    secure=True,
)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Silence third-party libraries
        'channels': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'asgiref': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Project loggers - set to WARNING for normal operation, INFO for debugging
        'servicedesk': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'servicedesk.sla_engine': {
            'handlers': ['console'],
            'level': 'INFO',  # Temporarily INFO to show SLA policy matching
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'teams': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'notifications': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
