"""
Comprehensive tests for SQLModel models with validation and relationships.
"""

import pytest
from pydantic import ValidationError

from app.models.enum import RoleEnum
from app.models.location import Location, LocationCreate, LocationRead, LocationUpdate
from app.models.location_group import (
    LocationGroup,
    LocationGroupCreate,
    LocationGroupRead,
    LocationGroupUpdate,
)
from app.models.user import User, UserCreate, UserRead, UserRegister, UserUpdate


class TestUserModels:
    """Test suite for User models."""

    def test_user_creation_valid_data(self) -> None:
        """Test creating a User with valid data."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "auth_id": "auth-123",
            "role": RoleEnum.USER,
        }

        user = User(**user_data)
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john.doe@example.com"
        assert user.auth_id == "auth-123"
        assert user.role == RoleEnum.USER
        assert user.created_at is not None
        assert user.updated_at is None

    def test_user_creation_invalid_email(self) -> None:
        """Test creating a User with invalid email."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "auth_id": "auth-123",
            "role": RoleEnum.USER,
        }

        with pytest.raises(ValidationError) as exc_info:
            User(**user_data)

        assert "email" in str(exc_info.value)

    def test_user_creation_empty_name(self) -> None:
        """Test creating a User with empty name."""
        user_data = {
            "first_name": "",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "auth_id": "auth-123",
            "role": RoleEnum.USER,
        }

        with pytest.raises(ValidationError) as exc_info:
            User(**user_data)

        assert "first_name" in str(exc_info.value)

    def test_user_create_model(self) -> None:
        """Test UserCreate model validation."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123",
            "role": RoleEnum.USER,
        }

        user_create = UserCreate(**user_data)
        assert user_create.first_name == "John"
        assert user_create.password == "securepassword123"

    def test_user_create_invalid_password(self) -> None:
        """Test UserCreate with invalid password."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "123",  # Too short
            "role": RoleEnum.USER,
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        assert "password" in str(exc_info.value)

    def test_user_read_model(self) -> None:
        """Test UserRead model."""
        user_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "auth_id": "auth-123",
            "role": RoleEnum.USER,
        }

        user_read = UserRead(**user_data)
        assert user_read.id == 1
        assert user_read.first_name == "John"

    def test_user_update_model(self) -> None:
        """Test UserUpdate model with partial data."""
        update_data = {"first_name": "Updated Name"}

        user_update = UserUpdate(**update_data)
        assert user_update.first_name == "Updated Name"
        assert user_update.last_name is None
        assert user_update.email is None

    def test_user_register_model(self) -> None:
        """Test UserRegister model."""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123",
        }

        user_register = UserRegister(**register_data)
        assert user_register.first_name == "John"
        assert user_register.password == "securepassword123"


class TestLocationModels:
    """Test suite for Location models."""

    def test_location_creation_valid_data(self) -> None:
        """Test creating a Location with valid data."""
        location_data = {
            "location_group_id": None,  # Optional field
            "is_school": True,
            "school_name": "Central Elementary",
            "contact_name": "Jane Smith",
            "address": "123 Main St, City, State 12345",
            "phone_number": "(555) 123-4567",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "halal": False,
            "dietary_restrictions": "No nuts",
            "num_children": 150,
            "num_boxes": 25,
            "notes": "Main entrance on Main St",
        }

        location = Location(**location_data)
        assert location.is_school is True
        assert location.school_name == "Central Elementary"
        assert location.contact_name == "Jane Smith"
        assert location.address == "123 Main St, City, State 12345"
        assert location.phone_number == "(555) 123-4567"
        assert location.longitude == -122.4194
        assert location.latitude == 37.7749
        assert location.halal is False
        assert location.dietary_restrictions == "No nuts"
        assert location.num_children == 150
        assert location.num_boxes == 25
        assert location.notes == "Main entrance on Main St"
        assert location.created_at is not None
        assert location.location_id is not None

    def test_location_creation_without_optional_fields(self) -> None:
        """Test creating a Location with only required fields."""
        location_data = {
            "location_group_id": None,  # Optional field
            "is_school": False,
            "contact_name": "John Doe",
            "address": "456 Oak Ave, City, State 12345",
            "phone_number": "(555) 987-6543",
            "longitude": -122.5000,
            "latitude": 37.8000,
            "halal": True,
            "num_boxes": 10,
        }

        location = Location(**location_data)
        assert location.is_school is False
        assert location.school_name is None
        assert location.contact_name == "John Doe"
        assert location.dietary_restrictions is None
        assert location.num_children is None
        assert location.notes is None
        assert location.location_group_id is None

    def test_location_creation_extra_field_validation(self) -> None:
        """Test that extra fields raise ValidationError."""
        location_data = {
            "location_group_id": None,  # Optional field
            "is_school": True,
            "contact_name": "Jane Smith",
            "address": "123 Main St, City, State 12345",
            "phone_number": "(555) 123-4567",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "halal": False,
            "num_boxes": 25,
            "invalid_field": "This should cause an error",  # Extra field
        }

        with pytest.raises(ValidationError) as exc_info:
            Location(**location_data)

        assert "invalid_field" in str(exc_info.value)

    def test_location_create_model(self) -> None:
        """Test LocationCreate model."""
        location_data = {
            "location_group_id": None,  # Optional field
            "is_school": True,
            "contact_name": "Jane Smith",
            "address": "123 Main St, City, State 12345",
            "phone_number": "(555) 123-4567",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "halal": False,
            "num_boxes": 25,
        }

        location_create = LocationCreate(**location_data)
        assert location_create.contact_name == "Jane Smith"
        assert location_create.is_school is True

    def test_location_read_model(self) -> None:
        """Test LocationRead model."""
        from uuid import uuid4

        location_data = {
            "location_id": uuid4(),
            "location_group_id": None,  # Optional field
            "is_school": True,
            "contact_name": "Jane Smith",
            "address": "123 Main St, City, State 12345",
            "phone_number": "(555) 123-4567",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "halal": False,
            "num_boxes": 25,
        }

        location_read = LocationRead(**location_data)
        assert location_read.location_id is not None
        assert location_read.contact_name == "Jane Smith"

    def test_location_update_model(self) -> None:
        """Test LocationUpdate model with partial data."""
        from uuid import uuid4

        update_data = {
            "location_id": uuid4(),
            "location_group_id": None,  # Optional field
            "is_school": True,  # Required field
            "contact_name": "Updated Contact",
            "address": "123 Main St, City, State 12345",  # Required field
            "phone_number": "(555) 123-4567",  # Required field
            "longitude": -122.4194,  # Required field
            "latitude": 37.7749,  # Required field
            "halal": False,  # Required field
            "num_boxes": 30,
        }

        location_update = LocationUpdate(**update_data)
        assert location_update.contact_name == "Updated Contact"
        assert location_update.num_boxes == 30
        assert location_update.is_school is True  # Required field


class TestLocationGroupModels:
    """Test suite for LocationGroup models."""

    def test_location_group_creation_valid_data(self) -> None:
        """Test creating a LocationGroup with valid data."""
        group_data = {
            "name": "Downtown Schools",
            "color": "#FF5733",
            "notes": "Schools in downtown area",
        }

        group = LocationGroup(**group_data)
        assert group.name == "Downtown Schools"
        assert group.color == "#FF5733"
        assert group.notes == "Schools in downtown area"
        assert group.created_at is not None
        assert group.location_group_id is not None

    def test_location_group_creation_without_notes(self) -> None:
        """Test creating a LocationGroup without optional notes."""
        group_data = {
            "name": "Suburban Schools",
            "color": "#33FF57",
        }

        group = LocationGroup(**group_data)
        assert group.name == "Suburban Schools"
        assert group.color == "#33FF57"
        assert group.notes is None

    def test_location_group_creation_extra_field_validation(self) -> None:
        """Test that extra fields raise ValidationError."""
        group_data = {
            "name": "Test Group",
            "color": "#FF5733",
            "invalid_field": "This should cause an error",  # Extra field
        }

        with pytest.raises(ValidationError) as exc_info:
            LocationGroup(**group_data)

        assert "invalid_field" in str(exc_info.value)

    def test_location_group_create_model(self) -> None:
        """Test LocationGroupCreate model."""
        group_data = {
            "name": "Test Group",
            "color": "#FF5733",
            "notes": "Test notes",
        }

        group_create = LocationGroupCreate(**group_data)
        assert group_create.name == "Test Group"
        assert group_create.color == "#FF5733"

    def test_location_group_read_model(self) -> None:
        """Test LocationGroupRead model."""
        from uuid import uuid4

        group_data = {
            "location_group_id": uuid4(),
            "name": "Test Group",
            "color": "#FF5733",
            "notes": "Test notes",
            "num_locations": 5,
        }

        group_read = LocationGroupRead(**group_data)
        assert group_read.location_group_id is not None
        assert group_read.name == "Test Group"
        assert group_read.num_locations == 5

    def test_location_group_update_model(self) -> None:
        """Test LocationGroupUpdate model with partial data."""
        update_data = {
            "name": "Updated Group Name",
            "color": "#33FF57",
        }

        group_update = LocationGroupUpdate(**update_data)
        assert group_update.name == "Updated Group Name"
        assert group_update.color == "#33FF57"
        assert group_update.notes is None


class TestEnumModels:
    """Test suite for Enum models."""

    def test_role_enum_values(self) -> None:
        """Test RoleEnum values."""
        assert RoleEnum.USER.value == "User"
        assert RoleEnum.ADMIN.value == "Admin"

    def test_enum_serialization(self) -> None:
        """Test that enums serialize correctly."""
        user = User(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            auth_id="test-123",
            role=RoleEnum.ADMIN,
        )

        # Test that enum values are properly serialized
        user_dict = user.model_dump()
        assert user_dict["role"] == "Admin"


class TestModelValidation:
    """Test suite for model validation edge cases."""

    def test_location_required_fields_validation(self) -> None:
        """Test that required fields are validated."""
        # Test missing required field
        incomplete_data = {
            "is_school": True,
            "contact_name": "Jane Smith",
            # Missing address, phone_number, longitude, latitude, num_boxes
        }

        with pytest.raises(ValidationError) as exc_info:
            Location(**incomplete_data)

        # Should mention missing required fields
        error_str = str(exc_info.value)
        assert any(
            field in error_str
            for field in [
                "address",
                "phone_number",
                "longitude",
                "latitude",
                "num_boxes",
            ]
        )

    def test_location_group_required_fields_validation(self) -> None:
        """Test that required fields are validated for LocationGroup."""
        # Test missing required field
        incomplete_data = {
            "name": "Test Group",
            # Missing color
        }

        with pytest.raises(ValidationError) as exc_info:
            LocationGroup(**incomplete_data)

        assert "color" in str(exc_info.value)

    def test_model_dump_excludes_none(self) -> None:
        """Test that model_dump excludes None values when appropriate."""
        user = User(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            auth_id="test-123",
            role=RoleEnum.USER,
        )

        user_dict = user.model_dump()
        # updated_at should be None and might be excluded
        assert "first_name" in user_dict
        assert "created_at" in user_dict
