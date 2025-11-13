"""
Celery application configuration.
"""

from celery import Celery
from celery.schedules import crontab
from src.utils.config import settings

# Create Celery app
celery_app = Celery(
    'nitter_scraper',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['src.scheduler.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Periodic task schedules
celery_app.conf.beat_schedule = {
    'check-tracked-users': {
        'task': 'src.scheduler.tasks.check_tracked_users',
        'schedule': 60.0,  # Check every minute
    },
    'check-tracked-searches': {
        'task': 'src.scheduler.tasks.check_tracked_searches',
        'schedule': 300.0,  # Check every 5 minutes
    },
    'cleanup-old-jobs': {
        'task': 'src.scheduler.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
