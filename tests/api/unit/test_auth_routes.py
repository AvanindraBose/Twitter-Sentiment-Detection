from datetime import datetime, timezone
from types import SimpleNamespace

from backend.api import routes_auth


async def test_signup_page_loads(async_client):
    response = await async_client.get("/auth/signup")

    assert response.status_code == 200
    assert "Create account" in response.text


async def test_login_page_loads(async_client):
    response = await async_client.get("/auth/login")

    assert response.status_code == 200
    assert "Sign in" in response.text


async def test_login_page_shows_session_message(async_client):
    response = await async_client.get("/auth/login?session=expired")

    assert response.status_code == 200
    assert "Your session expired. Please log in again." in response.text


async def test_signup_rejects_existing_email(async_client, fake_db, monkeypatch):
    existing_user = SimpleNamespace(email="taken@example.com")
    fake_db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: existing_user)
    monkeypatch.setattr(routes_auth, "run_in_threadpool", _unused_threadpool)

    response = await async_client.post(
        "/auth/signup",
        data={"username": "tester", "email": "taken@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 400
    assert "Email already exists" in response.text


async def test_signup_redirects_after_success(async_client, fake_db, monkeypatch):
    fake_db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    async def fake_threadpool(func, *args):
        if func is routes_auth.hash_password:
            return "hashed-password"
        return func(*args)

    monkeypatch.setattr(routes_auth, "run_in_threadpool", fake_threadpool)

    response = await async_client.post(
        "/auth/signup",
        data={"username": "tester", "email": "new@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login?signup=success"
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()


async def test_login_returns_rate_limit_message(async_client, unit_app):
    async def override_login_rate_limiter():
        return "rate_limited"

    unit_app.dependency_overrides[routes_auth.login_rate_limiter] = override_login_rate_limiter

    response = await async_client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 429
    assert "Too many login attempts" in response.text


async def test_login_returns_service_unavailable_message(async_client, unit_app):
    async def override_login_rate_limiter():
        return "redis_unavailable"

    unit_app.dependency_overrides[routes_auth.login_rate_limiter] = override_login_rate_limiter

    response = await async_client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 503
    assert "Service temporarily unavailable" in response.text


async def test_login_rejects_invalid_credentials(async_client, fake_db, monkeypatch):
    fake_db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    monkeypatch.setattr(routes_auth, "run_in_threadpool", _unused_threadpool)

    response = await async_client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.text


async def test_login_redirects_after_success(async_client, fake_db, monkeypatch):
    db_user = SimpleNamespace(id="user-1", password_hash="stored-hash")
    fake_db.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda: db_user),
        SimpleNamespace(scalar_one_or_none=lambda: None),
    ]

    async def fake_threadpool(func, *args):
        if func is routes_auth.verify_password:
            return True
        if func is routes_auth.hash_refresh_token:
            return "hashed-refresh-token"
        return func(*args)

    monkeypatch.setattr(routes_auth, "run_in_threadpool", fake_threadpool)
    monkeypatch.setattr(routes_auth, "create_access_tokens", lambda _user_id: "access-token")
    monkeypatch.setattr(
        routes_auth,
        "create_refresh_tokens",
        lambda _user_id: ("refresh-token", datetime.now(timezone.utc)),
    )

    response = await async_client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token=" in response.headers.get("set-cookie", "")


async def test_refresh_redirects_when_limited(async_client, unit_app):
    async def override_refresh_rate_limiter():
        return "rate_limited"

    unit_app.dependency_overrides[routes_auth.refresh_rate_limiter] = override_refresh_rate_limiter

    response = await async_client.get("/auth/refresh")

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login?refresh=rate_limited"


async def test_refresh_redirects_when_redis_unavailable(async_client, unit_app):
    async def override_refresh_rate_limiter():
        return "redis_unavailable"

    unit_app.dependency_overrides[routes_auth.refresh_rate_limiter] = override_refresh_rate_limiter

    response = await async_client.get("/auth/refresh")

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login?refresh=service_unavailable"


async def test_logout_redirects_to_landing(async_client):
    response = await async_client.post("/auth/logout")

    assert response.status_code == 303
    assert response.headers["location"] == "/?logout=success"


async def _unused_threadpool(func, *args):
    return func(*args)
