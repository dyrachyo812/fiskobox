import numpy as np

from shared.logging import get_logger

from worker.pipeline.ocr.provider import OCRProvider
from worker.pipeline.ocr.result import OCRResult

logger = get_logger(__name__)


class FallbackOCRProvider(OCRProvider):
    name = "fallback"

    def __init__(self, primary: OCRProvider, fallback: OCRProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def extract_text(self, image: np.ndarray) -> OCRResult:
        try:
            result = self.primary.extract_text(image)
            logger.info(
                "OCR primary succeeded",
                extra={
                    "ocr_provider": result.provider,
                    "ocr_confidence": result.confidence,
                    "ocr_chars": len(result.raw_text or ""),
                },
            )
            return result
        except Exception as error:
            reason = str(error)
            logger.warning(
                "OCR primary failed, switching to fallback",
                extra={
                    "ocr_provider": self.primary.name,
                    "fallback_provider": self.fallback.name,
                    "fallback_reason": reason,
                },
            )
            result = self.fallback.extract_text(image)
            result.used_fallback = True
            result.fallback_reason = reason
            result.provider = self.fallback.name
            logger.info(
                "OCR fallback succeeded",
                extra={
                    "ocr_provider": result.provider,
                    "ocr_confidence": result.confidence,
                    "ocr_chars": len(result.raw_text or ""),
                    "used_fallback": True,
                    "fallback_reason": reason,
                },
            )
            return result
