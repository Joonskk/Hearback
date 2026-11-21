"""Database work for applications. Routers call these; they never build queries themselves."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import APIError
from app.models import Application, ApplicationEvent, Company, JobPosting, User
from app.schemas import ApplicationCreate, StatusChange
from app.state_machine import can_transition

from datetime import UTC, datetime


def _find_or_create_company(session: Session, name: str) -> Company:
    company = session.scalar(select(Company).where(func.lower(Company.name) == name.lower()))
    if company is None:
        company = Company(name=name)
        session.add(company)
    return company


def _find_or_create_posting(session: Session, data: ApplicationCreate) -> JobPosting:
    if data.url is not None:
        posting = session.scalar(select(JobPosting).where(JobPosting.url == data.url))
        if posting is not None:
            return posting
    company = _find_or_create_company(session, data.company_name)
    posting = JobPosting(company=company, title=data.title, url=data.url, source=data.source)
    session.add(posting)
    return posting


def create_application(session: Session, user: User, data: ApplicationCreate) -> Application:
    posting = _find_or_create_posting(session, data)
    application = Application(user_id=user.id, job_posting=posting, notes=data.notes)
    if data.applied_at is not None:
        application.applied_at = data.applied_at
    application.events.append(
        ApplicationEvent(type="created", to_status="applied", source="manual")
    )
    session.add(application)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise APIError(409, "duplicate_application", "You already logged this job") from exc
    return application


def get_application(
    session: Session, user: User, application_id: uuid.UUID, *, for_update: bool = False
) -> Application:
    query = select(Application).where(
        Application.id == application_id,
        Application.user_id == user.id,
    )
    if for_update:
        query = query.with_for_update()
    application = session.scalar(query)
    if application is None:
        raise APIError(404, "not_found", "Application not found")
    return application


def change_status(
    session: Session, user: User, application_id: uuid.UUID, data: StatusChange
) -> Application:
    application = get_application(session, user, application_id, for_update=True)

    result = can_transition(application.status, data.to_status, source="manual")
    if not result.allowed:
        raise APIError(
            409,
            "invalid_transition",
            f"Can't move from {application.status} to {data.to_status}",
        )

    details: dict = {}
    if result.correction:
        details["correction"] = True
    if data.note:
        details["note"] = data.note

    now = datetime.now(UTC)
    application.events.append(
        ApplicationEvent(
            type="status_changed",
            from_status=application.status,
            to_status=data.to_status,
            source="manual",
            occurred_at=now,
            details=details,
        )
    )
    application.status = data.to_status
    application.last_event_at = now
    application.updated_at = now
    session.commit()
    session.refresh(application)
    return application
