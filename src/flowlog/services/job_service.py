from fastapi.exceptions import HTTPException
from sqlmodel import Session, func, select
from flowlog.dto.job_finish_dto import JobFinishResponseDto
from flowlog.dto.job_log_dto import JobLogResponseDto
from flowlog.dto.job_service_dto import JobServiceDto
from flowlog.dto.response_job_logs_dto import JobLogsResponseDto
from flowlog.server.database.connection import engine
from flowlog.server.database.models.job_logs import JobLog
from flowlog.server.database.models.jobs import Job
from flowlog.shared.enums.log_enums import LogLevel
from flowlog.shared.utils.is_exists_job import is_exists_job
from flowlog.shared.utils.is_valid_finish_job_status import is_valid_finish_job_status
from flowlog.validators.job_finish_validator import JobFinishValidator
from flowlog.validators.job_log_validator import JobLogValidator
from flowlog.validators.job_register_validator import JobRegisterValidator


def create_job(job_register: JobRegisterValidator) -> Job:
    job_data = Job(
        client_identifier=job_register.client_identifier,
        job_type=job_register.job_type,
        environment=job_register.environment,
    )

    with Session(engine) as session:
        session.add(job_data)
        session.commit()
        session.refresh(job_data)
        return job_data


def create_job_log(job_id: str, job_log: JobLogValidator) -> JobLogResponseDto:
    finded_job = find_job_by_id(job_id=job_id)

    is_exists_job(job_id, finded_job)
    is_valid_status = is_valid_finish_job_status(finded_job.status)

    if is_valid_status:
        raise HTTPException(
            status_code=400,
            detail="Não é possivel inserir logs em um job já finalizado.",
        )

    job_log_data = JobLog(
        message=job_log.message,
        error_code=job_log.error_code,
        stack_trace=job_log.stack_trace,
        level=job_log.level,
        job_id=job_id,
        metadata_info=job_log.metadata,
    )

    with Session(engine) as session:
        session.add(job_log_data)
        session.commit()
        session.refresh(job_log_data)

        return job_log_data


def find_job_by_id(job_id: str) -> JobServiceDto | None:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job:
            # 2. Converte a entidade 'Job' para 'JobResponseDTO' usando o validation_alias
            job_dto = JobServiceDto.model_validate(job)

            return job_dto

        return None


def get_total_logs_by_job_id(
    session: Session, job_id: str, search: str | None = None, level: LogLevel | None = None
) -> int:
    statement = select(func.count()).select_from(JobLog).where(JobLog.job_id == job_id)

    if level is not None:
        statement = statement.where(JobLog.level == level)

    if search is not None:
        statement = statement.where(JobLog.message.icontains(search))

    total_logs = session.exec(statement).one()

    return total_logs


def get_logs_by_job_id(
    job_id: str, page: int, page_size: int, search: str | None, level: LogLevel | None = None
):
    finded_job = find_job_by_id(job_id=job_id)
    is_exists_job(job_id, finded_job)

    offset = (page - 1) * page_size

    with Session(engine) as session:
        statement = (
            select(JobLog)
            .order_by(JobLog.timestamp)
            .where(JobLog.job_id == job_id)
            .offset(offset)
            .limit(page_size)
        )

        if level is not None:
            statement = statement.where(JobLog.level == level)

        if search is not None:
            statement = statement.where(JobLog.message.icontains(search))

        results = session.exec(statement)
        job_logs = results.all()

        total_logs = get_total_logs_by_job_id(session, job_id=job_id, search=search, level=level)

        return JobLogsResponseDto.from_job_log_model(
            job_logs=job_logs, page=page, page_size=page_size, total=total_logs
        )


def finish_job_by_id(job_id: str, job_finish_data: JobFinishValidator) -> JobFinishResponseDto:

    with Session(engine) as session:
        job = session.get(Job, job_id)

        is_exists_job(job_id, job)
        is_valid_status = is_valid_finish_job_status(job.status)

        if is_valid_status:
            raise HTTPException(
                status_code=400,
                detail="Não é possivel alterar o STATUS de um job já finalizado.",
            )

        if job_finish_data.ended_at < job.started_at:
            raise HTTPException(
                status_code=400,
                detail="Data de finalização do Job não pode ser maior que a data de inicio.",
            )

        job.status = job_finish_data.final_status
        job.ended_at = job_finish_data.ended_at
        job.summary = job_finish_data.summary

        total_logs_count = get_total_logs_by_job_id(session, job.id)

        session.add(job)
        session.commit()
        session.refresh(job)

        return JobFinishResponseDto.from_model(job, total_logs_count=total_logs_count)
