from datetime import datetime, timedelta, timezone
import os

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-this-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    full_name: str


class UserInStore(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# In production, replace this with a database and a strong secret from configuration.
users = {
    "alice": UserInStore(
        username="alice",
        full_name="Alice Example",
        hashed_password=password_context.hash("secret123"),
    )
}

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
    return User(username=user.username, full_name=user.full_name)


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=create_access_token(user.username),
        token_type="bearer",
    )


@app.get("/users/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
