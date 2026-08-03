import os

import pytest


@pytest.fixture(autouse=True)
def force_regex_parser_mode(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    if request.node.get_closest_marker("local_llm"):
        yield
        return
    monkeypatch.setenv("PARSER_MODE", "regex")
    from shared.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "local_llm: real requests to local Ollama (manual run)",
    )
