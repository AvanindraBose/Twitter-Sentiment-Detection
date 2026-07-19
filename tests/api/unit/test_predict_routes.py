from fastapi import HTTPException, status

from backend.api import routes_predict


async def test_predict_redirects_to_login_when_session_missing(async_client, unit_app):
    async def override_predict_rate_limiter():
        return None

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter

    def fake_get_current_user(_request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_access_token")

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(routes_predict, "get_current_user", fake_get_current_user)

    response = await async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login?session=expired"
    monkeypatch.undo()


async def test_predict_redirects_to_refresh_when_access_token_expired(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return None

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter

    def fake_get_current_user(_request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="expired")

    monkeypatch.setattr(routes_predict, "get_current_user", fake_get_current_user)
    async_client.cookies.set("refresh_token", "refresh-cookie")

    response = await async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/refresh?next=/dashboard"


async def test_predict_returns_dashboard_message_when_rate_limited(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return "rate_limited"

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter
    monkeypatch.setattr(routes_predict, "get_current_user", lambda _request: "user-123")

    response = await async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 200
    assert "Experiencing heavy traffic" in response.text


async def test_predict_returns_dashboard_message_when_redis_unavailable(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return "redis_unavailable"

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter
    monkeypatch.setattr(routes_predict, "get_current_user", lambda _request: "user-123")

    response = await async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 200
    assert "Service temporarily unavailable" in response.text


async def test_predict_renders_result_on_success(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return None

    async def fake_predict_sentiment(_payload):
        return {"prediction": 1}

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter
    monkeypatch.setattr(routes_predict, "get_current_user", lambda _request: "user-123")
    monkeypatch.setattr(routes_predict, "predict_sentiment", fake_predict_sentiment)

    response = await async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 200
    assert "Positive" in response.text


async def test_xquik_batch_predicts_supported_text_columns(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return None

    async def fake_predict_sentiment(_payload):
        return {"prediction": 1}

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter
    monkeypatch.setattr(routes_predict, "get_current_user", lambda _request: "user-123")
    monkeypatch.setattr(routes_predict, "predict_sentiment", fake_predict_sentiment)

    response = await async_client.post(
        "/api/predict/xquik",
        json={
            "tweets": [
                {"tweet_id": "174", "tweet_text": "Markets like this product update."},
                {"id": "175", "content": "Second export row."},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "predictions": [
            {"index": 0, "source_id": "174", "sentiment": 1},
            {"index": 1, "source_id": "175", "sentiment": 1},
        ]
    }


async def test_xquik_batch_rejects_rows_without_text(async_client, unit_app, monkeypatch):
    async def override_predict_rate_limiter():
        return None

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter
    monkeypatch.setattr(routes_predict, "get_current_user", lambda _request: "user-123")

    response = await async_client.post(
        "/api/predict/xquik",
        json={"tweets": [{"tweet_id": "174"}]},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "No readable tweet text found in Xquik rows."


async def test_xquik_batch_requires_authentication(async_client):
    response = await async_client.post(
        "/api/predict/xquik",
        json={"tweets": [{"tweet_text": "A valid row."}]},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "missing_access_token"


async def test_xquik_batch_limits_request_size(async_client, unit_app):
    async def override_predict_rate_limiter():
        return None

    unit_app.dependency_overrides[routes_predict.predict_rate_limiter] = override_predict_rate_limiter

    response = await async_client.post(
        "/api/predict/xquik",
        json={"tweets": [{"tweet_text": "A valid row."}] * 101},
    )

    assert response.status_code == 422
