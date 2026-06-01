"""
Celery application.
Used for offloading long-running tasks (OCR, complex solves) from FastAPI request threads.
Start workers with:  celery -A workflows.celery_app worker --loglevel=info
"""
from celery import Celery

from core.config import settings

celery_app = Celery(
    "mathbot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,       # hard kill after 2 minutes
    task_soft_time_limit=90,   # sends SoftTimeLimitExceeded at 90s
    worker_prefetch_multiplier=1,  # fairness — don't hoard tasks
)

# Auto-discover tasks in workflows/
celery_app.autodiscover_tasks(["workflows.ocr_tasks", "workflows.solve_tasks"])
