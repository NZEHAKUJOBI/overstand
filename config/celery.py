"""
Celery application for IPAWAS.

Loaded by the Procfile worker dyno:
    celery -A config worker --loglevel=info --concurrency=2
"""

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

# Point Celery at the correct Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

app = Celery("ipawas")

# Read Celery config from Django settings using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug("Request: %r", self.request)
