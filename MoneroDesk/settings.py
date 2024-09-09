import os
from pathlib import Path
from decouple import config, Csv
from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet
import sys


# Définir BASE_DIR pour l'ensemble du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement des configurations sensibles depuis le fichier .env
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost, 127.0.0.1', cast=Csv())

# Configuration de la base de données
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

if DEBUG :
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Configuration Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Utilise Redis comme broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Utilise Redis comme backend de résultats
CELERY_ACCEPT_CONTENT = ['json']  # Format de contenu accepté
CELERY_TASK_SERIALIZER = 'json'  # Sérialisation des tâches au format JSON
CELERY_RESULT_SERIALIZER = 'json'  # Sérialisation des résultats au format JSON
CELERY_TIMEZONE = 'UTC'  # Fuseau horaire

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
    'monero_app',
    'redis',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
MEDIA_ROOT = BASE_DIR / 'media'

# Réglages pour les fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

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

# Configuration des reseaux Xmr
if DEBUG:
    XMR_RPC_PORT = 28088
    XMR_RPC_HOST = '127.0.0.1'
else:
    XMR_RPC_PORT = 18081 

w = Wallet(JSONRPCWallet(port=28088))
w.address = config('XMR_WALLET')
try:
    wallet = Wallet(JSONRPCWallet(host=XMR_RPC_HOST, port=XMR_RPC_PORT))
    # Vous pouvez ajouter des appels qui ne provoquent pas d'erreurs ici, comme obtenir le solde
    balance = wallet.balance()  # Exemple d'appel sécurisé
except Exception as e:
    # Gérer les exceptions si nécessaire
    print(f"Erreur lors de l'initialisation du portefeuille Monero : {e}")

# Configuration pour les tests
if 'test' in sys.argv:
    ALLOWED_HOSTS = ['testserver']
