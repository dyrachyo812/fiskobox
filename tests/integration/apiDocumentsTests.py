from decimal import Decimal
from pathlib import Path

import pytest
from shared.models import Document, DocumentStatus, Receipt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

pytestmark = pytest.mark.asyncio


async def _create_document(
    session: AsyncSession,
    user_id: int,
    image_path: str,
    *,
    with_receipt: bool = False,
) -> Document:
    document = Document(
        user_id=user_id,
        image_path=image_path,
        image_hash="hash-integration-1",
        status=DocumentStatus.pending,
    )
    session.add(document)
    await session.flush()
    if with_receipt:
        session.add(
            Receipt(
                document_id=document.id,
                amount=Decimal("10.00"),
                currency="UAH",
                merchant_name="Seed Shop",
                category="Продукты",
            )
        )
    await session.commit()
    await session.refresh(document)
    return document


class TestDocumentApiLifecycle:
    async def test_create_get_patch_and_verify_db(
        self,
        api_client,
        db_session: AsyncSession,
        test_user,
        owner_token: str,
        prepare_fixtures: Path,
        test_env: dict[str, str],
    ):
        source = prepare_fixtures / "receiptAtb.png"
        stored = Path(test_env["UPLOAD_DIR"]) / "lifecycle.png"
        stored.write_bytes(source.read_bytes())

        document = await _create_document(db_session, test_user.id, str(stored))

        headers = {"Authorization": f"Bearer {owner_token}"}
        get_response = await api_client.get(
            f"/api/documents/{document.id}", headers=headers
        )
        assert get_response.status_code == 200
        body = get_response.json()
        assert body["id"] == document.id
        assert body["status"] == "pending"

        patch_response = await api_client.patch(
            f"/api/documents/{document.id}",
            headers=headers,
            json={
                "amount": "134.90",
                "currency": "UAH",
                "merchant_name": "ATB Market",
                "purchase_date": "2024-03-15",
                "category": "Продукты",
            },
        )
        assert patch_response.status_code == 200
        patched = patch_response.json()
        assert patched["receipt"]["merchant_name"] == "ATB Market"
        assert patched["receipt"]["is_manually_corrected"] is True

        result = await db_session.scalar(
            select(Document)
            .where(Document.id == document.id)
            .options(selectinload(Document.receipt))
        )
        assert result is not None
        assert result.receipt is not None
        assert result.receipt.amount == Decimal("134.90")
        assert result.receipt.currency == "UAH"
        assert result.receipt.merchant_name == "ATB Market"
        assert result.receipt.is_manually_corrected is True


class TestDocumentAccessControl:
    async def test_other_user_get_returns_403(
        self,
        api_client,
        db_session: AsyncSession,
        test_user,
        other_token: str,
        prepare_fixtures: Path,
        test_env: dict[str, str],
    ):
        source = prepare_fixtures / "receiptSilpo.png"
        stored = Path(test_env["UPLOAD_DIR"]) / "foreign.png"
        stored.write_bytes(source.read_bytes())
        document = await _create_document(db_session, test_user.id, str(stored))

        response = await api_client.get(
            f"/api/documents/{document.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 403
        assert "чуж" in response.json()["detail"].lower() or "доступ" in response.json()[
            "detail"
        ].lower()

    async def test_other_user_patch_returns_403(
        self,
        api_client,
        db_session: AsyncSession,
        test_user,
        other_token: str,
        prepare_fixtures: Path,
        test_env: dict[str, str],
    ):
        source = prepare_fixtures / "receiptSilpo.png"
        stored = Path(test_env["UPLOAD_DIR"]) / "foreign-patch.png"
        stored.write_bytes(source.read_bytes())
        document = await _create_document(
            db_session, test_user.id, str(stored), with_receipt=True
        )

        response = await api_client.patch(
            f"/api/documents/{document.id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"amount": "999.00"},
        )
        assert response.status_code == 403

    async def test_missing_document_returns_404(
        self, api_client, owner_token: str
    ):
        response = await api_client.get(
            "/api/documents/999999",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 404

    async def test_invalid_json_returns_422(self, api_client, owner_token: str):
        response = await api_client.patch(
            "/api/documents/1",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"amount": -5, "currency": "U"},
        )
        assert response.status_code == 422
