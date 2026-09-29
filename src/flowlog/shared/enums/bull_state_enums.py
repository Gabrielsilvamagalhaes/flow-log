from enum import StrEnum


class BullState(StrEnum):
    WAIT = "wait"
    ACTIVE = "active"
    DELAYED = "delayed"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
