"""Database work for applications. Routers call these; they never build queries themselves."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import APIError
from app.models import Application, ApplicationEvent, Company, JobPosting, User
from app.schemas import ApplicationCreate


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


def get_application(session: Session, user: User, application_id: uuid.UUID) -> Application:
    application = session.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    if application is None:
        raise APIError(404, "not_found", "Application not found")
    return application
