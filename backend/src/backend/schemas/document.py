from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from shared.models import DocumentStatus


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: Decimal | None = None
    currency: str | None = None
    merchant_name: str | None = None
    purchase_date: date | None = None
    category: str | None = None
    is_manually_corrected: bool = False
    amount_matched_by: str | None = None
    date_matched_by: str | None = None
    merchant_matched_by: str | None = None
    needs_manual_review: bool = False


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: DocumentStatus
    created_at: datetime
    receipt: ReceiptOut | None = None
    low_quality_scan: bool = False


class DocumentDetailOut(DocumentOut):
    raw_ocr_text: str | None = None
    image_url: str
    sharpness_score: float | None = None


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int


class DocumentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0, lt=Decimal(1000000))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    merchant_name: str | None = Field(default=None, min_length=1, max_length=255)
    purchase_date: date | None = None
    category: str | None = Field(default=None, min_length=1, max_length=64)
