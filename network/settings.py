from os import getenv
from dj_database_url import parse as db_url
from unipath import Path

ROOT = Path(__file__).parent.parent

ENVIRONMENT = getenv('ENVIRONMENT', 'production')
DEBUG = getenv('DEBUG', False)

# Apps
DJANGO_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
)
THIRD_PARTY_APPS = (
    'avatar',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'compressor',
    'csp',
)
LOCAL_APPS = (
    'network.users',
    'network.base',
    'network.api',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
if ENVIRONMENT == 'production':
    INSTALLED_APPS += (
        'opbeat.contrib.django',
    )

# Middlware
MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
)
if ENVIRONMENT == 'production':
    MIDDLEWARE += (
        'opbeat.contrib.django.middleware.OpbeatAPMMiddleware',
        'opbeat.contrib.django.middleware.Opbeat404CatchMiddleware',
    )

# Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_TIMEOUT = 300
DEFAULT_FROM_EMAIL = getenv('DEFAULT_FROM_EMAIL', 'noreply@satnogs.org')
ADMINS = (
    (
        getenv('ADMINS_FROM_NAME', 'SatNOGS Admins'),
        getenv('ADMINS_FROM_EMAIL', DEFAULT_FROM_EMAIL)
    ),
)
MANAGERS = ADMINS
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Cache
CACHES = {
    'default': {
        'BACKEND': getenv('CACHE_BACKEND', 'redis_cache.RedisCache'),
        'LOCATION': getenv('CACHE_LOCATION', 'unix://var/run/redis/redis.sock'),
        'OPTIONS': {
            'CLIENT_CLASS': getenv('CACHE_CLIENT_CLASS', 'django_redis.client.DefaultClient'),
        },
        'KEY_PREFIX': 'network-{0}'.format(ENVIRONMENT),
    }
}
CACHE_TTL = int(getenv('CACHE_TTL', 300))

# Internationalization
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
USE_L10N = False
USE_TZ = True

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            Path('network/templates').resolve(),
        ],
        'OPTIONS': {
            'debug': False,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'network.base.context_processors.analytics',
                'network.base.context_processors.stage_notice',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },

    },
]

# Static & Media
STATIC_ROOT = Path('staticfiles').resolve()
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    Path('network/static').resolve(),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
MEDIA_ROOT = getenv('MEDIA_ROOT', Path('media').resolve())
MEDIA_URL = '/media/'
CRISPY_TEMPLATE_PACK = 'bootstrap3'
STATION_DEFAULT_IMAGE = '/static/img/dish.png'
SATELLITE_DEFAULT_IMAGE = 'https://db.satnogs.org/static/img/sat.png'

# App conf
ROOT_URLCONF = 'network.urls'
WSGI_APPLICATION = 'network.wsgi.application'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'users:redirect_user'
LOGIN_URL = 'account_login'
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'
if ENVIRONMENT == 'production':
    # Disable registration
    ACCOUNT_ADAPTER = 'network.users.adapter.NoSignupsAdapter'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s - %(process)d %(thread)d - %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'opbeat': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'opbeat.contrib.django.handlers.OpbeatHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['opbeat'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.network.backends': {
            'level': 'ERROR',
            'handlers': ['opbeat'],
            'propagate': False,
        },
        'network': {
            'level': 'WARNING',
            'handlers': ['opbeat'],
            'propagate': False,
        },
        'opbeat.errors': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

# Celery
CELERY_ENABLE_UTC = USE_TZ
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_RESULTS_EXPIRES = 3600
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_DEFAULT_QUEUE = 'network-{0}-queue'.format(ENVIRONMENT)
CELERY_BROKER_URL = getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
REDIS_CONNECT_RETRY = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': getenv('REDIS_VISIBILITY_TIMEOUT', default=604800),
    'fanout_prefix': True
}

# API
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
    )
}

# Security
SECRET_KEY = getenv('SECRET_KEY', 'changeme')
SECURE_HSTS_SECONDS = getenv('SECURE_HSTS_SECONDS', 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
ALLOWED_HOSTS = [
    getenv('ALLOWED_HOSTS', '*')
]
CSP_DEFAULT_SRC = (
    "'self'",
    'https://*.mapbox.com',
)
CSP_SCRIPT_SRC = (
    "'self'",
    'https://*.google-analytics.com',
)
CSP_IMG_SRC = (
    "'self'",
    'https://*.gravatar.com',
    'https://*.mapbox.com',
    'https://*.satnogs.org',
    'https://*.google-analytics.com',
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
)

# Database
DATABASE_URL = getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {'default': db_url(DATABASE_URL)}
DATABASES_EXTRAS = {
    'OPTIONS': {
        'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"'
    },
}
if DATABASES['default']['ENGINE'].split('.')[-1] == 'mysql':
    DATABASES['default'].update(DATABASES_EXTRAS)

# Mapbox API
MAPBOX_GEOCODE_URL = 'https://api.tiles.mapbox.com/v4/geocode/mapbox.places/'
MAPBOX_MAP_ID = getenv('MAPBOX_MAP_ID', '')
MAPBOX_TOKEN = getenv('MAPBOX_TOKEN', '')

# Metrics
OPBEAT = {
    'ORGANIZATION_ID': getenv('OPBEAT_ORGID', None),
    'APP_ID': getenv('OPBEAT_APPID', None),
    'SECRET_TOKEN': getenv('OPBEAT_SECRET', None),
}

# Observations settings
# Datetimes in minutes for scheduling OPTIONS
# Deletion range in minutes
# Clean up threshold in days
DATE_MIN_START = '15'
DATE_MIN_END = '75'
DATE_MAX_RANGE = '480'
OBSERVATION_MAX_DELETION_RANGE = getenv('OBSERVATION_MAX_DELETION_RANGE', 10)
OBSERVATION_MIN_DELETION_RANGE = getenv('OBSERVATION_MIN_DELETION_RANGE', 60)
OBSERVATION_OLD_RANGE = getenv('OBSERVATION_OLD_RANGE', 30)

# Station settings
# Heartbeat for keeping a station online in minutes
# Maximum window for upcoming passes in hours
STATION_HEARTBEAT_TIME = getenv('STATION_HEARTBEAT_TIME', 60)
STATION_UPCOMING_END = getenv('STATION_UPCOMING_END', 12)

# DB API
DB_API_ENDPOINT = getenv('DB_API_ENDPOINT', 'https://db.satnogs.org/api/')

# ListView pagination
ITEMS_PER_PAGE = 25

# User settings
AVATAR_GRAVATAR_DEFAULT = getenv('AVATAR_GRAVATAR_DEFAULT', 'mm')
