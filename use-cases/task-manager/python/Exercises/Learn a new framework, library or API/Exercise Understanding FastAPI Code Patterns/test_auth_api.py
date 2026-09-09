import os
import tempfile

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["AUTH_DATABASE_PATH"] = _db_file.name

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import auth_api
from auth_api import app


client = TestClient(app)


def clear_logs():
    with auth_api.get_db_connection() as connection:
        connection.execute("DELETE FROM audit_logs")
        connection.commit()


def test_login_returns_bearer_token():
    clear_logs()
    response = client.post(
        "/token",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_successful_login_is_logged():
    clear_logs()
    response = client.post(
        "/token",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    logs = client.get(
        "/admin/logs",
        headers={
            "Authorization": f"Bearer {response.json()['access_token']}"
        },
    )

    assert logs.status_code == 200
    assert logs.json()[0]["username"] == "alice"
    assert logs.json()[0]["action"] == "LOGIN_SUCCESS"


def test_protected_endpoint_accepts_valid_token():
    clear_logs()
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
        "is_admin": True,
    }


def test_login_rejects_invalid_password_and_logs_failure():
    clear_logs()
    response = client.post(
        "/token",
        data={"username": "alice", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

    with auth_api.get_db_connection() as connection:
        row = connection.execute(
            "SELECT username, action FROM audit_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert dict(row) == {"username": "alice", "action": "LOGIN_FAILURE"}


def test_protected_endpoint_requires_token():
    clear_logs()
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_token_is_rejected():
    clear_logs()
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


def test_admin_action_is_logged():
    clear_logs()
    login_response = client.post(
        "/token",
        data={"username": "alice", "password": "secret123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/admin/actions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with auth_api.get_db_connection() as connection:
        row = connection.execute(
            "SELECT username, action FROM audit_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert dict(row) == {"username": "alice", "action": "ADMIN_ACTION"}
