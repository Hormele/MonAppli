#pour executer automatiquement les campagnes reccurentews 
# Initialisation de celery
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  # remplace monprojet par le nom de ton projet

app = Celery('myproject')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')