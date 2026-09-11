from datetime import datetime
from typing import Optional
import uuid
from pydantic import ConfigDict
from sqlmodel import SQLModel

from flowlog.shared.enums.job_enums import Environment, JobStatus, Jobtypes


class JobServiceDto(SQLModel):
    id: uuid.UUID
    status: JobStatus
    started_at: datetime
    job_type: Jobtypes
    environment: Environment
    ended_at: Optional[datetime]
    summary: Optional[str]

    # Permite extrair dados a partir de atributos de objetos Python/ORM
    model_config = ConfigDict(from_attributes=True)
