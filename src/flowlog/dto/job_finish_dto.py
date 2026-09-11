from datetime import datetime
import uuid
from sqlmodel import SQLModel

from flowlog.server.database.models.jobs import Job
from flowlog.shared.enums.job_enums import JobStatus


class JobFinishResponseDto(SQLModel):
    job_id: uuid.UUID
    status: JobStatus
    duration_seconds: float
    total_logs_count: int
    tags: list[str]

    @classmethod
    def from_model(cls, job: Job, total_logs_count: int) -> "JobFinishResponseDto":
        """Monta o JobFinishResponseDto a partir do Job model"""
        durantion_seconds = cls.calculate_duration(job.started_at, job.ended_at)

        tags: list[str] = []

        if durantion_seconds < 1 and job.status == JobStatus.SUCCESS:
            tags.extend(["FAST_EXECUTION", "SUCCESS_EXECUTION"])
        elif job.status == JobStatus.SUCCESS:
            tags.append("SUCCESS_EXECUTION")

        return cls(
            job_id=job.id,
            status=job.status,
            duration_seconds=durantion_seconds,
            tags=tags,
            total_logs_count=total_logs_count,
        )

    @classmethod
    def calculate_duration(cls, started_at: datetime, ended_at: datetime) -> float:
        """Metodo que calcula a duração do job"""
        return (ended_at - started_at).total_seconds()
