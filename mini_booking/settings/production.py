from .base import *
from dotenv import load_dotenv
import os

load_dotenv()

DEBUG = True  # Geçici olarak True yapıyoruz
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# PostgreSQL database for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Production security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True 