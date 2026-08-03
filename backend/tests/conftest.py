from types import SimpleNamespace

import pytest
from shared.config.settings import get_settings


@pytest.fixture
def jwt_settings(monkeypatch):
    get_settings.cache_clear()
    settings = SimpleNamespace(
        jwt_secret="unit-test-secret-key",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
    )
    monkeypatch.setattr("backend.core.security.get_settings", lambda: settings)
    return settings
