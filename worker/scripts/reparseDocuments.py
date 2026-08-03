from shared.models import Document
from sqlalchemy import select
from worker.db.session import session_scope
from worker.pipeline.parsing import parse_receipt
from worker.repositories.categoryrepository import load_categories
from worker.repositories.documentrepository import fetch_document, save_result


def main() -> None:
    with session_scope() as session:
        document_ids = list(session.scalars(select(Document.id).order_by(Document.id)))
        categories = load_categories(session)

    for document_id in document_ids:
        with session_scope() as session:
            document = fetch_document(session, document_id)
            if document is None or not document.raw_ocr_text:
                continue
            if document.raw_ocr_text.startswith("[FAILED]"):
                continue
            categories = load_categories(session)
            parsed = parse_receipt(document.raw_ocr_text, categories)
            save_result(
                session,
                document,
                document.raw_ocr_text,
                parsed,
                low_quality_scan=document.low_quality_scan,
                sharpness_score=document.sharpness_score,
            )
            print(
                document_id,
                parsed["merchant_name"],
                parsed["purchase_date"],
                parsed["category"],
                parsed["amount"],
                parsed["currency"],
                parsed["amount_matched_by"],
                parsed["date_matched_by"],
                parsed["merchant_matched_by"],
            )


if __name__ == "__main__":
    main()
