from flowlog.shared.enums.job_enums import FinishJobStatus


def is_valid_finish_job_status(value) -> bool:
    finish_job_status_values = [status.value for status in FinishJobStatus]

    return value in finish_job_status_values
