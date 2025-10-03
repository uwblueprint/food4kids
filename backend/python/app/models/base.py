from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Enhanced base model with common fields and functionality"""

    # Common timestamp fields
    created_at: datetime | None = Field(
        default_factory=datetime.utcnow,
    )
    updated_at: datetime | None = Field(
        default=None,
    )

    class Config:
        # Enable ORM mode for automatic Pydantic conversion
        from_attributes = True
        # Use enum values instead of names
        use_enum_values = True
