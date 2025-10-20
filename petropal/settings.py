import os 
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')


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

    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'storages',

    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    

    'accounts',
    'shared',
    'profiles',
    'chat',
] 

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'accounts.middleware.SecurityMiddleware',
]

ROOT_URLCONF = 'petropal.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'petropal.wsgi.application'

ASGI_APPLICATION = 'petropal.asgi.application'

# ======================
# Redis + Channels Config
# ======================
# REDIS_HOST = os.getenv("REDIS_HOST", "redis")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
REDIS_URL = os.getenv("REDIS_URL")

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# # ======================
# # Cache using Redis
# # ======================
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            # 'ssl': {'ssl-ca': '/path/to/ca-cert.pem'}  # If online DB requires SSL
        }
    }
}

# DATABASES = {
#     'default': dj_database_url.config(
#         default=os.getenv("DATABASE_URL"),  # Render's DB URL
#         conn_max_age=600,  # keeps connection alive
#         ssl_require=True   # Render Postgres requires SSL
#     )
# }

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ontapke.com')



AUTHENTICATION_BACKENDS = [
    'accounts.authentication.EmailPhoneAuthBackend',  
    'django.contrib.auth.backends.ModelBackend',
]


AUTH_USER_MODEL = 'accounts.Account'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# # MEDIA_URL = '/media/'
# MEDIA_URL = 'https://www.ontapke.com/media/petropal_media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT_FILE_STORAGE = 'chat.storage_backends.CPanelSFTPStorage'

STORAGES = {
    "default": {
        "BACKEND": "chat.storage_backends.CPanelSFTPStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


SFTP_STORAGE_HOST = os.getenv('SFTP_HOST')
SFTP_STORAGE_ROOT = os.getenv('REMOTE_MEDIA_ROOT')
SFTP_STORAGE_PARAMS = {
    'username': os.getenv('SFTP_USER'),
    'password': os.getenv('SFTP_PASS'),
    'port': int(os.getenv('SFTP_PORT', 22)),
}
SFTP_STORAGE_INTERACTIVE = False
SFTP_STORAGE_FILE_MODE = 0o644
SFTP_STORAGE_DIR_MODE = 0o755

MEDIA_URL = 'https://ontapke.com/media/petropal_media/'
MEDIA_ROOT = '/home/ontapke/petropal-main/media/petropal_media/'


# File upload settings --- message attachments
MAX_FILE_SIZE = 50 * 1024 * 1024      # 50MB default max file size
MAX_IMAGE_SIZE = 10 * 1024 * 1024     # 10MB 
MAX_VIDEO_SIZE = 60 * 1024 * 1024     # 60MB 
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB 

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.csv']

COMPRESS_IMAGES = True
COMPRESS_VIDEOS = True
IMAGE_QUALITY = 85  # JPEG quality (1-100)
VIDEO_CRF = 28  # Video compression factor (18-28 recommended, lower = better quality)



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.TokenAuthentication',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
# }


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],

    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,



    # rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',  # 10 requests per minute for anonymous users
        'user': '160/min'   # 60 requests per minute for authenticated users
    }
}





# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': (SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'acc_id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}





# Security settings
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  
    "http://localhost:8000",  
    "http://127.0.0.1:8000",  
    "http://localhost:8080",  
    "https://petropal-v2-0.onrender.com",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  


# CORS settings for API requests
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# For development, disable CSRF for API endpoints
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    'https://petropal-v2-0.onrender.com',
]


# for development
if DEBUG:
    # Allow all origins during development
    CORS_ALLOW_ALL_ORIGINS = True
    
    # Less strict CSRF settings for development
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Rate limiting
RATE_LIMIT_ENABLED = True


#app settings
APP_NAME = 'Petropal'




# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts': {  
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

