#pour initailiser celery lorsque le projet demarre
# Import Celery application
from .celery import app as celery_app

_all_ = ('celery_app',)