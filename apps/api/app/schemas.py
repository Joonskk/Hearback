import uuid
from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None
    created_at: datetime


JobSource = Literal["greenhouse", "lever", "ashby", "workday", "manual", "other"]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    url: str | None = Field(default=None, max_length=2000)
    source: JobSource = "manual"
    applied_at: datetime | None = None
    notes: str | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    from_status: str | None
    to_status: str | None
    source: str
    occurred_at: datetime
    details: dict


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    company_name: str = Field(validation_alias=AliasPath("job_posting", "company", "name"))
    title: str = Field(validation_alias=AliasPath("job_posting", "title"))
    url: str | None = Field(validation_alias=AliasPath("job_posting", "url"))
    source: str = Field(validation_alias=AliasPath("job_posting", "source"))
    applied_at: datetime
    last_event_at: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationDetail(ApplicationOut):
    events: list[EventOut]


ApplicationStatus = Literal["applied", "assessment", "interview", "offer", "rejected", "stale"]


class StatusChange(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    to_status: ApplicationStatus
    note: str | None = Field(default=None, max_length=2000)
