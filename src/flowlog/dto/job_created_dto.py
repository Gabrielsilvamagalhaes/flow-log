from datetime import datetime
import uuid
from pydantic import ConfigDict
from sqlmodel import SQLModel

from flowlog.shared.enums.job_enums import JobStatus


class JobResponseDto(SQLModel):
    id: uuid.UUID
    status: JobStatus
    started_at: datetime

    # Permite extrair dados a partir de atributos de objetos Python/ORM
    model_config = ConfigDict(from_attributes=True)
