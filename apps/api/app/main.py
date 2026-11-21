from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.auth import CurrentUserDep
from app.db import SessionDep
from app.errors import APIError, api_error_handler, validation_error_handler
from app.routers import applications
from app.schemas import UserOut

app = FastAPI(title="Hearback API", version="0.1.0")

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(applications.router)


@app.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/me")
def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)
