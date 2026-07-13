from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, TypeVar
from zoneinfo import ZoneInfo

import sqlmodel as sm
from sqlmodel import Field

_ONGOING_MODEL_VALIDATE: ContextVar[bool] = ContextVar("_ONGOING_MODEL_VALIDATE")

T = TypeVar("T", bound="BaseModel")


def _now_est_naive() -> datetime:
    """Current time in F4K's timezone (America/New_York), stored tz-naive."""
    return datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)


@contextmanager
def set_ongoing_model_validate() -> Any:
    token = _ONGOING_MODEL_VALIDATE.set(True)
    yield
    _ONGOING_MODEL_VALIDATE.reset(token)


class BaseModel(sm.SQLModel):
    """Enhanced base model with common fields and functionality"""

    # Common timestamp fields.
    # Industry-standard convention (Rails/Django/Laravel): both are stamped on
    # insert (equal to within microseconds) and `updated_at` is bumped on every
    # update. Models that genuinely need "null until first set" (e.g. Job, whose
    # lifecycle tracks started/updated/finished) override `updated_at` explicitly.
    #
    # `updated_at` is bumped by a column-level SQLAlchemy `onupdate`, which fires
    # for BOTH ORM flushes and Core `update()` statements — so bulk updates stay
    # accurate too — unless the statement sets `updated_at` itself.
    created_at: datetime | None = Field(default_factory=_now_est_naive)
    updated_at: datetime | None = Field(
        default_factory=_now_est_naive,
        sa_column_kwargs={"onupdate": _now_est_naive},
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

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
