from celery import Celery
from celery.schedules import crontab

celery_app = Celery('auditcore', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
celery_app.conf.timezone = 'Asia/Baghdad'
celery_app.conf.beat_schedule = {
    'generate-daily-auditor-tasks': {
        'task': 'app.workers.tasks.generate_daily_tasks',
        'schedule': crontab(hour=8, minute=0),
    },
    'apply-sla-demerits': {
        'task': 'app.workers.tasks.apply_sla_demerits',
        'schedule': crontab(minute='*/15'),
    },
}
