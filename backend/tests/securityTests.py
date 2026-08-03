from datetime import datetime, timedelta, timezone

from backend.core.security import create_access_token, decode_access_token
from jose import jwt


class TestJwtLogic:
    def test_create_and_decode_roundtrip(self, jwt_settings):
        token = create_access_token("123456789")
        assert decode_access_token(token) == "123456789"

    def test_expired_token_returns_none(self, jwt_settings):
        payload = {
            "sub": "123456789",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = jwt.encode(
            payload,
            jwt_settings.jwt_secret,
            algorithm=jwt_settings.jwt_algorithm,
        )
        assert decode_access_token(token) is None

    def test_wrong_signature_returns_none(self, jwt_settings):
        payload = {
            "sub": "123456789",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(payload, "totally-different-secret", algorithm="HS256")
        assert decode_access_token(token) is None

    def test_malformed_token_returns_none(self, jwt_settings):
        assert decode_access_token("not.a.jwt") is None
        assert decode_access_token("") is None

    def test_token_without_subject_returns_none(self, jwt_settings):
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload,
            jwt_settings.jwt_secret,
            algorithm=jwt_settings.jwt_algorithm,
        )
        assert decode_access_token(token) is None
