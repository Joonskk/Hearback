import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.auth import CurrentUserDep
from app.db import SessionDep
from app.schemas import (
    ApplicationCreate,
    ApplicationDetail,
    ApplicationOut,
    ApplicationPage,
    ApplicationStatus,
    StatusChange,
)
from app.services import applications as service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    data: ApplicationCreate, user: CurrentUserDep, session: SessionDep
) -> ApplicationDetail:
    application = service.create_application(session, user, data)
    return ApplicationDetail.model_validate(application)


@router.get("")
def list_applications(
    user: CurrentUserDep,
    session: SessionDep,
    status: ApplicationStatus | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApplicationPage:
    items, next_cursor = service.list_applications(
        session, user, status=status, cursor=cursor, limit=limit
    )
    return ApplicationPage(
        items=[ApplicationOut.model_validate(application) for application in items],
        next_cursor=next_cursor,
    )


@router.get("/{application_id}")
def get_application(
    application_id: uuid.UUID, user: CurrentUserDep, session: SessionDep
) -> ApplicationDetail:
    application = service.get_application(session, user, application_id)
    return ApplicationDetail.model_validate(application)


@router.post("/{application_id}/status")
def change_status(
    application_id: uuid.UUID, data: StatusChange, user: CurrentUserDep, session: SessionDep
) -> ApplicationDetail:
    application = service.change_status(session, user, application_id, data)
    return ApplicationDetail.model_validate(application)
