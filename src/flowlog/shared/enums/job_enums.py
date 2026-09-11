from enum import Enum, auto


class Jobtypes(str, Enum):
    ETL = "ETL"
    EXPORT = "EXPORT"
    NOTIFICATION = "NOTIFICATION"
    CLEANUP = "CLEANUP"


class JobStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FinishJobStatus(str, Enum):
    SUCCESS = JobStatus.SUCCESS.value
    FAILED = JobStatus.FAILED.value
    CANCELLED = JobStatus.CANCELLED.value


class Environment(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
