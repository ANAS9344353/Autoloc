"""
Configuration Django du projet AutoLoc.

Les valeurs sensibles (SECRET_KEY, mot de passe MySQL, etc.) sont
lues depuis le fichier .env grace a python-dotenv.

Pour configurer :
1. Copier .env.example en .env
2. Modifier .env selon ton environnement
3. Lancer normalement : python manage.py runserver
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger le fichier .env (a la racine du backend)
load_dotenv(BASE_DIR / '.env')


def env_bool(key, default='False'):
    """Convertit une variable env en booleen."""
    return os.getenv(key, default).lower() in ('true', '1', 'yes', 'oui')


# ============================================================
# DJANGO
# ============================================================
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-changez-moi-en-production-autoloc-jwt-2025',
)
DEBUG = env_bool('DJANGO_DEBUG', 'True')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Tiers
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # Mes apps
    'accounts',
    'scraper',
    'voitures',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'

# ============================================================
# BASE DE DONNEES : MySQL (lue depuis le .env)
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     os.getenv('DB_NAME',     'autoloc_db'),
        'USER':     os.getenv('DB_USER',     'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST':     os.getenv('DB_HOST',     '127.0.0.1'),
        'PORT':     os.getenv('DB_PORT',     '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# Fichiers media (photos uploadees par les proprietaires)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', 'True')
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# DJANGO REST FRAMEWORK : authentification par JWT
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Pagination : DESACTIVEE PAR DEFAUT pour ne pas casser le frontend
    # qui attend une liste pure. La pagination est appliquee MANUELLEMENT
    # dans certaines views si necessaire (cf. voitures/views.py).
    # Pour activer la pagination globale, decommenter les lignes ci-dessous :
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 20,
}

# ============================================================
# JWT : duree de vie des tokens (lue depuis le .env)
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(days=int(os.getenv('JWT_ACCESS_LIFETIME_DAYS',  '7'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_LIFETIME_DAYS', '30'))),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ============================================================
# LOGGING (logs structures pour le scraper et le reste)
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'scraper': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
