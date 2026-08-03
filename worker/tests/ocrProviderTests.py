from types import SimpleNamespace

import numpy as np
import pytest
from worker.pipeline.ocr.fallback import FallbackOCRProvider
from worker.pipeline.ocr.googleVision import GoogleVisionError, GoogleVisionOCR
from worker.pipeline.ocr.googleVisionQuota import (
    GoogleVisionQuota,
    GoogleVisionQuotaError,
)
from worker.pipeline.ocr.result import OCRResult, WordConfidence
from worker.pipeline.ocr.tesseractProvider import TesseractOCR


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str):
        return self.store.get(key)

    def incr(self, key: str) -> int:
        value = int(self.store.get(key, "0")) + 1
        self.store[key] = str(value)
        return value

    def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return True


class FakePrimary:
    name = "google"

    def __init__(self, *, fail: bool = False, text: str = "primary text") -> None:
        self.fail = fail
        self.text = text
        self.calls = 0

    def extract_text(self, image):
        self.calls += 1
        if self.fail:
            raise GoogleVisionError("quota exceeded")
        return OCRResult(
            raw_text=self.text,
            confidence=0.91,
            words_with_confidence=[WordConfidence("sum", 0.91)],
            provider=self.name,
        )


class FakeFallback:
    name = "tesseract"

    def __init__(self) -> None:
        self.calls = 0

    def extract_text(self, image):
        self.calls += 1
        return OCRResult(
            raw_text="fallback text",
            confidence=0.55,
            words_with_confidence=[],
            provider=self.name,
        )


class TestFallbackOCRProvider:
    def test_uses_primary_when_available(self):
        primary = FakePrimary()
        fallback = FakeFallback()
        provider = FallbackOCRProvider(primary, fallback)
        result = provider.extract_text(np.zeros((10, 10), dtype=np.uint8))
        assert result.raw_text == "primary text"
        assert result.provider == "google"
        assert result.used_fallback is False
        assert primary.calls == 1
        assert fallback.calls == 0

    def test_switches_to_tesseract_on_primary_failure(self):
        primary = FakePrimary(fail=True)
        fallback = FakeFallback()
        provider = FallbackOCRProvider(primary, fallback)
        result = provider.extract_text(np.zeros((10, 10), dtype=np.uint8))
        assert result.raw_text == "fallback text"
        assert result.provider == "tesseract"
        assert result.used_fallback is True
        assert "quota" in (result.fallback_reason or "")
        assert primary.calls == 1
        assert fallback.calls == 1


class TestGoogleVisionQuota:
    def test_increments_and_warns_near_limit(self):
        redis_client = FakeRedis()
        quota = GoogleVisionQuota(
            redis_client,
            monthly_limit=1000,
            warn_threshold=3,
            enforce_limit=True,
        )
        assert quota.current_count() == 0
        assert quota.record_usage() == 1
        assert quota.record_usage() == 2
        assert quota.record_usage() == 3
        assert quota.is_near_limit()
        assert not quota.is_exhausted()
        assert redis_client.ttls[quota.month_key()] == 40 * 24 * 60 * 60

    def test_enforce_blocks_at_limit(self):
        redis_client = FakeRedis()
        redis_client.store[GoogleVisionQuota(redis_client).month_key()] = "1000"
        quota = GoogleVisionQuota(
            redis_client,
            monthly_limit=1000,
            warn_threshold=900,
            enforce_limit=True,
        )
        with pytest.raises(GoogleVisionQuotaError, match="исчерпан"):
            quota.ensure_available()

    def test_without_enforce_allows_over_limit(self):
        redis_client = FakeRedis()
        redis_client.store[GoogleVisionQuota(redis_client).month_key()] = "1000"
        quota = GoogleVisionQuota(
            redis_client,
            monthly_limit=1000,
            warn_threshold=900,
            enforce_limit=False,
        )
        quota.ensure_available()


class TestGoogleVisionOCRMocked:
    def test_parses_document_text_response(self, monkeypatch: pytest.MonkeyPatch):
        class FakeSymbol:
            def __init__(self, text: str) -> None:
                self.text = text

        class FakeWord:
            def __init__(self, text: str, confidence: float) -> None:
                self.symbols = [FakeSymbol(character) for character in text]
                self.confidence = confidence

        class FakeParagraph:
            def __init__(self) -> None:
                self.words = [FakeWord("ИТОГО", 0.9), FakeWord("100.00", 0.8)]

        class FakeBlock:
            def __init__(self) -> None:
                self.paragraphs = [FakeParagraph()]

        class FakePage:
            def __init__(self) -> None:
                self.blocks = [FakeBlock()]

        class FakeAnnotation:
            def __init__(self) -> None:
                self.text = "ИТОГО 100.00"
                self.pages = [FakePage()]

        class FakeResponse:
            error = SimpleNamespace(message="")
            full_text_annotation = FakeAnnotation()

        redis_client = FakeRedis()
        quota = GoogleVisionQuota(redis_client, monthly_limit=1000, warn_threshold=900)
        provider = GoogleVisionOCR(timeout_seconds=5, quota=quota)
        monkeypatch.setattr(provider, "_annotate", lambda content: FakeResponse())

        result = provider.extract_text(np.zeros((20, 20), dtype=np.uint8))
        assert result.provider == "google"
        assert result.raw_text == "ИТОГО 100.00"
        assert result.confidence == pytest.approx(0.85)
        assert [word.text for word in result.words_with_confidence] == [
            "ИТОГО",
            "100.00",
        ]
        assert quota.current_count() == 1

    def test_timeout_raises_google_vision_error(self, monkeypatch: pytest.MonkeyPatch):
        def slow_annotate(content: bytes):
            import time

            time.sleep(0.2)
            return SimpleNamespace(
                error=SimpleNamespace(message=""),
                full_text_annotation=None,
            )

        provider = GoogleVisionOCR(timeout_seconds=0.01)
        monkeypatch.setattr(provider, "_annotate", slow_annotate)
        with pytest.raises(GoogleVisionError, match="таймаут"):
            provider.extract_text(np.zeros((8, 8), dtype=np.uint8))

    def test_quota_exhausted_falls_back_to_tesseract(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        redis_client = FakeRedis()
        quota = GoogleVisionQuota(
            redis_client,
            monthly_limit=1,
            warn_threshold=1,
            enforce_limit=True,
        )
        redis_client.store[quota.month_key()] = "1"
        google = GoogleVisionOCR(timeout_seconds=5, quota=quota)
        monkeypatch.setattr(
            google,
            "_annotate",
            lambda content: (_ for _ in ()).throw(AssertionError("API must not run")),
        )
        fallback = FakeFallback()
        provider = FallbackOCRProvider(google, fallback)
        result = provider.extract_text(np.zeros((8, 8), dtype=np.uint8))
        assert result.provider == "tesseract"
        assert result.used_fallback is True
        assert "лимит" in (result.fallback_reason or "")
        assert fallback.calls == 1


class TestTesseractOCRWrapper:
    def test_extract_text_uses_engine(self, monkeypatch: pytest.MonkeyPatch):
        provider = TesseractOCR(languages="eng")

        class FakeEngine:
            def recognize_receipt(self, image, variant: int = 0) -> str:
                return "TOTAL 12.00"

        provider.engine = FakeEngine()
        monkeypatch.setattr(
            provider,
            "_word_confidences",
            lambda image: (
                [WordConfidence("TOTAL", 0.7), WordConfidence("12.00", 0.8)],
                0.75,
            ),
        )
        result = provider.extract_text(np.zeros((12, 12), dtype=np.uint8))
        assert result.provider == "tesseract"
        assert result.raw_text == "TOTAL 12.00"
        assert result.confidence == 0.75
