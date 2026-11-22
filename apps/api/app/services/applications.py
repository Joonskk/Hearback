"""Database work for applications. Routers call these; they never build queries themselves."""

import base64
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import APIError
from app.models import Application, ApplicationEvent, Company, JobPosting, User
from app.schemas import ApplicationCreate, StatusChange
from app.state_machine import can_transition


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


def _encode_cursor(application: Application) -> str:
    """Application → opaque cursor string (base64 of "applied_at|id")."""
    raw = f"{application.applied_at.isoformat()}|{application.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Cursor string → (applied_at, id). Raises 422 if it's malformed."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        applied_at, application_id = raw.split("|")
        return datetime.fromisoformat(applied_at), uuid.UUID(application_id)
    except ValueError as exc:
        raise APIError(422, "invalid_cursor", "Invalid cursor") from exc


def list_applications(
    session: Session,
    user: User,
    *,
    status: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Application], str | None]:
    query = (
        select(Application)
        .where(Application.user_id == user.id)
        .options(selectinload(Application.job_posting).selectinload(JobPosting.company))
        .order_by(Application.applied_at.desc(), Application.id.desc())
        .limit(limit + 1)
    )
    if status is not None:
        query = query.where(Application.status == status)
    if cursor is not None:
        applied_at, last_id = _decode_cursor(cursor)
        query = query.where(
            tuple_(Application.applied_at, Application.id) < tuple_(applied_at, last_id)
        )

    rows = list(session.scalars(query))
    items = rows[:limit]
    next_cursor = _encode_cursor(items[-1]) if len(rows) > limit else None
    return items, next_cursor
