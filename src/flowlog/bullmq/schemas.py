import json
from datetime import UTC, datetime, timedelta

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    computed_field,
    field_validator,
)
from typing_extensions import Any, Literal, NotRequired, TypedDict

from flowlog.shared.enums.bull_state_enums import BullState


class BullQueue(BaseModel):
    name: str
    prefix: str
    paused: bool
    count_completed: int
    count_wait: int
    count_failed: int
    count_active: int
    count_delayed: int
    count_paused: int


class BackoffOptions(TypedDict):
    type: Literal["exponential", "fixed"]
    delay: NotRequired[int]


class KeepJobsOptions(TypedDict):
    age: int
    count: NotRequired[int | None]
    limit: NotRequired[int | None]


class BullJobOpts(TypedDict):
    attempts: int
    backoff: NotRequired[BackoffOptions | int | None]
    jobId: NotRequired[str]
    removeOnComplete: NotRequired[int | bool | KeepJobsOptions | None]
    delay: NotRequired[int]
    priority: int  # default 0 (0 a 10)


class BullJob(BaseModel):
    state: BullState
    opts: BullJobOpts
    name: str = Field(default="unknown")
    timestamp: datetime

    stack_trace: list[str] = Field(
        default=[],
        validation_alias="stacktrace",
    )  # array JSON, default []
    return_value: Any | None = Field(
        default=None, validation_alias="returnvalue", validate_default=True
    )
    attempts_made: int = Field(default=0, validation_alias="atm")
    processed_on: datetime | None = Field(
        default=None, validation_alias="processedOn", validate_default=True
    )
    finished_on: datetime | None = Field(
        default=None, validation_alias="finishedOn", validate_default=True
    )
    failed_reason: str | None = Field(
        default=None, validation_alias="failedReason", validate_default=True
    )
    data: dict | list | None = Field(default=None)

    @computed_field
    @property
    def wait_time(self) -> timedelta | None:
        if self.processed_on is None:
            return None

        return self.processed_on - self.timestamp

    @computed_field
    @property
    def duration(self) -> timedelta | None:
        if self.processed_on is None or self.finished_on is None:
            return None

        return self.finished_on - self.processed_on

    @field_validator("opts", mode="before")
    @classmethod
    def load_opts_value(cls, value: Any) -> BullJobOpts:
        default_bull_opts = BullJobOpts(attempts=0, priority=0)

        try:
            bull_opts_json = json.loads(value)
            bull_opts = BullJobOpts(default_bull_opts | bull_opts_json)
            return bull_opts
        except ValueError as err:
            print(f"Error ao parsear string de opts do job: {err} ")

            return default_bull_opts

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_load_datetime(cls, value: Any) -> Any:
        try:
            if isinstance(value, str):
                value = int(value)

            data = datetime.fromtimestamp(value / 1000, tz=UTC)
            return data
        except (ValueError, OverflowError, OSError):
            raise ValueError("Utilize um timestamp válido")

    @field_validator("finished_on", mode="before")
    @classmethod
    def finished_on_load_datetime(cls, value: Any) -> Any:
        try:
            if value is None:
                return None

            if isinstance(value, str):
                value = int(value)

            data = datetime.fromtimestamp(value / 1000, tz=UTC)
            return data
        except (ValueError, OverflowError, OSError):
            raise ValueError("Utilize um timestamp válido para finishedOn")

    @field_validator("processed_on", mode="before")
    @classmethod
    def processed_on_load_datetime(cls, value: Any) -> Any:
        try:
            if value is None:
                return None

            if isinstance(value, str):
                value = int(value)

            data = datetime.fromtimestamp(value / 1000, tz=UTC)
            return data
        except (ValueError, OverflowError, OSError):
            raise ValueError("Utilize um timestamp válido para processedOn")

    @field_validator("attempts_made", mode="before")
    @classmethod
    def attempts_made_load_int(cls, value: Any) -> int:
        try:
            return int(value)
        except (ValueError, OverflowError, OSError):
            return 0

    @field_validator("data", mode="before")
    @classmethod
    def data_load_json(cls, value: Any) -> dict | list | None:
        default_json_response = {"_raw": "..."}

        if value is None:
            return default_json_response

        try:
            data = json.loads(value)
            return data
        except ValueError as err:
            print(f"Error ao parsear string de data do job: {err} ")

            return default_json_response

    @field_validator("return_value", mode="before")
    @classmethod
    def return_value_load_json(cls, value: Any) -> Any | None:
        if value is None:
            return None

        try:
            return_value = json.loads(value)
            return return_value
        except ValueError as err:
            print(f"Error ao parsear string de return_value do job: {err} ")

            if isinstance(value, str):
                return value

            return None

    @field_validator("stack_trace", mode="before")
    @classmethod
    def stack_trace_load_json(cls, value: Any) -> dict | list | None:
        try:
            data = json.loads(value)
            return data
        except ValueError as err:
            print(f"Error ao parsear string de data do job: {err} ")

            return []

    @field_validator("processed_on", mode="after")
    @classmethod
    def check_processed_on_value(
        cls, value: datetime | None, info: ValidationInfo
    ) -> datetime | None:
        state = info.data["state"]

        match state:
            case BullState.ACTIVE:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado active é necessário informar o processedOn"
                    )

            case BullState.COMPLETED:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado completed é necessário informar o processedOn"
                    )

            case BullState.FAILED:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado failed é necessário informar o processedOn"
                    )

        return value

    @field_validator("failed_reason", mode="after")
    @classmethod
    def check_failed_reason_value(
        cls, value: datetime | None, info: ValidationInfo
    ) -> datetime | None:
        state = info.data["state"]

        match state:
            case BullState.FAILED:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado failed é necessário informar o failedReason"
                    )

        return value

    @field_validator("finished_on", mode="after")
    @classmethod
    def check_finished_on_value(
        cls, value: datetime | None, info: ValidationInfo
    ) -> datetime | None:
        state = info.data["state"]

        match state:
            case BullState.COMPLETED:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado completed é necessário informar o finishedOn"
                    )
            case BullState.FAILED:
                if value is None:
                    raise ValueError(
                        "Para jobs com o estado failed é necessário informar o finishedOn"
                    )

        return value

    @field_validator("opts", mode="after")
    @classmethod
    def check_opts_value(cls, value: BullJobOpts, info: ValidationInfo) -> BullJobOpts:
        state = info.data["state"]

        match state:
            case BullState.DELAYED:
                delay = value.get("delay")

                if delay is None:
                    raise ValueError(
                        "Para jobs com o estado delayed é necessário informar o delay em opts"
                    )
                elif delay == 0:
                    raise ValueError(
                        "Para jobs com o estado delayed o valor do delay deve ser maior que zero"
                    )

        return value
