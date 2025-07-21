"""Celery application configuration for async task processing."""

import os
from celery import Celery
from celery.schedules import crontab
from src.config.config import Config

# Initialize Celery
celery_app = Celery('ioagent')

# Configure Celery
celery_app.config_from_object({
    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 minutes
    'task_soft_time_limit': 25 * 60,  # 25 minutes
    'worker_prefetch_multiplier': 4,
    'worker_max_tasks_per_child': 1000,
    
    # Task routing
    'task_routes': {
        'src.tasks.document_tasks.*': {'queue': 'documents'},
        'src.tasks.ai_tasks.*': {'queue': 'ai'},
        'src.tasks.file_tasks.*': {'queue': 'files'},
        'src.tasks.notification_tasks.*': {'queue': 'notifications'},
    },
    
    # Periodic tasks
    'beat_schedule': {
        'cleanup-old-files': {
            'task': 'src.tasks.maintenance_tasks.cleanup_old_files',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'generate-usage-reports': {
            'task': 'src.tasks.maintenance_tasks.generate_usage_reports',
            'schedule': crontab(hour=1, minute=0, day_of_week=1),  # Weekly on Monday
        },
        'backup-database': {
            'task': 'src.tasks.maintenance_tasks.backup_database',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        },
    },
    
    # Task result expiration
    'result_expires': 3600,  # 1 hour
    
    # Task annotations
    'task_annotations': {
        '*': {'rate_limit': '10/s'},
        'src.tasks.ai_tasks.*': {'rate_limit': '1/s'},  # AI tasks rate limited
    },
})

# Auto-discover tasks
celery_app.autodiscover_tasks(['src.tasks'])

# Celery signals for monitoring
from celery.signals import task_prerun, task_postrun, task_failure
import logging

logger = logging.getLogger(__name__)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task start."""
    logger.info(f"Task {task.name}[{task_id}] starting with args={args} kwargs={kwargs}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kw):
    """Log task completion."""
    logger.info(f"Task {task.name}[{task_id}] completed with state={state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, 
                        kwargs=None, traceback=None, einfo=None, **kw):
    """Log task failures."""
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}", exc_info=True)