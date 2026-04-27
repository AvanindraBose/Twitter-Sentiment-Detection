from fastapi import HTTPException, status

from backend.api import routes_root


async def test_root_returns_landing_page_when_logged_out(async_client, monkeypatch):
    def fake_get_current_user(_request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_access_token")

    monkeypatch.setattr(routes_root, "get_current_user", fake_get_current_user)

    response = await async_client.get("/")

    assert response.status_code == 200
    assert "Understand the emotion behind social chatter" in response.text


async def test_root_redirects_authenticated_user_to_dashboard(async_client, monkeypatch):
    monkeypatch.setattr(routes_root, "get_current_user", lambda _request: "user-123")

    response = await async_client.get("/")

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


async def test_dashboard_redirects_to_login_when_session_missing(async_client, monkeypatch):
    def fake_get_current_user(_request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_access_token")

    monkeypatch.setattr(routes_root, "get_current_user", fake_get_current_user)

    response = await async_client.get("/dashboard")

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login?session=expired"


async def test_dashboard_redirects_to_refresh_when_access_token_expired(async_client, monkeypatch):
    def fake_get_current_user(_request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="expired")

    monkeypatch.setattr(routes_root, "get_current_user", fake_get_current_user)
    async_client.cookies.set("refresh_token", "refresh-cookie")

    response = await async_client.get("/dashboard")

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/refresh?next=/dashboard"


async def test_dashboard_renders_for_authenticated_user(async_client, monkeypatch):
    monkeypatch.setattr(routes_root, "get_current_user", lambda _request: "user-123")

    response = await async_client.get("/dashboard")

    assert response.status_code == 200
    assert "Analyze sentiment" in response.text
