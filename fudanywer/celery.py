from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fudanywer.settings')

app = Celery('fudanywer')
app.conf.enable_utc = False

app.conf.update(timezone = 'Asia/Kolkata')

app.config_from_object(settings, namespace='CELERY')

#Celery Beat Settings

app.conf.beat_schedule = {
    'create-vendor-bill-at-month-start': {
        'task': 'vendor.tasks.vendor_bill',
        # 'schedule': crontab(0,0, day_of_month='1'),
        'schedule': crontab(hour=2, minute=13),
    }
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

