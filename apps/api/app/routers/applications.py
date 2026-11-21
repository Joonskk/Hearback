import uuid

from fastapi import APIRouter, status

from app.auth import CurrentUserDep
from app.db import SessionDep
from app.schemas import ApplicationCreate, ApplicationDetail
from app.services import applications as service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    data: ApplicationCreate, user: CurrentUserDep, session: SessionDep
) -> ApplicationDetail:
    application = service.create_application(session, user, data)
    return ApplicationDetail.model_validate(application)


@router.get("/{application_id}")
def get_application(
    application_id: uuid.UUID, user: CurrentUserDep, session: SessionDep
) -> ApplicationDetail:
    application = service.get_application(session, user, application_id)
    return ApplicationDetail.model_validate(application)
