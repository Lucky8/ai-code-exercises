from datetime import date
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    due_date: date


class TodoResponse(TodoCreate):
    id: int
    status: TodoStatus


app = FastAPI(
    title="Todo API",
    description="A simple in-memory API for managing a to-do list.",
    version="1.0.0",
)

# This deliberately uses in-memory storage so the example can run without a database.
todo_items: dict[int, TodoResponse] = {}
next_todo_id = 1


@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate) -> TodoResponse:
    global next_todo_id

    created_todo = TodoResponse(
        id=next_todo_id,
        title=todo.title,
        description=todo.description,
        due_date=todo.due_date,
        status=TodoStatus.PENDING,
    )
    todo_items[next_todo_id] = created_todo
    next_todo_id += 1
    return created_todo


@app.get("/todos", response_model=list[TodoResponse])
async def list_todos(
    todo_status: TodoStatus | None = Query(default=None, alias="status"),
) -> list[TodoResponse]:
    if todo_status is None:
        return list(todo_items.values())

    return [todo for todo in todo_items.values() if todo.status == todo_status]


@app.patch("/todos/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: int) -> TodoResponse:
    todo = todo_items.get(todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"To-do item {todo_id} was not found",
        )

    completed_todo = todo.model_copy(update={"status": TodoStatus.COMPLETED})
    todo_items[todo_id] = completed_todo
    return completed_todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int) -> None:
    if todo_id not in todo_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"To-do item {todo_id} was not found",
        )

    del todo_items[todo_id]
