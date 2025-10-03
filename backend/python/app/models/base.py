from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Enhanced base model with common fields and functionality"""

    # Common timestamp fields
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
    )
    updated_at: Optional[datetime] = Field(
        default=None,
    )

    class Config:
        # Enable ORM mode for automatic Pydantic conversion
        from_attributes = True
        # Use enum values instead of names
        use_enum_values = True
