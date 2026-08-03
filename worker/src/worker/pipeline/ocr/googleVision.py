import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import numpy as np

from worker.pipeline.ocr.imageBytes import image_to_png_bytes
from worker.pipeline.ocr.provider import OCRProvider
from worker.pipeline.ocr.result import OCRResult, WordConfidence
from worker.pipeline.ocr.googleVisionQuota import (
    GoogleVisionQuota,
    GoogleVisionQuotaError,
)


class GoogleVisionError(Exception):
    pass


class GoogleVisionOCR(OCRProvider):
    name = "google"

    def __init__(
        self,
        *,
        credentials_path: str | None = None,
        timeout_seconds: float = 30.0,
        quota: GoogleVisionQuota | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.quota = quota
        if credentials_path:
            os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if not credentials:
            raise GoogleVisionError(
                "GOOGLE_APPLICATION_CREDENTIALS не задан — Google Vision недоступен"
            )
        if not os.path.isfile(credentials):
            raise GoogleVisionError(
                f"файл credentials не найден: {credentials}"
            )
        try:
            from google.cloud import vision
        except ImportError as error:
            raise GoogleVisionError(
                "google-cloud-vision не установлен"
            ) from error
        try:
            self._client = vision.ImageAnnotatorClient()
        except Exception as error:
            raise GoogleVisionError(
                f"не удалось инициализировать Google Vision client: {error}"
            ) from error
        return self._client

    def _annotate(self, content: bytes):
        from google.cloud import vision

        client = self._get_client()
        vision_image = vision.Image(content=content)
        return client.document_text_detection(image=vision_image)

    def extract_text(self, image: np.ndarray) -> OCRResult:
        if self.quota is not None:
            try:
                self.quota.ensure_available()
            except GoogleVisionQuotaError as error:
                raise GoogleVisionError(str(error)) from error

        content = image_to_png_bytes(image)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._annotate, content)
                response = future.result(timeout=self.timeout_seconds)
        except FuturesTimeout as error:
            raise GoogleVisionError(
                f"таймаут Google Vision ({self.timeout_seconds}s)"
            ) from error
        except GoogleVisionError:
            raise
        except Exception as error:
            raise GoogleVisionError(f"ошибка Google Vision API: {error}") from error

        if getattr(response, "error", None) and getattr(response.error, "message", ""):
            raise GoogleVisionError(response.error.message)

        if self.quota is not None:
            self.quota.record_usage()

        annotation = response.full_text_annotation
        if annotation is None or not annotation.text:
            return OCRResult(
                raw_text="",
                confidence=None,
                words_with_confidence=[],
                provider=self.name,
            )

        words: list[WordConfidence] = []
        scores: list[float] = []
        for page in annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        token = "".join(symbol.text for symbol in word.symbols)
                        if not token.strip():
                            continue
                        conf = float(word.confidence) if word.confidence else 0.0
                        words.append(WordConfidence(text=token, confidence=conf))
                        scores.append(conf)

        average = sum(scores) / len(scores) if scores else None
        return OCRResult(
            raw_text=annotation.text.strip(),
            confidence=average,
            words_with_confidence=words,
            provider=self.name,
        )
