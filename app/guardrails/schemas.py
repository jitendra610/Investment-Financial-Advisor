
from typing import Literal

from pydantic import BaseModel, Field


class GuardrailResult(BaseModel):
    allowed: bool
    action: Literal["allow", "block", "review"]
    reason: str = ""
    violations: list[str] = Field(default_factory=list)
