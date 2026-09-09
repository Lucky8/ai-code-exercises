from datetime import datetime, timedelta, timezone
import os
import sqlite3

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-this-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_PATH = os.getenv("AUTH_DATABASE_PATH", "auth_api.db")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    full_name: str
    is_admin: bool = False


class UserInStore(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class AuditLog(BaseModel):
    id: int
    username: str
    action: str
    timestamp: str


# In production, replace the in-memory users store with a database as well.
users = {
    "alice": UserInStore(
        username="alice",
        full_name="Alice Example",
        is_admin=True,
        hashed_password=password_context.hash("secret123"),
    )
}


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.commit()


def log_action(username: str, action: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO audit_logs (username, action, timestamp) VALUES (?, ?, ?)",
            (username, action, timestamp),
        )
        connection.commit()


init_db()
app = FastAPI(title="JWT Authentication API")


def authenticate_user(username: str, password: str) -> UserInStore | None:
    user = users.get(username)
    if user is None or not password_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": username, "exp": expires_at},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_error from None

    username = payload.get("sub")
    if not isinstance(username, str):
        raise credentials_error

    user = users.get(username)
    if user is None:
        raise credentials_error
    return User(
        username=user.username,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        log_action(form_data.username, "LOGIN_FAILURE")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_action(user.username, "LOGIN_SUCCESS")
    return Token(
        access_token=create_access_token(user.username),
        token_type="bearer",
    )


@app.get("/users/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.post("/admin/actions")
async def perform_admin_action(
    current_user: User = Depends(require_admin),
) -> dict[str, str]:
    log_action(current_user.username, "ADMIN_ACTION")
    return {"message": "Admin action completed"}


@app.get("/admin/logs", response_model=list[AuditLog])
async def read_audit_logs(
    current_user: User = Depends(require_admin),
) -> list[AuditLog]:
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT id, username, action, timestamp "
            "FROM audit_logs ORDER BY id"
        ).fetchall()

    return [AuditLog(**dict(row)) for row in rows]
