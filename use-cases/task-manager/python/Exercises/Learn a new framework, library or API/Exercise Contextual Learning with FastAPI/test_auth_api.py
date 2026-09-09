from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import auth_api
from auth_api import app


client = TestClient(app)


def test_login_returns_bearer_token():
    response = client.post(
        "/token",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_protected_endpoint_accepts_valid_token():
    login_response = client.post(
        "/token",
        data={"username": "alice", "password": "secret123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "full_name": "Alice Example",
    }


def test_login_rejects_invalid_password():
    response = client.post(
        "/token",
        data={"username": "alice", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_protected_endpoint_requires_token():
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_token_is_rejected():
    expired_token = auth_api.jwt.encode(
        {
            "sub": "alice",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        auth_api.SECRET_KEY,
        algorithm=auth_api.ALGORITHM,
    )

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
