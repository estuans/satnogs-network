from decouple import config, Csv
from dj_database_url import parse as db_url
from unipath import Path

ROOT = Path(__file__).parent.parent

ENVIRONMENT = config('ENVIRONMENT', default='dev')
DEBUG = config('DEBUG', default=False, cast=bool)

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
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@satnogs.org')
ADMINS = [
    ('SatNOGS Admins', DEFAULT_FROM_EMAIL)
]
MANAGERS = ADMINS
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Cache
CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='redis_cache.RedisCache'),
        'LOCATION': config('CACHE_LOCATION', default='unix://var/run/redis/redis.sock'),
        'OPTIONS': {
            'CLIENT_CLASS': config('CACHE_CLIENT_CLASS',
                                   default='django_redis.client.DefaultClient'),
        },
        'KEY_PREFIX': 'network-{0}'.format(ENVIRONMENT),
    }
}
CACHE_TTL = config('CACHE_TTL', default=300, cast=int)

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
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'network.base.context_processors.analytics',
                'network.base.context_processors.stage_notice',
                'network.base.context_processors.user_processor',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
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
MEDIA_ROOT = Path('media').resolve()
MEDIA_URL = '/media/'
CRISPY_TEMPLATE_PACK = 'bootstrap3'
STATION_DEFAULT_IMAGE = '/static/img/ground_station_no_image.png'
SATELLITE_DEFAULT_IMAGE = 'https://db.satnogs.org/static/img/sat.png'
COMPRESS_ENABLED = config('COMPRESS_ENABLED', default=False, cast=bool)
COMPRESS_OFFLINE = config('COMPRESS_OFFLINE', default=False, cast=bool)
COMPRESS_CACHE_BACKEND = config('COMPRESS_CACHE_BACKEND', default='default')
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter'
]
COMPRESS_PRECOMPILERS = (
    ('text/scss', 'sass --scss {infile} {outfile}'),
)

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
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
REDIS_CONNECT_RETRY = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': config('REDIS_VISIBILITY_TIMEOUT', default=604800, cast=int),
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
        'django_filters.rest_framework.DjangoFilterBackend',
    )
}

# Security
SECRET_KEY = config('SECRET_KEY', default='changeme')
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())
CSP_DEFAULT_SRC = (
    "'self'",
    'https://*.mapbox.com',
    'https://*.archive.org',
)
CSP_SCRIPT_SRC = (
    "'self'",
    'https://*.google-analytics.com',
    "'unsafe-eval'",
)
CSP_IMG_SRC = (
    "'self'",
    'https://*.gravatar.com',
    'https://*.mapbox.com',
    'https://*.satnogs.org',
    'https://*.google-analytics.com',
    'data:',
    'blob:',
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
)
CSP_CHILD_SRC = (
    'blob:',
)

# Database
DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')
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
MAPBOX_MAP_ID = config('MAPBOX_MAP_ID', default='')
MAPBOX_TOKEN = config('MAPBOX_TOKEN', default='')

# Metrics
OPBEAT = {
    'ORGANIZATION_ID': config('OPBEAT_ORGID', default=''),
    'APP_ID': config('OPBEAT_APPID', default=''),
    'SECRET_TOKEN': config('OPBEAT_SECRET', default=''),
}

# Observations settings
# Datetimes in minutes for scheduling OPTIONS
OBSERVATION_DATE_MIN_START = config('OBSERVATION_DATE_MIN_START', default=15, cast=int)
OBSERVATION_DATE_MIN_END = config('OBSERVATION_DATE_MIN_START', default=75, cast=int)
# Deletion range in minutes
OBSERVATION_DATE_MAX_RANGE = config('OBSERVATION_DATE_MAX_RANGE', default=480, cast=int)
# Clean up threshold in days
OBSERVATION_OLD_RANGE = config('OBSERVATION_OLD_RANGE', default=30, cast=int)

# Station settings
# Heartbeat for keeping a station online in minutes
STATION_HEARTBEAT_TIME = config('STATION_HEARTBEAT_TIME', default=60, cast=int)
# Maximum window for upcoming passes in hours
STATION_UPCOMING_END = config('STATION_UPCOMING_END', default=12, cast=int)
WIKI_STATION_URL = config('WIKI_STATION_URL', default='https://wiki.satnogs.org/')

# DB API
DB_API_ENDPOINT = config('DB_API_ENDPOINT', default='https://db.satnogs.org/api/')

# ListView pagination
ITEMS_PER_PAGE = 25

# User settings
AVATAR_GRAVATAR_DEFAULT = config('AVATAR_GRAVATAR_DEFAULT', default='mm')

# Archive.org
S3_ACCESS_KEY = config('S3_ACCESS_KEY', default='')
S3_SECRET_KEY = config('S3_SECRET_KEY', default='')
ARCHIVE_COLLECTION = config('ARCHIVE_COLLECTION', default='test_collection')
ARCHIVE_URL = 'https://archive.org/download/'

if ENVIRONMENT == 'dev':
    # Disable template caching
    for backend in TEMPLATES:
        del backend['OPTIONS']['loaders']
        backend['APP_DIRS'] = True
