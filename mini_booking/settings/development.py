from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# SQLite database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Development specific settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Override any production settings that might have been imported
DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
DATABASES['default']['NAME'] = os.path.join(BASE_DIR, 'db.sqlite3') 