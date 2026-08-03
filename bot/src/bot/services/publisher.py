from celery import Celery
from shared.config import get_settings
from shared.schemas import PROCESS_RECEIPT_TASK

settings = get_settings()
celery_client = Celery(broker=settings.celery_broker_url)


def enqueue_document(document_id: int) -> None:
    # Бот только публикует задачу в брокер и не ждёт результат — весь OCR идёт в воркере.
    celery_client.send_task(PROCESS_RECEIPT_TASK, kwargs={"document_id": document_id})
