from typing import Annotated, Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.config import settings
from app.db import SessionDep
from app.errors import APIError
from app.models import User


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            options={"require": ["sub", "email", "exp", "aud"]},
        )
    except jwt.InvalidTokenError as exc:
        raise APIError(401, "invalid_token", "Missing or invalid token") from exc


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise APIError(401, "invalid_token", "Missing or invalid token")
    claims = decode_token(credentials.credentials)

    user = session.scalar(select(User).where(User.google_sub == claims["sub"]))
    if user is None:
        user = User(
            google_sub=claims["sub"],
            email=claims["email"],
            name=claims.get("name"),
        )
        session.add(user)
        session.commit()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
