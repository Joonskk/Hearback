import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, ApplicationEvent, Company, JobPosting, Resume, User


def make_user(db: Session, email: str = "joon@example.com", google_sub: str = "sub-1") -> User:
    user = User(google_sub=google_sub, email=email)
    db.add(user)
    db.flush()
    return user


def make_posting(db: Session) -> JobPosting:
    company = Company(name="Stripe")
    db.add(company)
    db.flush()
    posting = JobPosting(company_id=company.id, title="SWE Intern")
    db.add(posting)
    db.flush()
    return posting


def test_new_application_defaults_to_applied(db: Session) -> None:
    application = Application(user_id=make_user(db).id, job_posting_id=make_posting(db).id)
    db.add(application)
    db.flush()
    db.refresh(application)

    assert application.status == "applied"


def test_invalid_status_is_rejected(db: Session) -> None:
    db.add(
        Application(user_id=make_user(db).id, job_posting_id=make_posting(db).id, status="banana")
    )

    with pytest.raises(IntegrityError, match="ck_applications_status_valid"):
        db.flush()


def test_email_is_unique_ignoring_case(db: Session) -> None:
    make_user(db, email="joon@example.com", google_sub="sub-1")
    db.add(User(google_sub="sub-2", email="JOON@example.com"))

    with pytest.raises(IntegrityError, match="uq_users_email_lower"):
        db.flush()


def test_same_user_cannot_apply_to_same_posting_twice(db: Session) -> None:
    user = make_user(db)
    posting = make_posting(db)
    db.add(Application(user_id=user.id, job_posting_id=posting.id))
    db.flush()
    db.add(Application(user_id=user.id, job_posting_id=posting.id))

    with pytest.raises(IntegrityError, match="uq_applications_user_id_job_posting_id"):
        db.flush()


def test_deleting_user_deletes_their_data(db: Session) -> None:
    user = make_user(db)
    application = Application(user_id=user.id, job_posting_id=make_posting(db).id)
    db.add(application)
    db.flush()
    db.add(ApplicationEvent(application_id=application.id, type="created", source="manual"))
    db.add(
        Resume(
            user_id=user.id,
            version=1,
            s3_key="resumes/test/v1.pdf",
            filename="resume.pdf",
            content_type="application/pdf",
            size_bytes=1024,
        )
    )
    db.flush()

    db.delete(user)
    db.flush()

    for model in (Application, ApplicationEvent, Resume):
        assert db.scalar(select(func.count()).select_from(model)) == 0
