import uuid

from backend.api import routes_predict


async def test_predict_redirects_when_user_is_not_authenticated(integration_async_client):
    response = await integration_async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 401


async def test_authenticated_predict_flow(integration_async_client, monkeypatch):
    email = f"{uuid.uuid4()}@example.com"
    password = "ValidPass1!"

    await integration_async_client.post(
        "/auth/signup",
        data={"username": "tester", "email": email, "password": password},
    )
    await integration_async_client.post(
        "/auth/login",
        data={"email": email, "password": password},
    )

    async def fake_predict_sentiment(_payload):
        return {"prediction": 1}

    monkeypatch.setattr(routes_predict, "predict_sentiment", fake_predict_sentiment)

    response = await integration_async_client.post("/predict", data={"text": "hello world"})

    assert response.status_code == 200
    assert "Positive" in response.text
