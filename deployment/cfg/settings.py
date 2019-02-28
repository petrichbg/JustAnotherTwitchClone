"""
Django settings for streaming_platform project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [ '127.0.0.1', 'localhost' ]


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
	'osp',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
	'osp.exception_logging.ExceptionLoggingMiddleware',
	'osp.middleware.UpdateLastActivityMiddleware'
)

ROOT_URLCONF = 'streaming_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
				'osp.context_processors.update_hot',
				'osp.context_processors.hotfix_hot'
            ],
        },
    },
]

WSGI_APPLICATION = 'streaming_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'osp',
		'USER': 'osp',
		'PASSWORD': '',
		'HOST': '127.0.0.1',
		'OPTIONS': {'charset': 'utf8mb4'},
		'CONN_MAX_AGE': 600
	}
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'osp_cache',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Asia/Krasnoyarsk'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/pic/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'pic/')
STATIC_ROOT = os.path.join(BASE_DIR, 'osp/static/')

LOGIN_URL = 'osp:login'

OSP_SITE_TITLE = "OSP"
OSP_RTMP_SERVER_STREAM_APP_ADDRESS = "rtmp://127.0.0.1/live/"
OSP_RTMP_SERVER_STAT_ADDRESS = "http://127.0.0.1/stat/"
OSP_RTMP_SERVER_CONTROL_ADDRESS = "http://127.0.0.1/control/"
OSP_RTMP_SERVER_STREAM_PREVIEW_ADDRESS = "http://127.0.0.1/streampreview/"
OSP_STREAM_LIST_PATH = "/var/www/stream/streams.json"

# without file extension
OSP_PLAY_LOG_NAME = "stream_play"
OSP_PUBLISH_LOG_NAME = "stream_publish"

# use 'None' if you don't need logging
OSP_PLAY_LOG_DIRECTORY = "/var/log/stream/stream_play/"
OSP_PUBLISH_LOG_DIRECTORY = "/var/log/stream/stream_publish/"
OSP_EXCEPTION_LOG = "/var/log/stream/stream_exceptions.log"

OSP_USE_LEGACY_PLAYER = False

OSP_DAYS_UNTIL_USER_CONSIDERED_INACTIVE = 21

OSP_IP_ALLOWED_TO_QUICK_HIDE_STREAMS = [ ]