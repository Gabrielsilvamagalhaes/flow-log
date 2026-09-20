from enum import StrEnum


class QueueState(StrEnum):
    FAILED = "failed"
    COMPLETED = "completed"
    DELAYED = "delayed"
    WAIT = "wait"
    PRIORITIZED = "prioritized"
