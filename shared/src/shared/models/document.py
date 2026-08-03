import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from shared.models.receipt import Receipt
    from shared.models.user import User


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Document(Base, CreatedAtMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    image_path: Mapped[str] = mapped_column(String(512))
    image_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.pending,
        index=True,
    )
    raw_ocr_text: Mapped[str | None] = mapped_column(Text)
    low_quality_scan: Mapped[bool] = mapped_column(Boolean, default=False)
    sharpness_score: Mapped[float | None] = mapped_column(Float)
    ocr_provider: Mapped[str | None] = mapped_column(String(32))
    ocr_confidence: Mapped[float | None] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="documents")
    receipt: Mapped["Receipt | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
