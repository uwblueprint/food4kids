from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, TypeVar

import sqlmodel as sm
from sqlmodel import Field

_ONGOING_MODEL_VALIDATE: ContextVar[bool] = ContextVar("_ONGOING_MODEL_VALIDATE")

T = TypeVar("T", bound="BaseModel")


@contextmanager
def set_ongoing_model_validate() -> Any:
    token = _ONGOING_MODEL_VALIDATE.set(True)
    yield
    _ONGOING_MODEL_VALIDATE.reset(token)


class BaseModel(sm.SQLModel):
    """Enhanced base model with common fields and functionality"""

    # Common timestamp fields
    created_at: datetime | None = Field(
        default_factory=datetime.utcnow,
    )
    updated_at: datetime | None = Field(
        default=None,
    )

    def __init__(self, **data: Any) -> None:
        if self.model_config.get("table", False) and not _ONGOING_MODEL_VALIDATE.get(
            False
        ):
            self_copy = self.model_copy()
            self.__pydantic_validator__.validate_python(data, self_instance=self_copy)
            data = self_copy.model_dump()
            self.__dict__ |= self_copy.__dict__
        super().__init__(**data)

    @classmethod
    def model_validate(cls: type[T], *args: Any, **kwargs: Any) -> T:
        with set_ongoing_model_validate():
            return super().model_validate(*args, **kwargs)

    # Pydantic v2 configuration
    model_config = {
        "validate_assignment": True,
        "from_attributes": True,
        "use_enum_values": True,
        "extra": "forbid",  # Reject extra fields
    }
