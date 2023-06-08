from .settings import *

DEBUG = True

INSTALLED_APPS.extend([
    'corsheaders'
])

LOGGING['handlers']['console']['level'] = 'DEBUG'

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
ALLOWED_HOSTS = ['localhost']
CSRF_TRUSTED_ORIGINS = ['http://localhost:4200']

# cors midleware has to be loaded first
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware'
] + MIDDLEWARE

# allow access to Rest API with session in development only
# (in production only auth. via tokens is allowed)
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].extend([
    'rest_framework.authentication.SessionAuthentication',
])

DATABASES['default']['OPTIONS']['sslmode'] = 'prefer'

# default secret keys, for dev only!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-mzejv_pa9tbj7$5$q%ju0ko*)vrouq3_+0&q)y@phi!fevpntp'
)