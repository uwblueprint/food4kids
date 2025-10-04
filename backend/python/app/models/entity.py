from sqlalchemy import ARRAY, Enum, String
from sqlmodel import Column, Field, SQLModel

from .base import BaseModel
from .enum import EntityEnum

# common columns and methods across multiple data models can be added via a Mixin class:
# https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html

# see examples of Mixins in current and past Blueprint projects:
# https://github.com/uwblueprint/dancefest-web/blob/master/db/models.py#L10-L70
# https://github.com/uwblueprint/plasta/blob/master/backend/app/models/mixins.py#L10-L95


class EntityBase(SQLModel):
    """Shared fields between table and API models"""

    string_field: str = Field(min_length=1, max_length=255)
    int_field: int = Field(ge=0)  # Greater than or equal to 0
    enum_field: EntityEnum = Field(
        default=EntityEnum.A,
        sa_column=Column(
            Enum(
                EntityEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="entityenum",
            )
        ),
    )
    string_array_field: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String))
    )
    bool_field: bool = Field(default=False)


class Entity(EntityBase, BaseModel, table=True):
    """Entity model for demonstration purposes"""

    __tablename__ = "entities"

    id: int | None = Field(default=None, primary_key=True)


class EntityCreate(EntityBase):
    """Entity creation request"""

    pass


class EntityRead(EntityBase):
    """Entity response model"""

    id: int


class EntityUpdate(SQLModel):
    """Entity update request - all optional"""

    string_field: str | None = Field(default=None, min_length=1, max_length=255)
    int_field: int | None = Field(default=None, ge=0)
    enum_field: EntityEnum | None = Field(default=None)
    string_array_field: list[str] | None = Field(default=None)
    bool_field: bool | None = Field(default=None)
