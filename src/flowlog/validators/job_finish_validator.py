from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from flowlog.shared.enums.job_enums import JobStatus


class JobFinishValidator(BaseModel):
    final_status: Literal[
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.SUCCESS,
    ]
    summary: Optional[str] = Field(default=None, max_length=500)
    ended_at: datetime = Field(default_factory=datetime.now)
