from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, func


class BaseModel(SQLModel):
    """Enhanced base model with common fields and functionality"""
    
    # Common timestamp fields
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_type=DateTime(timezone=True),
        description="Timestamp when the record was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Timestamp when the record was last updated"
    )
    
    class Config:
        # Enable ORM mode for automatic Pydantic conversion
        from_attributes = True
        # Use enum values instead of names
        use_enum_values = True
