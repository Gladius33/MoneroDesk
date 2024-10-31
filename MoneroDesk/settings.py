import os
from pathlib import Path
from decouple import config, Csv
import sys


# Définir BASE_DIR pour l'ensemble du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement des configurations sensibles depuis le fichier .env
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '54.36.175.127', 'monerodesk.org', 'www.monerodesk.org', 'hest.monerodesk.org', 'www.hest.monerodesk.org']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if not DEBUG:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Security
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
SESSION_COOKIE_SECURE = True  # Garantit que les cookies sont transmis uniquement via HTTPS
SESSION_COOKIE_HTTPONLY = True  # Empêche l'accès aux cookies par JavaScript (contre XSS)
SESSION_COOKIE_SAMESITE = 'Strict'  # Empêche l’envoi de cookies lors des requêtes intersites (protection contre le CSRF)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_PERMISSIONS_POLICY = {
    "geolocation": ["'none'"],  # Interdit la géolocalisation
    "camera": ["'none'"],  # Désactive l'accès à la caméra
    "microphone": ["'none'"],  # Désactive le microphone
    "payment": ["'none'"],  # Désactive les API de paiement
    "fullscreen": ["'self'"],  # Autorise le plein écran uniquement sur le domaine
    "accelerometer": ["'none'"],  # Désactive les capteurs d'accélération
    "ambient-light-sensor": ["'none'"],  # Désactive le capteur de lumière ambiante
    "autoplay": ["'none'"],  # Empêche la lecture automatique des vidéos
    "encrypted-media": ["'none'"],  # Désactive le déchiffrement des médias protégés
    "gyroscope": ["'none'"],  # Désactive le gyroscope
    "magnetometer": ["'none'"],  # Désactive le magnétomètre
    "usb": ["'none'"],  # Interdit l'accès aux périphériques USB
    "xr-spatial-tracking": ["'none'"]  # Désactive le suivi spatial XR
}



# Configuration Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Utilise Redis comme broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Utilise Redis comme backend de résultats
CELERY_ACCEPT_CONTENT = ['json']  # Format de contenu accepté
CELERY_TASK_SERIALIZER = 'json'  # Sérialisation des tâches au format JSON
CELERY_RESULT_SERIALIZER = 'json'  # Sérialisation des résultats au format JSON
CELERY_TIMEZONE = 'UTC'  # Fuseau horaire
CELERY_BEAT_SCHEDULE = {
    'fetch-monero-rates-every-minute': {
        'task': 'monero_app.tasks.fetch_monero_rates',  # The task to fetch Monero rates
        'schedule': 60.0,  # Schedule the task to run every 60 seconds (1 minute)
    },
}


# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'ads',
    'transactions',
    'chat',
    'dashboard',
    'channels',
    'support',
    'monero_app.apps.MoneroAppConfig',
    'redis',
    'django_celery_beat',
]
# Middleware utilisé par Django
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MoneroDesk.urls'

# Configuration des templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'MoneroDesk', 'templates')],
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

# WSGI et ASGI configuration
WSGI_APPLICATION = 'MoneroDesk.wsgi.application'
ASGI_APPLICATION = 'MoneroDesk.asgi.application'  # Configuration pour ASGI

# Configuration de Django Channels avec Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],  # Adresse du serveur Redis
        },
    },
}


# Configuration de validation des mots de passe
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

# Réglages pour les fichiers médias
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/appuser/web/monerodesk.org/media/'

# Réglages pour les fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = '/home/appuser/web/monerodesk.org/static/'

# Redirections après login/logout
LOGIN_REDIRECT_URL = 'user_dashboard'
LOGOUT_REDIRECT_URL = '/'

# Réglages internationaux
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Utilisation du champ auto par défaut pour les modèles
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Monero RPC Configuration
XMR_RPC_HOST = '127.0.0.1'
XMR_RPC_PORT = 28088 if DEBUG else 18081

# Configuration pour les tests
if 'test' in sys.argv:
    ALLOWED_HOSTS = ['testserver']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


