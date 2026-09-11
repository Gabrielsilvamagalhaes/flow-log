from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator

from flowlog.shared.enums.log_enums import LogLevel


class JobLogValidator(BaseModel):
    level: LogLevel
    message: str = Field(min_length=5, max_length=2000)
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_stack_trace_for_critical_log_levels(self):
        # Validate stack_trace attribute for critical log levels
        if self.level == LogLevel.CRITICAL and not self.stack_trace:
            raise ValueError("O campo 'stack_trace' é obrigatório para levels criticos")

        return self

    @model_validator(mode="after")
    def validate_error_code_for_critical_log_levels(self):
        # Validate erro_code attribute for critical log levels
        if self.level == LogLevel.CRITICAL and not self.error_code:
            raise ValueError("O campo 'error_code' é obrigatório para levels criticos")

        return self
