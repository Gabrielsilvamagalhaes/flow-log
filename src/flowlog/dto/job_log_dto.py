from datetime import datetime
import uuid
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field

from flowlog.server.database.models.job_logs import JobLog
from flowlog.shared.enums.log_enums import LogLevel


class JobLogResponseDto(SQLModel):
    log_id: uuid.UUID = Field(validation_alias="id")
    job_id: uuid.UUID
    level: LogLevel
    message: str
    created_at: datetime = Field(validation_alias="timestamp")

    # Configuração necessária para converter objetos ORM/SQLModel automaticamente
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
