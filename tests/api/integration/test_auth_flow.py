import uuid


async def test_signup_login_dashboard_logout_flow(integration_async_client):
    email = f"{uuid.uuid4()}@example.com"
    password = "ValidPass1!"

    signup_response = await integration_async_client.post(
        "/auth/signup",
        data={"username": "tester", "email": email, "password": password},
    )

    assert signup_response.status_code == 303
    assert signup_response.headers["location"] == "/auth/login?signup=success"

    login_response = await integration_async_client.post(
        "/auth/login",
        data={"email": email, "password": password},
    )

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/dashboard"

    dashboard_response = await integration_async_client.get("/dashboard")
    assert dashboard_response.status_code == 200
    assert "Analyze sentiment" in dashboard_response.text

    logout_response = await integration_async_client.post("/auth/logout")
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/?logout=success"


async def test_refresh_flow_redirects_back_to_dashboard(integration_async_client):
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

    refresh_response = await integration_async_client.get("/auth/refresh?next=/dashboard")

    assert refresh_response.status_code == 303
    assert refresh_response.headers["location"] == "/dashboard"
