import math
from typing import List, Sequence
from sqlmodel import SQLModel

from flowlog.dto.job_log_dto import JobLogResponseDto
from flowlog.server.database.models.job_logs import JobLog


class JobLogsResponseDto(SQLModel):
    items: List[JobLogResponseDto]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def from_job_log_model(
        cls, job_logs: Sequence[JobLog], page: int, page_size: int, total: int
    ) -> "JobLogsResponseDto":
        total_pages = cls.calculate_total_pages(total, page_size)
        items: list[JobLogResponseDto] = [JobLogResponseDto.model_validate(log) for log in job_logs]

        print(items)

        return cls(
            page=page, page_size=page_size, total=total, total_pages=total_pages, items=items
        )

    @classmethod
    def calculate_total_pages(cls, total: int, page_size: int) -> int:
        return math.ceil(total / page_size)
