from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import Field, SQLModel

from flowlog.shared.enums.job_enums import Environment, JobStatus, Jobtypes


class Job(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_type: Jobtypes
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    status: JobStatus = Field(default=JobStatus.RUNNING)
    client_identifier: str = Field(min_length=3, max_length=50)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime]
    summary: Optional[str] = Field(default=None, max_length=500)
