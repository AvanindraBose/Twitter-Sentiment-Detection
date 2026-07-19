import importlib

from backend.core import security


def test_token_expiry_defaults_when_environment_is_missing(monkeypatch):
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    monkeypatch.delenv("REFRESH_TOKEN_EXPIRE_DAYS", raising=False)

    reloaded = importlib.reload(security)

    assert reloaded.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert reloaded.REFRESH_TOKEN_EXPIRE_DAYS == 7


def test_token_expiry_defaults_when_environment_is_empty(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "")

    reloaded = importlib.reload(security)

    assert reloaded.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert reloaded.REFRESH_TOKEN_EXPIRE_DAYS == 7
