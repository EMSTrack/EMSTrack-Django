"""
Django settings for emstrack project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import sys

from django.contrib.messages import constants as messages
from socket import gethostname, gethostbyname

from environs import Env
env = Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sessions
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('DJANGO_SECRET_KEY', default='CHANG3M3')

# swagger settings
#SWAGGER_SETTINGS = {
#    'APIS_SORTER': 'alpha',
#    'DOC_EXPANSION': 'list',
#    'LOGIN_URL': 'rest_framework:login',
#    'LOGOUT_URL': 'rest_framework:logout'
#}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJANGO_DEBUG', default=False)
allowed_hosts = env.str('DJANGO_HOSTNAMES', default="*")
if allowed_hosts == "*":
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = env.list('DJANGO_HOSTNAMES') + [gethostbyname(gethostname())]

USE_X_FORWARDED_HOST = True

# Application definition

INSTALLED_APPS = [
    'ambulance.apps.AmbulanceConfig',
    'hospital.apps.HospitalConfig',
    'login.apps.LoginConfig',
    'equipment.apps.EquipmentConfig',
    'report.apps.ReportConfig',
    'mqtt',
    'emstrack',
    'rest_framework',
    'drf_yasg',
    'rest_framework.authtoken',
    'import_export',
    'django_nose',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'jquery',
    'djangoformsetjs',
    'webpack_loader',
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'emstrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mqtt.context_processors.jstags',
            ],
        },
    },
]

WSGI_APPLICATION = 'emstrack.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env.str('DB_DATABASE'),
        'USER': env.str('DB_USERNAME'),
        'PASSWORD': env.str('DB_PASSWORD'),
        'HOST': env.str('DB_HOST'),
        'PORT': 5432,
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
        os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# STATIC_ROOT = './static/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy', 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# login redirect
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login:login'

# email settings
EMAIL_BACKEND = env.str('EMAIL_BACKEND')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL')
EMAIL_HOST = env.str('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')

# MQTT settings
MQTT = {
    'USERNAME': env.str('MQTT_USERNAME'),
    'PASSWORD': env.str('MQTT_PASSWORD'),
    'EMAIL': env.str('MQTT_EMAIL'),
    'CLIENT_ID': env.str('MQTT_CLIENTID'),
    'BROKER_HOST': env.str('MQTT_BROKER_HOST'),
    'BROKER_PORT': env.str('MQTT_BROKER_PORT'),
    'BROKER_SSL_HOST': env.str('MQTT_BROKER_SSL_HOST'),
    'BROKER_SSL_PORT': env.str('MQTT_BROKER_SSL_PORT'),
    'BROKER_WEBSOCKETS_HOST': env.str('MQTT_BROKER_WEBSOCKETS_HOST'),
    'BROKER_WEBSOCKETS_PORT': env.str('MQTT_BROKER_WEBSOCKETS_PORT'),
    'BROKER_TEST_HOST': env.str('MQTT_BROKER_TEST_HOST'),
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'
}

# Custom message tags
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Access Token
MAP_PROVIDER = env.str('MAP_PROVIDER')
MAP_PROVIDER_TOKEN = env.str('MAP_PROVIDER_TOKEN')

# Webpack Loader
WEBPACK_LOADER = {
    'BASE': {
        'BUNDLE_DIR_NAME': 'bundles/base/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/base-stats.json'),
    },
    'MAP': {
        'BUNDLE_DIR_NAME': 'bundles/map/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/map-stats.json'),
    },
    'AMBULANCE': {
        'BUNDLE_DIR_NAME': 'bundles/ambulance/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/ambulance-stats.json'),
    },
    'POINT_WIDGET': {
        'BUNDLE_DIR_NAME': 'bundles/point-widget/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/point-widget-stats.json'),
    },
    'CALL': {
        'BUNDLE_DIR_NAME': 'bundles/call/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/call-stats.json'),
    },
    'REPORT_VEHICLE_MILEAGE': {
        'BUNDLE_DIR_NAME': 'bundles/report-vehicle-mileage/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/report-vehicle-mileage-stats.json'),
    },
    'REPORT_VEHICLE_STATUS': {
        'BUNDLE_DIR_NAME': 'bundles/report-vehicle-activity/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack/report-vehicle-activity-stats.json'),
    },
}

# Import-export settings
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/etc/emstrack/log/django.log',
        },
        'emstrack': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/etc/emstrack/log/emstrack.log',
        },
        'mqtt': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/etc/emstrack/log/mqtt.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['debug'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'ambulance': {
            'handlers': ['emstrack'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'emstrack': {
            'handlers': ['emstrack'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'login': {
            'handlers': ['emstrack'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'mqtt': {
            'handlers': ['mqtt'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
    },
}

# Testing
# https://stackoverflow.com/questions/6957016/detect-django-testing-mode
TESTING = sys.argv[1:2] == ['test']
