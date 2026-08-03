import redis
from shared.config import get_settings
from shared.logging import get_logger

from worker.pipeline.ocr.fallback import FallbackOCRProvider
from worker.pipeline.ocr.googleVision import GoogleVisionOCR
from worker.pipeline.ocr.googleVisionQuota import GoogleVisionQuota
from worker.pipeline.ocr.provider import OCRProvider
from worker.pipeline.ocr.tesseractProvider import TesseractOCR

logger = get_logger(__name__)


def _resolve_provider_name(settings) -> str:
    provider = (settings.ocr_provider or "").strip().lower()
    if provider:
        return provider
    engine = (settings.ocr_engine or "tesseract").strip().lower()
    return engine


def build_tesseract_provider() -> TesseractOCR:
    settings = get_settings()
    return TesseractOCR(languages=settings.tesseract_languages)


def build_google_vision_quota() -> GoogleVisionQuota:
    settings = get_settings()
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return GoogleVisionQuota(
        client,
        monthly_limit=settings.google_vision_monthly_limit,
        warn_threshold=settings.google_vision_warn_threshold,
        enforce_limit=settings.google_vision_enforce_limit,
    )


def build_ocr_provider() -> OCRProvider:
    settings = get_settings()
    provider_name = _resolve_provider_name(settings)
    tesseract = build_tesseract_provider()

    if provider_name == "tesseract":
        logger.info("OCR provider selected", extra={"ocr_provider": "tesseract"})
        return tesseract

    if provider_name == "google":
        google = GoogleVisionOCR(
            credentials_path=settings.google_application_credentials,
            timeout_seconds=settings.ocr_timeout_seconds,
            quota=build_google_vision_quota(),
        )
        logger.info(
            "OCR provider selected with tesseract fallback",
            extra={
                "ocr_provider": "google",
                "fallback_provider": "tesseract",
                "google_vision_monthly_limit": settings.google_vision_monthly_limit,
                "google_vision_enforce_limit": settings.google_vision_enforce_limit,
            },
        )
        return FallbackOCRProvider(primary=google, fallback=tesseract)

    if provider_name == "aws":
        raise ValueError(
            "OCR_PROVIDER=aws пока не реализован. Используйте google или tesseract."
        )

    raise ValueError(f"Unsupported OCR_PROVIDER: {provider_name}")


def build_ocr_engine():
    return build_ocr_provider()
