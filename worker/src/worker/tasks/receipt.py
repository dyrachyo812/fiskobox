from celery.exceptions import Retry, SoftTimeLimitExceeded
from shared.config import get_settings
from shared.logging import get_logger
from shared.models import DocumentStatus

from worker.celeryapp import celery_app
from worker.db.session import session_scope
from worker.notifications import (
    GENERIC_FAILURE_MESSAGE,
    failure_message,
    notify_result,
    success_message,
)
from worker.pipeline.ocr import build_ocr_provider
from worker.pipeline.parsing import parse_receipt
from worker.pipeline.preprocessing import (
    count_receipts,
    is_blurry,
    laplacian_variance,
    load_grayscale,
)
from worker.pipeline.quality import is_meaningful
from worker.repositories.categoryrepository import load_categories
from worker.repositories.documentrepository import (
    fetch_document,
    mark_failed,
    mark_processing,
    save_result,
)

logger = get_logger(__name__)
settings = get_settings()

BLURRY_MESSAGE = "фото размытое, переснимите чётче"
MULTIPLE_MESSAGE = "на фото несколько чеков, отправьте по одному"


class OcrQualityError(Exception):
    pass


@celery_app.task(
    bind=True,
    name="worker.tasks.receipt.process_receipt_image",
    max_retries=2,
    default_retry_delay=3,
    soft_time_limit=180,
    time_limit=210,
)
def process_receipt_image(self, document_id: int) -> dict:
    attempt = self.request.retries
    chat_id: int | None = None

    def log(stage: str, message: str, level: str = "info") -> None:
        getattr(logger, level)(
            message,
            extra={
                "document_id": document_id,
                "stage": stage,
                "attempt": attempt,
                "chat_id": chat_id,
            },
        )

    def safe_notify(text: str) -> bool:
        if chat_id is None:
            log("notify", "chat_id неизвестен, уведомление пропущено", level="error")
            return False
        log("notify", "Отправка результата в Telegram")
        sent = notify_result(chat_id, text)
        if sent:
            log("notify", "Отправка результата готова")
        else:
            log(
                "notify",
                "Отправка в Telegram не удалась",
                level="error",
            )
        return sent

    def fail(reason: str, retryable: bool, user_text: str | None = None) -> dict:
        log("failed", reason, level="warning")
        with session_scope() as session:
            document = fetch_document(session, document_id)
            if document is not None:
                mark_failed(session, document, reason)
        safe_notify(user_text or failure_message(reason))
        return {"status": "failed", "reason": reason, "retryable": retryable}

    try:
        log("received", "Задача принята в обработку")
        low_sharpness = False
        sharpness = None

        with session_scope() as session:
            document = fetch_document(session, document_id)
            if document is None:
                log("missing", "Документ не найден", level="warning")
                return {"status": "missing"}
            mark_processing(session, document)
            image_path = document.image_path
            chat_id = document.user.telegram_id
            log("loaded", f"Документ загружен для chat_id={chat_id}")

        try:
            gray = load_grayscale(image_path)
            sharpness = laplacian_variance(gray)
            log("sharpness", f"Laplacian variance={sharpness:.2f}")

            if is_blurry(gray, settings.blur_variance_threshold):
                return fail(BLURRY_MESSAGE, retryable=False)
            low_sharpness = sharpness < settings.blur_warn_variance_threshold
            if count_receipts(gray) > 1:
                return fail(MULTIPLE_MESSAGE, retryable=False)

            log("preprocess", "OpenCV готов")
            log("ocr", "Запуск OCR")
            ocr_result = build_ocr_provider().extract_text(gray)
            raw_text = ocr_result.raw_text
            log(
                "ocr",
                (
                    f"OCR готов provider={ocr_result.provider} "
                    f"confidence={ocr_result.confidence} "
                    f"fallback={ocr_result.used_fallback} "
                    f"chars={len(raw_text)}"
                ),
            )
            if ocr_result.used_fallback:
                log(
                    "ocr",
                    f"Использован fallback OCR: {ocr_result.fallback_reason}",
                    level="warning",
                )
            log(
                "ocr",
                f"raw OCR ({len(raw_text)} chars): {raw_text[:1500]}",
            )

            if not is_meaningful(raw_text):
                raise OcrQualityError("распознан пустой или нечитаемый текст")
        except SoftTimeLimitExceeded:
            raise
        except OcrQualityError as error:
            if self.request.retries < self.max_retries:
                log("retry", f"Повтор из-за качества OCR: {error}")
                raise self.retry(exc=error) from error
            return fail(
                str(error),
                retryable=True,
                user_text=GENERIC_FAILURE_MESSAGE,
            )
        except Exception as error:
            log("error", f"Сбой обработки: {error}", level="exception")
            if self.request.retries < self.max_retries:
                raise self.retry(exc=error) from error
            return fail(
                "внутренняя ошибка обработки",
                retryable=True,
                user_text=GENERIC_FAILURE_MESSAGE,
            )

        with session_scope() as session:
            document = fetch_document(session, document_id)
            categories = load_categories(session)
            parsed = parse_receipt(raw_text, categories)
            parsed["low_quality_scan"] = low_sharpness
            log(
                "parse",
                (
                    f"режим={parsed.get('parser_mode')} "
                    f"review={parsed.get('needs_manual_review')} "
                    f"merchant={parsed.get('merchant_name')} "
                    f"amount={parsed.get('amount')}"
                ),
            )
            save_result(
                session,
                document,
                raw_text,
                parsed,
                low_quality_scan=low_sharpness,
                sharpness_score=sharpness,
                ocr_provider=ocr_result.provider,
                ocr_confidence=ocr_result.confidence,
            )
        log("parse", "Парсинг готов, результат сохранён")

        safe_notify(success_message(parsed, low_sharpness=low_sharpness))
        return {"status": "done"}

    except Retry:
        raise
    except SoftTimeLimitExceeded:
        log("timeout", "Превышен soft_time_limit задачи", level="error")
        with session_scope() as session:
            document = fetch_document(session, document_id)
            if document is not None and document.status != DocumentStatus.done:
                mark_failed(session, document, "timeout")
        safe_notify(GENERIC_FAILURE_MESSAGE)
        return {"status": "failed", "reason": "timeout", "retryable": False}
    except Exception as error:
        log("error", f"Необработанное исключение пайплайна: {error}", level="exception")
        with session_scope() as session:
            document = fetch_document(session, document_id)
            if document is not None and document.status != DocumentStatus.done:
                mark_failed(session, document, "unhandled")
        safe_notify(GENERIC_FAILURE_MESSAGE)
        return {"status": "failed", "reason": "unhandled", "retryable": False}
