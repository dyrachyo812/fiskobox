from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from shared.models import Document, DocumentStatus, User
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


class FakeOcrProvider:
    def __init__(self, text: str) -> None:
        self.text = text
        self.name = "fake"

    def extract_text(self, image):
        from worker.pipeline.ocr.result import OCRResult

        return OCRResult(
            raw_text=self.text,
            confidence=0.99,
            words_with_confidence=[],
            provider="fake",
        )


@pytest.fixture
def pipeline_user(sync_session: Session) -> User:
    user = User(telegram_id=200001, username="pipeline")
    sync_session.add(user)
    sync_session.commit()
    sync_session.refresh(user)
    return user


class TestCeleryPipeline:
    def test_process_receipt_reaches_done_with_parsed_data(
        self,
        sync_session: Session,
        pipeline_user: User,
        prepare_fixtures: Path,
        test_env: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ):
        source = prepare_fixtures / "receiptMultiAmount.png"
        stored = Path(test_env["UPLOAD_DIR"]) / "pipeline-done.png"
        stored.write_bytes(source.read_bytes())

        document = Document(
            user_id=pipeline_user.id,
            image_path=str(stored),
            image_hash="pipeline-hash-1",
            status=DocumentStatus.pending,
        )
        sync_session.add(document)
        sync_session.commit()
        sync_session.refresh(document)
        document_id = document.id

        ocr_text = (
            "Pyaterochka\n"
            "08.07.2024\n"
            "ItemA 45.00\n"
            "ItemB 89.90\n"
            "ITOGO: 146.90 RUB\n"
        )
        monkeypatch.setattr(
            "worker.tasks.receipt.build_ocr_provider",
            lambda: FakeOcrProvider(ocr_text),
        )
        monkeypatch.setattr(
            "worker.tasks.receipt.notify_result",
            lambda chat_id, text: True,
        )
        monkeypatch.setattr(
            "worker.tasks.receipt.settings",
            SimpleNamespace(
                blur_variance_threshold=1.0,
                blur_warn_variance_threshold=250.0,
            ),
        )

        from worker.tasks.receipt import process_receipt_image

        result = process_receipt_image.apply(kwargs={"document_id": document_id}).get()
        assert result["status"] == "done"

        sync_session.expire_all()
        saved = sync_session.scalar(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.receipt), selectinload(Document.user))
        )
        assert saved is not None
        assert saved.status == DocumentStatus.done
        assert saved.raw_ocr_text is not None
        assert "ITOGO" in saved.raw_ocr_text
        assert saved.receipt is not None
        assert saved.receipt.amount == Decimal("146.90")
        assert saved.receipt.currency == "RUB"
        assert saved.receipt.merchant_name == "Pyaterochka"

    def test_process_blurry_receipt_reaches_failed(
        self,
        sync_session: Session,
        pipeline_user: User,
        prepare_fixtures: Path,
        test_env: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ):
        source = prepare_fixtures / "receiptBlurry.png"
        stored = Path(test_env["UPLOAD_DIR"]) / "pipeline-blur.png"
        stored.write_bytes(source.read_bytes())

        document = Document(
            user_id=pipeline_user.id,
            image_path=str(stored),
            image_hash="pipeline-hash-blur",
            status=DocumentStatus.pending,
        )
        sync_session.add(document)
        sync_session.commit()
        sync_session.refresh(document)
        document_id = document.id

        monkeypatch.setattr(
            "worker.tasks.receipt.notify_result",
            lambda chat_id, text: True,
        )
        monkeypatch.setattr(
            "worker.tasks.receipt.settings",
            SimpleNamespace(
                blur_variance_threshold=500.0,
                blur_warn_variance_threshold=250.0,
            ),
        )

        from worker.tasks.receipt import process_receipt_image

        result = process_receipt_image.apply(kwargs={"document_id": document_id}).get()
        assert result["status"] == "failed"
        assert "размыт" in result["reason"]

        sync_session.expire_all()
        saved = sync_session.scalar(select(Document).where(Document.id == document_id))
        assert saved is not None
        assert saved.status == DocumentStatus.failed
