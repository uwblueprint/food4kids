import hashlib
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

# temporary import to avoid circular dependency
if TYPE_CHECKING:
    from .location import Location


class LocationGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(unique=True, index=True)
    color: str  # TODO: Decide if this is going to be an enum or a string
    notes: str = Field(default="")


class LocationGroup(LocationGroupBase, BaseModel, table=True):
    """Location group model"""

    __tablename__ = "location_groups"
    location_group_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # Relationship to locations
    locations: list["Location"] = Relationship(back_populates="location_group")

    DEFAULT_PALETTE: ClassVar[tuple[str, ...]] = (
        "#EF4444",
        "#F97316",
        "#EAB308",
        "#22C55E",
        "#3B82F6",
        "#A855F7",
        "#EC4899",
    )

    @classmethod
    def default_color(cls, name: str) -> str:
        """Pick a palette color deterministically from the group name.

        Same name always yields the same color, so re-imports stay stable. Used
        when auto-creating groups during location import where the caller
        doesn't have a user-selected color.
        """
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        return cls.DEFAULT_PALETTE[int(digest, 16) % len(cls.DEFAULT_PALETTE)]

    @property
    def num_locations(self) -> int:
        """Computed property for number of locations"""
        return len(self.locations)


class LocationGroupCreate(LocationGroupBase):
    """Location group creation request"""

    location_ids: list[UUID] = Field(min_length=1)


class LocationGroupRead(LocationGroupBase):
    """Location group response model"""

    location_group_id: UUID
    num_locations: int


class LocationGroupUpdate(SQLModel):
    """Location group update request - all optional"""

    name: str | None = Field(default=None)
    color: str | None = Field(default=None)
    notes: str | None = Field(default=None)
