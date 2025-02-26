import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mini_booking.settings.development')

app = Celery('mini_booking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() 