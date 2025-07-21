"""Celery configuration file."""

import os
from datetime import timedelta

# Broker settings
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes
task_acks_late = True
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Result backend settings
result_expires = 3600  # 1 hour
result_persistent = True
result_compression = 'gzip'

# Task routing
task_routes = {
    'src.tasks.document_tasks.*': {
        'queue': 'documents',
        'routing_key': 'document.generate'
    },
    'src.tasks.ai_tasks.*': {
        'queue': 'ai',
        'routing_key': 'ai.process'
    },
    'src.tasks.file_tasks.*': {
        'queue': 'files',
        'routing_key': 'file.process'
    },
    'src.tasks.notification_tasks.*': {
        'queue': 'notifications',
        'routing_key': 'notification.send'
    },
    'src.tasks.maintenance_tasks.*': {
        'queue': 'maintenance',
        'routing_key': 'maintenance.run'
    }
}

# Queue configuration
task_queues = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default'
    },
    'documents': {
        'exchange': 'documents',
        'exchange_type': 'direct',
        'routing_key': 'document.generate'
    },
    'ai': {
        'exchange': 'ai',
        'exchange_type': 'direct',
        'routing_key': 'ai.process'
    },
    'files': {
        'exchange': 'files',
        'exchange_type': 'direct',
        'routing_key': 'file.process'
    },
    'notifications': {
        'exchange': 'notifications',
        'exchange_type': 'direct',
        'routing_key': 'notification.send'
    },
    'maintenance': {
        'exchange': 'maintenance',
        'exchange_type': 'direct',
        'routing_key': 'maintenance.run'
    }
}

# Task annotations (rate limits)
task_annotations = {
    '*': {'rate_limit': '100/m'},  # Default: 100 per minute
    'src.tasks.ai_tasks.*': {'rate_limit': '10/m'},  # AI tasks: 10 per minute
    'src.tasks.document_tasks.generate_roi_async': {'rate_limit': '5/m'},  # ROI generation: 5 per minute
    'src.tasks.notification_tasks.send_email_notification_async': {'rate_limit': '30/m'},  # Emails: 30 per minute
}

# Worker settings
worker_send_task_events = True
worker_disable_rate_limits = False
worker_state_db = None

# Beat schedule (periodic tasks)
beat_schedule = {
    'cleanup-old-files': {
        'task': 'src.tasks.maintenance_tasks.cleanup_old_files_async',
        'schedule': timedelta(hours=24),  # Daily
        'options': {
            'queue': 'maintenance',
            'expires': 3600
        }
    },
    'generate-usage-reports': {
        'task': 'src.tasks.maintenance_tasks.generate_usage_reports_async',
        'schedule': timedelta(days=7),  # Weekly
        'options': {
            'queue': 'maintenance',
            'expires': 7200
        }
    },
    'backup-database': {
        'task': 'src.tasks.maintenance_tasks.backup_database_async',
        'schedule': timedelta(hours=24),  # Daily
        'options': {
            'queue': 'maintenance',
            'priority': 9  # High priority
        }
    },
    'check-system-health': {
        'task': 'src.tasks.maintenance_tasks.check_system_health_async',
        'schedule': timedelta(minutes=30),  # Every 30 minutes
        'options': {
            'queue': 'maintenance',
            'expires': 1800
        }
    },
    'optimize-database': {
        'task': 'src.tasks.maintenance_tasks.optimize_database_async',
        'schedule': timedelta(days=7),  # Weekly
        'options': {
            'queue': 'maintenance',
            'expires': 3600
        }
    }
}

# Error handling
task_reject_on_worker_lost = True
task_ignore_result = False

# Monitoring
worker_send_task_events = True
task_send_sent_event = True

# Security
worker_hijack_root_logger = False
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Performance optimizations
worker_pool = 'threads'  # Use threads for I/O bound tasks
worker_concurrency = 4  # Number of concurrent workers
worker_max_memory_per_child = 200000  # 200MB per worker

# Redis optimizations
redis_max_connections = 100
redis_socket_connect_timeout = 5
redis_socket_timeout = 5
redis_retry_on_timeout = True
redis_health_check_interval = 30