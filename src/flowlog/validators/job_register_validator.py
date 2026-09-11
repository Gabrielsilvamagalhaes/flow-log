from datetime import datetime
from pydantic import BaseModel, Field

from flowlog.shared.enums.job_enums import Environment, Jobtypes


class JobRegisterValidator(BaseModel):
    client_identifier: str = Field(min_length=3, max_length=50)
    job_type: Jobtypes
    environment: Environment
