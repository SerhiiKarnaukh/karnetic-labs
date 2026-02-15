from pathlib import Path
from datetime import timedelta
import os
import sys
# from decouple import config
from django.contrib.messages import constants as messages
from .version import __version__

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

VERSION = __version__

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", default=False) == "True"

ALLOWED_HOSTS = []
ALLOWED_HOSTS.extend(
    filter(
        None,
        os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(" "),
    ))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'django_ckeditor_5',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'djoser',
    'accounts',
    'core',
    'taberna_profiles',
    'taberna_cart',
    'taberna_product',
    'taberna_orders',
    'social_posts',
    'social_profiles',
    'social_chat',
    'social_notification',
    'donation',
    'paypal.standard.ipn',
    'ai_lab',
    'f1_pitwall',
]

MIGRATION_MODULES = {
    'ipn': None
}

CORS_ALLOWED_ORIGINS = []
CORS_ALLOWED_ORIGINS.extend(
    filter(
        None,
        os.environ.get('CORS_ALLOWED_ORIGINS', '').split(" "),
    ))

CORS_ORIGIN_WHITELIST = [
    'https://karnaukh-webdev.com'
    # Add any other trusted domains here
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]


CSRF_TRUSTED_ORIGINS = [
    'https://karnaukh-webdev.com'
]


CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = '.karnaukh-webdev.com'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'portfolio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'portfolio/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.menu_categories',
                'core.context_processors.core_tags',
                'taberna_product.context_processors.menu_categories',
                'taberna_product.context_processors.top_categories',
                'taberna_cart.context_processors.counter',
            ],
        },
    },
]

WSGI_APPLICATION = 'portfolio.wsgi.application'

ASGI_APPLICATION = 'portfolio.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER",
                                   "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND",
                                       "redis://redis:6379/0")

AUTH_USER_MODEL = 'accounts.Account'

DATABASES = {
    "default": {
        "ENGINE":
        os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME":
        os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER":
        os.environ.get("SQL_USER", "user"),
        "PASSWORD":
        os.environ.get("SQL_PASSWORD", "password"),
        "HOST":
        os.environ.get("SQL_HOST", "localhost"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/static/'
MEDIA_URL = '/static/media/'

MEDIA_ROOT = '/vol/web/media'
STATIC_ROOT = '/vol/web/static'
STATICFILES_DIRS = []

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    "127.0.0.1",
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# SMTP configurations
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_HOST_USER")

CKEDITOR_UPLOAD_PATH = "uploads/"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}
DJOSER = {
    'ACTIVATION_URL': 'accounts/activate/{uid}/{token}/',
    'SEND_ACTIVATION_EMAIL': True,
    'USER_ACTIVATION': {
        'SEND_EMAIL': True,
        'ACTIVATION_AFTER_REGISTRATION': True,
        'SEND_CONFIRMATION_EMAIL': True,
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
    timedelta(minutes=6),
    "REFRESH_TOKEN_LIFETIME":
    timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":
    False,
    "BLACKLIST_AFTER_ROTATION":
    False,
    "UPDATE_LAST_LOGIN":
    False,
    "ALGORITHM":
    "HS256",
    "SIGNING_KEY":
    SECRET_KEY,
    "VERIFYING_KEY":
    "",
    "AUDIENCE":
    None,
    "ISSUER":
    None,
    "JSON_ENCODER":
    None,
    "JWK_URL":
    None,
    "LEEWAY":
    0,
    "AUTH_HEADER_TYPES": ("Bearer", ),
    "AUTH_HEADER_NAME":
    "HTTP_AUTHORIZATION",
    "USER_ID_FIELD":
    "id",
    "USER_ID_CLAIM":
    "user_id",
    "USER_AUTHENTICATION_RULE":
    "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken", ),
    "TOKEN_TYPE_CLAIM":
    "token_type",
    "TOKEN_USER_CLASS":
    "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM":
    "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM":
    "refresh_exp",
    "SLIDING_TOKEN_LIFETIME":
    timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME":
    timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER":
    "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

customColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ],

    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
        ],
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
                    'bulletedList', 'numberedList', 'todoList', '|',  'blockQuote', 'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable',],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side',  '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]

        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            }
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        }
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}

TABERNA_TAX_RATE = 0.02

# PayPal Settings
PAYPAL_RECEIVER_EMAIL = os.environ.get("PAYPAL_RECEIVER_EMAIL")
PAYPAL_TEST = os.environ.get("PAYPAL_TEST")

# Stripe Settings
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_PRIVATE_KEY = os.environ.get("STRIPE_PRIVATE_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
