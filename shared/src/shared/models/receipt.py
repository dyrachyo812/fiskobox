from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from shared.models.document import Document


class Receipt(Base, CreatedAtMixin):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), unique=True, index=True
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    merchant_name: Mapped[str | None] = mapped_column(String(255))
    purchase_date: Mapped[date | None] = mapped_column(Date, index=True)
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    is_manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    amount_matched_by: Mapped[str | None] = mapped_column(String(64))
    date_matched_by: Mapped[str | None] = mapped_column(String(64))
    merchant_matched_by: Mapped[str | None] = mapped_column(String(64))
    needs_manual_review: Mapped[bool] = mapped_column(Boolean, default=False)

    document: Mapped["Document"] = relationship(back_populates="receipt")
