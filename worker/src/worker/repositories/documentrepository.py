from shared.models import Document, DocumentStatus, Receipt
from sqlalchemy.orm import Session


def fetch_document(session: Session, document_id: int) -> Document | None:
    return session.get(Document, document_id)


def mark_processing(session: Session, document: Document) -> None:
    document.status = DocumentStatus.processing


def mark_failed(session: Session, document: Document, reason: str) -> None:
    document.status = DocumentStatus.failed
    document.raw_ocr_text = f"[FAILED] {reason}"


def save_result(
    session: Session,
    document: Document,
    raw_text: str,
    parsed: dict,
    *,
    low_quality_scan: bool = False,
    sharpness_score: float | None = None,
    ocr_provider: str | None = None,
    ocr_confidence: float | None = None,
) -> None:
    document.raw_ocr_text = raw_text
    document.status = DocumentStatus.done
    document.low_quality_scan = low_quality_scan
    document.sharpness_score = sharpness_score
    document.ocr_provider = ocr_provider
    document.ocr_confidence = ocr_confidence

    receipt = document.receipt or Receipt(document_id=document.id)
    receipt.amount = parsed["amount"]
    receipt.currency = parsed["currency"]
    receipt.merchant_name = parsed["merchant_name"]
    receipt.purchase_date = parsed["purchase_date"]
    receipt.category = parsed["category"]
    receipt.is_manually_corrected = False
    receipt.amount_matched_by = parsed.get("amount_matched_by")
    receipt.date_matched_by = parsed.get("date_matched_by")
    receipt.merchant_matched_by = parsed.get("merchant_matched_by")
    receipt.needs_manual_review = bool(parsed.get("needs_manual_review"))

    session.add(receipt)
