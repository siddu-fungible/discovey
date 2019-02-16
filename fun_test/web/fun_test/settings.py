"""
Django settings for web project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from fun_settings import *
from fun_global import is_lite_mode, is_development_mode

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y9@*b%24y_iv_0wmr8l%&_3@@4hpfp2@_#n$q-qu$549f_r0ww'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'web.fun_test',
    'web.tools',
]

# if is_development_mode():
#    INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# if is_development_mode():
#    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')


ROOT_URLCONF = 'fun_test.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['../tools/templates'],
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

WSGI_APPLICATION = 'fun_test.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

REGRESSION_DB_FILE = "regression.db.sqlite3"
USERS_DB_FILE = "users.db.sqlite3"

DEFAULT_DB_FILE = REGRESSION_DB_FILE


# print "DEFAULT DB: {}".format(DEFAULT_DB_FILE)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, DEFAULT_DB_FILE),
    },
    'users': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, USERS_DB_FILE)
    },
    'OPTIONS': {
        'timeout': 20,
    }
}

# Sample for postgresql
if not is_lite_mode():
    DATABASES["default"] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fun_test',
        'USER': 'fun_test_user',
        'PASSWORD': 'fun123',
        'HOST': 'localhost',
        'PORT': ''}

DATABASE_ROUTERS = ('web.fun_test.db_routers.UsersRouter',)

'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fun_test',
        'USER': 'django',
        'PASSWORD': 'fun123',
        'HOST': 'localhost',
        'PORT': '',
    }
}
'''

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = ''

STATIC_URL = '/static/'

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),
                    os.path.join(BASE_DIR, 'tools/angular_templates'),
                    os.path.join(BASE_DIR, 'tools/angular_controllers'),
                    os.path.join(BASE_DIR, 'static/js/qa_dashboard'),
                    os.path.join(BASE_DIR, 'static/css/qa_dashboard'),
                    os.path.join(BASE_DIR, 'fun_test/templates'),
                    TEST_ARTIFACTS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'web': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

CSRF_COOKIE_SECURE = False


# SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')