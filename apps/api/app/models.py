"""SQLAlchemy ORM models: one class per table (design doc 6.2)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Allowed values live in Python so the API, the state machine and the CHECK
# constraints all share one list.
APPLICATION_STATUSES = ("applied", "assessment", "interview", "offer", "rejected", "stale")
EVENT_SOURCES = ("manual", "extension", "email", "system")
EVENT_TYPES = ("created", "status_changed", "note")
JOB_SOURCES = ("greenhouse", "lever", "ashby", "workday", "manual", "other")
PARSE_STATUSES = ("pending", "parsed", "failed")


def _in_list(column: str, values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"


class Base(DeclarativeBase):
    # Predictable constraint names make migrations reviewable and reversible.
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    google_sub: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(320))
    name: Mapped[str | None] = mapped_column(String(200))
    settings: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        # Case-insensitive uniqueness: Foo@x.com and foo@x.com are one user.
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    domains: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    size: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (Index("uq_companies_name_lower", func.lower(name), unique=True),)


class JobPosting(TimestampMixin, Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = _uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), server_default="manual")
    description: Mapped[str | None] = mapped_column(Text)
    company: Mapped[Company] = relationship()

    __table_args__ = (
        CheckConstraint(_in_list("source", JOB_SOURCES), name="source_valid"),
        Index("uq_job_postings_url", "url", unique=True, postgresql_where=text("url IS NOT NULL")),
    )


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_postings.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), server_default="applied")
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    job_posting: Mapped[JobPosting] = relationship()
    events: Mapped[list["ApplicationEvent"]] = relationship(
        order_by="ApplicationEvent.occurred_at.desc()",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(_in_list("status", APPLICATION_STATUSES), name="status_valid"),
        # One application per user per posting.
        UniqueConstraint("user_id", "job_posting_id"),
        # Matches the dashboard query: "my applications, newest first".
        Index("ix_applications_user_applied_at", "user_id", applied_at.desc()),
        # Matches the daily stale scan: "applied, no event for 30 days".
        Index("ix_applications_status_last_event_at", "status", "last_event_at"),
    )


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(String(20))
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(20))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    details: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint(_in_list("type", EVENT_TYPES), name="type_valid"),
        CheckConstraint(_in_list("source", EVENT_SOURCES), name="source_valid"),
        Index("ix_application_events_app_occurred", "application_id", "occurred_at"),
    )


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    s3_key: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    parse_status: Mapped[str] = mapped_column(String(20), server_default="pending")
    parsed_profile: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(_in_list("parse_status", PARSE_STATUSES), name="parse_status_valid"),
        UniqueConstraint("user_id", "version"),
    )
