from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import UUID4
from typing import Annotated
from fastapi import Query

from flowlog.dto.job_created_dto import JobResponseDto
from flowlog.dto.job_log_dto import JobLogResponseDto
from flowlog.services.job_service import (
    create_job,
    create_job_log,
    finish_job_by_id,
    get_logs_by_job_id,
)
from flowlog.shared.enums.log_enums import LogLevel
from flowlog.tags.job_tags import JOB_TAG
from flowlog.validators.job_finish_validator import JobFinishValidator
from flowlog.validators.job_log_validator import JobLogValidator
from flowlog.validators.job_register_validator import JobRegisterValidator

jobs_router = APIRouter(tags=[JOB_TAG], prefix="/jobs")


@jobs_router.post("/", status_code=201, response_model=JobResponseDto)
async def init_job(body: JobRegisterValidator):
    job = create_job(body)
    return job


@jobs_router.post("/{job_id}/logs", status_code=201, response_model=JobLogResponseDto)
async def insert_log(job_id: UUID4, body: JobLogValidator):
    job_log_data = create_job_log(job_id, body)
    return job_log_data


@jobs_router.patch("/{job_id}/finish", status_code=200)
async def finish_job(job_id: UUID4, body: JobFinishValidator):
    job_finish_data = finish_job_by_id(job_id, body)

    return job_finish_data


# async def read_item(item_id: str, q: str | None = None):


@jobs_router.get("/{job_id}/logs", status_code=200)
async def get_logs(
    job_id: UUID4,
    page: Annotated[int, Query(ge=1, le=200)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    level: LogLevel | None = None,
):

    return get_logs_by_job_id(job_id, page, page_size, search, level)
