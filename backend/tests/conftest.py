from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.clock.now",
        lambda tz: datetime(2026, 11, 16, 18, 0, tzinfo=tz),
    )

    class _NoNetwork:
        def __init__(self, *args, **kwargs):
            raise AssertionError("tests must not open a network connection")

    monkeypatch.setattr("app.services.ask.httpx.Client", _NoNetwork)

    db_path = tmp_path / "test.db"
    settings = Settings(
        _env_file=None,
        app_env="test",
        app_port=8080,
        database_url=f"sqlite:///{db_path}",
        github_token=None,
        llm_base_url=None,
        llm_api_key=None,
        llm_model=None,
        app_timezone="Asia/Shanghai",
    )
    application = create_app(settings)
    with TestClient(application) as test_client:
        yield test_client
