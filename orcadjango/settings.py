import os
import sys
from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORCA_MODULES = {
    'default': {
        'path': 'orcaserver.tests.dummy_orca_stuff',
        'template': 'orcaserver/project.html',
    },
    'available': {
        'test module': {
            'path': 'orcaserver.tests.dummy_orca_stuff',
            'description': 'module used for testing',
            'init': ['inj_list', 'inj_dict'],
        }
    }
}

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

ALLOWED_HOSTS = ['localhost']

# GDAL configuration
if os.name == 'nt':
    lib_path = os.path.join(sys.exec_prefix, 'Library')
    if (os.path.exists(os.path.join(lib_path, 'share', 'gdal'))
            and os.path.exists(os.path.join(lib_path, 'share', 'proj')) ):
        os.environ['GDAL_DATA'] = os.path.join(lib_path, 'share', 'gdal')
        os.environ['PROJ_LIB'] = os.path.join(lib_path, 'share', 'proj')
    else:
        # preset for GDAL installation via OSGeo4W as recommended by Django, see
        # https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#windows
        osgeo4w_directories = [r'C:\OSGeo4W64', r'C:\OSGeo4W']
        for OSGEO4W_ROOT in osgeo4w_directories:
            if os.path.exists(OSGEO4W_ROOT):
                break
        else:
            raise IOError(f'OSGeo4W not installed in {osgeo4w_directories}')
        os.environ['GDAL_DATA'] = os.path.join(OSGEO4W_ROOT, 'share', 'gdal')
        os.environ['PROJ_LIB'] = os.path.join(OSGEO4W_ROOT, 'share', 'proj')
        os.environ['PATH'] = ';'.join([os.environ['PATH'],
                                       os.path.join(OSGEO4W_ROOT, 'bin')])

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'orcaserver',
    'rest_framework',
    'rest_framework_simplejwt',
    'channels'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True
}

ROOT_URLCONF = 'orcadjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'orcadjango', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'orcadjango.wsgi.application'
ASGI_APPLICATION = 'orcadjango.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [f'redis://{REDIS_HOST}:{REDIS_PORT}'],
        },
    },
}

use_websockets = True

DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
HOST = os.environ.get('DJANGO_HOST')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {'sslmode': 'prefer'},
    },
}

LOGIN_REDIRECT_URL = '/'

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

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, 'orcadjango', 'static')
STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
        },
        'orca_channel': {
            'level': 'DEBUG',
            'class': 'orcadjango.loggers.WebSocketHandler',
        },
    },
    'loggers': {
        'OrcaLog': {
            'handlers': ['orca_channel'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}