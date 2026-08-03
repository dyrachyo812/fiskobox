from celery import Celery
from shared.config import get_settings
from shared.logging import configure_logging

configure_logging()

settings = get_settings()

celery_app = Celery(
    "paperlessbox",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["worker.tasks.receipt"],
)

celery_app.conf.update(
    task_soft_time_limit=120,
    task_time_limit=150,
    task_acks_late=True,
)
