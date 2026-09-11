from datetime import datetime
from typing import Any, Optional
import uuid

from sqlmodel import JSON, Column, Field, SQLModel

from flowlog.shared.enums.log_enums import LogLevel


class JobLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message: str = Field(..., max_length=2000, min_length=5)
    level: LogLevel
    timestamp: datetime = Field(default_factory=datetime.now)

    stack_trace: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)
    # sa_column=Column(JSON): Instrui o banco de dados (PostgreSQL, SQLite, MySQL) a criar a coluna no formato JSON nativo (ex: JSONB ou JSON).
    metadata_info: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    job_id: uuid.UUID = Field(..., foreign_key="job.id")
