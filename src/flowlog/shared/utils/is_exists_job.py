from fastapi.exceptions import HTTPException
from flowlog.dto.job_created_dto import JobResponseDto


def is_exists_job(job_id: str, job: JobResponseDto | None) -> bool:
    if not job:
        raise HTTPException(status_code=404, detail=f"Job com o id: {job_id} não encontrado.")

    return True
