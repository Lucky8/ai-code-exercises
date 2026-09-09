from fastapi.testclient import TestClient

import todo_api
from todo_api import app


client = TestClient(app)


def setup_function():
    todo_api.todo_items.clear()
    todo_api.next_todo_id = 1


def test_create_and_list_todo_items():
    response = client.post(
        "/todos",
        json={
            "title": "Learn FastAPI",
            "description": "Build a small API",
            "due_date": "2026-09-30",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"

    list_response = client.get("/todos?status=pending")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["title"] == "Learn FastAPI"


def test_validation_rejects_missing_or_invalid_fields():
    response = client.post(
        "/todos",
        json={"title": "", "due_date": "not-a-date"},
    )

    assert response.status_code == 422
    assert len(response.json()["detail"]) == 2


def test_complete_and_filter_todo_items():
    create_response = client.post(
        "/todos",
        json={"title": "Finish tests", "due_date": "2026-10-01"},
    )
    todo_id = create_response.json()["id"]

    complete_response = client.patch(f"/todos/{todo_id}/complete")

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert client.get("/todos?status=completed").json()[0]["id"] == todo_id
    assert client.get("/todos?status=pending").json() == []


def test_delete_todo_item():
    create_response = client.post(
        "/todos",
        json={"title": "Remove me", "due_date": "2026-11-01"},
    )
    todo_id = create_response.json()["id"]

    delete_response = client.delete(f"/todos/{todo_id}")

    assert delete_response.status_code == 204
    assert client.get("/todos").json() == []


def test_missing_todo_returns_not_found():
    response = client.patch("/todos/999/complete")

    assert response.status_code == 404
    assert response.json() == {"detail": "To-do item 999 was not found"}


def test_openapi_documents_the_api():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/todos" in response.json()["paths"]
    assert "/todos/{todo_id}/complete" in response.json()["paths"]
