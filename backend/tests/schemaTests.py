from datetime import date
from decimal import Decimal

import pytest
from backend.schemas.analytics import CategorySummary, SummaryOut
from backend.schemas.auth import LinkTelegramRequest, TokenResponse
from backend.schemas.document import DocumentUpdate
from pydantic import ValidationError


class TestLinkTelegramRequest:
    def test_valid_six_digit_code(self):
        payload = LinkTelegramRequest(code="123456")
        assert payload.code == "123456"

    @pytest.mark.parametrize(
        "code",
        ["", "12345", "1234567", "abcdef", "12 456", "12345a"],
    )
    def test_invalid_codes_rejected(self, code):
        with pytest.raises(ValidationError):
            LinkTelegramRequest(code=code)

    def test_missing_code_rejected(self):
        with pytest.raises(ValidationError):
            LinkTelegramRequest()


class TestTokenResponse:
    def test_default_token_type(self):
        payload = TokenResponse(access_token="abc.def.ghi")
        assert payload.token_type == "bearer"

    def test_empty_access_token_rejected(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="")


class TestDocumentUpdate:
    def test_valid_partial_update(self):
        payload = DocumentUpdate(
            amount=Decimal("12.50"),
            currency="UAH",
            merchant_name="АТБ",
            purchase_date=date(2024, 3, 15),
            category="Продукты",
        )
        assert payload.amount == Decimal("12.50")
        assert payload.currency == "UAH"

    def test_all_optional_fields_may_be_omitted(self):
        payload = DocumentUpdate()
        assert payload.amount is None

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUpdate(amount=Decimal(-1))

    def test_absurd_amount_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUpdate(amount=Decimal(1000000))

    def test_invalid_currency_length_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUpdate(currency="UA")
        with pytest.raises(ValidationError):
            DocumentUpdate(currency="UAHH")

    def test_empty_merchant_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUpdate(merchant_name="")

    def test_invalid_date_type_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUpdate(purchase_date="not-a-date")


class TestAnalyticsSchemas:
    def test_summary_out_valid(self):
        payload = SummaryOut(
            period="month",
            total=Decimal("100.00"),
            categories=[
                CategorySummary(category="Продукты", amount=Decimal("100.00"), count=2)
            ],
        )
        assert payload.total == Decimal("100.00")
        assert payload.categories[0].count == 2

    def test_summary_out_invalid_total_rejected(self):
        with pytest.raises(ValidationError):
            SummaryOut(period="month", total="not-number", categories=[])
