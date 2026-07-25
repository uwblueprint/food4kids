"""
Streamlined comprehensive tests for SQLModel models focusing on business-critical validation.
Reduced from 92 tests to ~60 tests by removing redundancy and focusing on core business logic.
"""

from datetime import time
from uuid import uuid4

import pytest
from pydantic import ValidationError

# Initialize all models to ensure proper relationship resolution
from app.models import init_app
from app.models.admin import Admin
from app.models.announcement import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.models.driver import (
    Driver,
    DriverCreate,
    DriverUpdate,
)
from app.models.driver_history import (
    DriverHistory,
    DriverHistoryRead,
    DriverHistoryUpdate,
)
from app.models.enum import (
    NotePermission,
    ProgressEnum,
    RoleEnum,
)
from app.models.job import Job, JobUpdate
from app.models.location import Location, LocationRead
from app.models.location_group import LocationGroup
from app.models.note import (
    Attachment,
    Note,
    NoteCreate,
    NoteRead,
    NoteUpdate,
)
from app.models.note_chain import (
    NoteChain,
    NoteChainCreate,
    NoteChainRead,
)
from app.models.route import Route, RouteUpdate
from app.models.route_group import (
    RouteGroup,
    RouteGroupRead,
)
from app.models.route_stop import RouteStop
from app.models.system_settings import EmailReminder, SystemSettings
from app.models.user import User, UserFinalize

init_app()


class TestCoreBusinessValidation:
    """Test suite for core business logic and validation rules."""

    def test_phone_validation_across_models(self) -> None:
        """Test phone validation (custom business logic) across all models that use it."""
        # Test one valid phone number (known to work)
        valid_phone = "+12125551234"

        # Test Driver phone validation
        driver_user = User(
            first_name="Test",
            last_name="Driver",
            email="test@example.com",
            auth_id="test-123",
        )
        driver = Driver(
            user_id=driver_user.user_id,
            phone=valid_phone,
            address="123 Main St",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
        )
        # Phone gets formatted to E164 format
        assert driver.phone.startswith("+")

        # Test Admin phone validation
        admin_user = User(
            first_name="Test",
            last_name="Admin",
            email="admin@example.com",
            auth_id="test-1234",
        )
        admin = Admin(
            user_id=admin_user.user_id,
            admin_phone=valid_phone,
        )
        assert admin.admin_phone.startswith("+")

        # Test invalid phone numbers
        invalid_phones = ["invalid-phone", "123", "abc-def-ghij", "(555) 123-4567"]

        for phone in invalid_phones:
            with pytest.raises(ValidationError) as exc_info:
                user = User(
                    first_name="Test",
                    last_name="Driver",
                    email="test@example.com",
                    auth_id="test-123",
                )
                Driver(
                    user_id=user.user_id,
                    phone=phone,
                    address="123 Main St",
                    license_plate="ABC123",
                    car_make_model="Toyota Camry",
                )
            assert "phone" in str(exc_info.value)

    def test_email_validation_across_models(self) -> None:
        """Test email validation across all models that use it."""
        # Test valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "admin+test@company.org",
        ]

        for email in valid_emails:
            driver_user = User(
                first_name="Test",
                last_name="Driver",
                email=email,
                auth_id="test-123",
            )
            assert driver_user.email == email

        # Test invalid emails
        invalid_emails = ["invalid-email", "@domain.com", "user@", "user.domain.com"]

        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                User(
                    first_name="Test",
                    last_name="Driver",
                    email=email,
                    auth_id="test-123",
                )
            assert "email" in str(exc_info.value)

    def test_password_validation(self) -> None:
        """Test password validation for driver registration."""
        # Test valid password
        user_finalize = UserFinalize(
            user_invite_id=uuid4(),
            password="securepassword123",
        )
        assert user_finalize.password == "securepassword123"

        # Test invalid password (too short)
        with pytest.raises(ValidationError) as exc_info:
            UserFinalize(
                user_invite_id=uuid4(),
                password="123",  # Too short
            )
        assert "password" in str(exc_info.value)

    def test_year_validation_business_rule(self) -> None:
        """Test year (2025-2100) and month (1-12) validation for DriverHistory."""
        # Test valid years and months (boundaries)
        valid_years = [2025, 2030, 2100]
        valid_months = [1, 6, 12]

        for year in valid_years:
            for month in valid_months:
                history = DriverHistory(
                    driver_id=uuid4(), year=year, month=month, km=1000.0
                )
                assert history.year == year
                assert history.month == month

        # Test invalid years
        invalid_years = [2024, 2101, 2000]
        for year in invalid_years:
            with pytest.raises(ValidationError) as exc_info:
                DriverHistory(
                    driver_id=uuid4(),
                    year=year,
                    month=1,
                    km=1000.0,
                )
            assert "year" in str(exc_info.value)

        # Test invalid months
        invalid_months = [0, 13, -1]
        for month in invalid_months:
            with pytest.raises(ValidationError) as exc_info:
                DriverHistory(
                    driver_id=uuid4(),
                    year=2025,
                    month=month,
                    km=1000.0,
                )
            assert "month" in str(exc_info.value)

    def test_route_length_validation(self) -> None:
        """Test route length validation (must be non-negative)."""
        from uuid import uuid4

        # Test valid lengths
        valid_lengths = [0.0, 10.5, 100.0]

        for length in valid_lengths:
            route = Route(
                name="Test Route",
                length=length,
                route_group_id=uuid4(),
            )
            assert route.length == length

        # Test invalid length (negative)
        with pytest.raises(ValidationError) as exc_info:
            Route(
                name="Test Route",
                length=-5.0,  # Negative length should fail
                route_group_id=uuid4(),
            )
        assert "length" in str(exc_info.value)

    def test_route_stop_number_validation(self) -> None:
        """Test route stop number validation (must be >= 1)."""
        from uuid import uuid4

        # Test valid stop numbers
        valid_stops = [1, 2, 10]

        for stop_num in valid_stops:
            route_stop = RouteStop(
                route_id=uuid4(),
                location_id=uuid4(),
                stop_number=stop_num,
            )
            assert route_stop.stop_number == stop_num

        # Test invalid stop number
        with pytest.raises(ValidationError) as exc_info:
            RouteStop(
                route_id=uuid4(),
                location_id=uuid4(),
                stop_number=0,  # Stop number must be >= 1
            )
        assert "stop_number" in str(exc_info.value)

    def test_required_field_validation(self) -> None:
        """Test required field validation across key models."""
        # Test Location required fields
        with pytest.raises(ValidationError) as exc_info:
            Location(  # type: ignore[call-arg]
                contact_name="Jane Smith",
                # Missing: address, phone_primary, longitude, latitude, halal
            )
        error_str = str(exc_info.value)
        assert any(
            field in error_str
            for field in [
                "address",
                "delivery_type",
                "phone_primary",
                "longitude",
                "latitude",
                "halal",
            ]
        )

        # LocationGroup auto-fills color from name when omitted
        group = LocationGroup(name="Test Group")  # type: ignore[call-arg]
        assert group.color in LocationGroup.DEFAULT_PALETTE

        # Test RouteGroup required fields
        from datetime import datetime

        with pytest.raises(ValidationError) as exc_info:
            RouteGroup(
                name="",  # Empty name should fail
                drive_date=datetime(2024, 1, 15, 8, 0),
            )
        assert "name" in str(exc_info.value)

    def test_extra_field_validation(self) -> None:
        """Test that extra fields are rejected (extra='forbid' configuration)."""
        # Test Location rejects extra fields
        with pytest.raises(ValidationError) as exc_info:
            Location(  # type: ignore[call-arg]
                location_group_id=uuid4(),
                name="Jane Smith",
                contact_name="Jane Smith",
                delivery_type="Family",
                address="123 Main St",
                phone_primary="(555) 123-4567",
                longitude=-122.4194,
                latitude=37.7749,
                halal=False,
                invalid_field="This should cause an error",  # Extra field
            )
        assert "invalid_field" in str(exc_info.value)

        # Test LocationGroup rejects extra fields
        with pytest.raises(ValidationError) as exc_info:
            LocationGroup(  # type: ignore[call-arg]
                name="Test Group",
                color="#FF5733",
                invalid_field="This should cause an error",  # Extra field
            )
        assert "invalid_field" in str(exc_info.value)


class TestCoreModels:
    """Test suite for core business models with essential CRUD operations."""

    def test_driver_core_operations(self) -> None:
        """Test Driver model core operations."""
        # Create
        driver_user = User(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            auth_id="auth-123",
        )
        driver = Driver(
            user_id=driver_user.user_id,
            phone="+12125551234",
            address="123 Main St, City, State 12345",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
        )
        assert driver_user.full_name == "John Doe"
        assert driver.active is True  # Default value
        assert driver.created_at is not None

        # Create model
        driver_create = DriverCreate(
            user_id=uuid4(),
            phone="+12125551234",
            address="456 Oak Ave, City, State 12345",
            license_plate="XYZ789",
            car_make_model="Honda Civic",
        )
        assert driver_create.license_plate == "XYZ789"

        # Update model
        driver_update = DriverUpdate(address="456 Oak Ave, City, State 12345")
        assert driver_update.address == "456 Oak Ave, City, State 12345"
        assert driver_update.license_plate is None

    def test_driver_update_rejects_explicit_null_for_non_nullable_fields(
        self,
    ) -> None:
        """Explicit null is a 422 for fields backed by non-nullable columns.

        None as a *default* means "not provided" and stays valid; only a null
        that the client actually sent is rejected. partner_driver_name is the
        one nullable column, where explicit null legitimately clears the value.
        """
        non_nullable_fields = [
            "first_name",
            "last_name",
            "phone",
            "availability",
            "address",
            "license_plate",
            "car_make_model",
            "active",
        ]
        for field in non_nullable_fields:
            with pytest.raises(ValidationError, match="cannot be null"):
                DriverUpdate.model_validate({field: None})

        # Omitting every field is still a valid (no-op) update
        empty_update = DriverUpdate.model_validate({})
        assert empty_update.model_fields_set == set()

        # Explicit null still clears the nullable partner_driver_name
        cleared = DriverUpdate.model_validate({"partner_driver_name": None})
        assert cleared.partner_driver_name is None
        assert "partner_driver_name" in cleared.model_fields_set

    def test_location_core_operations(self) -> None:
        """Test Location model core operations."""
        # Create with all fields
        location = Location(
            location_group_id=uuid4(),
            name="Central Elementary",
            contact_name="Jane Smith",
            delivery_type="School",
            address="123 Main St, City, State 12345",
            phone_primary="(555) 123-4567",
            longitude=-122.4194,
            latitude=37.7749,
            halal=False,
            dietary_restrictions="No nuts",
            num_children=150,
        )
        assert location.name == "Central Elementary"
        assert location.delivery_type == "School"
        assert location.created_at is not None

        # Create with minimal fields
        location_minimal = Location(
            location_group_id=uuid4(),
            name="John Doe",
            contact_name="John Doe",
            delivery_type="Family",
            address="456 Oak Ave, City, State 12345",
            phone_primary="(555) 987-6543",
            longitude=-122.5000,
            latitude=37.8000,
            halal=True,
            num_children=10,
        )
        assert location_minimal.name == "John Doe"
        assert location_minimal.delivery_type == "Family"

        # Read model
        location_read = LocationRead(
            location_id=uuid4(),
            location_group_id=uuid4(),
            location_group_name="Central Elementary",
            name="Central Elementary",
            contact_name="Jane Smith",
            delivery_type="School",
            address="123 Main St, City, State 12345",
            phone_primary="(555) 123-4567",
            longitude=-122.4194,
            latitude=37.7749,
            halal=False,
            num_children=25,
        )
        assert location_read.location_id is not None

    def test_route_core_operations(self) -> None:
        """Test Route model core operations."""
        from uuid import uuid4

        # Create
        route = Route(
            name="Downtown Route",
            notes="Route through downtown area",
            length=15.5,
            route_group_id=uuid4(),
        )
        assert route.name == "Downtown Route"
        assert route.length == 15.5
        assert route.created_at is not None

        # Create with defaults
        route_minimal = Route(
            name="Basic Route",
            length=10.0,
            route_group_id=uuid4(),
        )
        assert route_minimal.notes == ""  # Default value

        # Update
        route_update = RouteUpdate(name="Updated Route", length=20.0)
        assert route_update.name == "Updated Route"
        assert route_update.notes is None

    def test_route_group_core_operations(self) -> None:
        """Test RouteGroup model core operations."""
        from datetime import datetime

        # Create
        route_group = RouteGroup(
            name="Morning Routes",
            notes="Routes for morning delivery",
            drive_date=datetime(2024, 1, 15, 8, 0),
        )
        assert route_group.name == "Morning Routes"
        assert route_group.drive_date == datetime(2024, 1, 15, 8, 0)
        assert route_group.created_at is not None

        # Create with defaults
        route_group_minimal = RouteGroup(
            name="Evening Routes",
            drive_date=datetime(2024, 1, 15, 18, 0),
        )
        assert route_group_minimal.notes == ""  # Default value

        # Read
        from uuid import uuid4

        route_group_read = RouteGroupRead(
            route_group_id=uuid4(),
            name="Test Group",
            notes="Test notes",
            drive_date=datetime(2024, 1, 15, 8, 0),
            num_routes=3,
            status="Completed",
        )
        assert route_group_read.route_group_id is not None

    def test_driver_history_core_operations(self) -> None:
        """Test DriverHistory model core operations."""
        from uuid import uuid4

        # Create
        history = DriverHistory(driver_id=uuid4(), year=2025, km=1500.5, month=12)
        assert history.year == 2025
        assert history.km == 1500.5
        assert history.month == 12
        assert history.created_at is not None

        # Read
        history_read = DriverHistoryRead(
            driver_history_id=1,
            driver_id=uuid4(),
            year=2027,
            month=1,
            km=2200.0,
        )
        assert history_read.driver_history_id == 1

        # Update
        history_update = DriverHistoryUpdate(km=2500.0)
        assert history_update.km == 2500.0

    def test_job_core_operations(self) -> None:
        """Test Job model core operations."""
        from uuid import uuid4

        # Create with route group
        job = Job(
            route_group_id=uuid4(),
            progress=ProgressEnum.PENDING,
        )
        assert job.progress == ProgressEnum.PENDING
        assert job.created_at is not None

        # Create without route group
        job_no_group = Job(
            progress=ProgressEnum.RUNNING,
        )
        assert job_no_group.route_group_id is None
        assert job_no_group.progress == ProgressEnum.RUNNING

        # Update
        from datetime import datetime

        job_update = JobUpdate(
            progress=ProgressEnum.COMPLETED,
            started_at=datetime(2024, 1, 15, 8, 0),
            finished_at=datetime(2024, 1, 15, 10, 0),
        )
        assert job_update.progress == ProgressEnum.COMPLETED
        assert ProgressEnum.CANCELLED.value == "Cancelled"

    def test_note_chain_core_operations(self) -> None:
        """Test NoteChain and Note model core operations."""
        # Create chain with defaults
        chain = NoteChain(
            read_permission=NotePermission.ADMIN,
            write_permission=NotePermission.ADMIN,
        )
        assert chain.read_permission == NotePermission.ADMIN
        assert chain.created_at is not None

        # Create chain with ALL permissions
        chain_public = NoteChain(
            read_permission=NotePermission.ALL,
            write_permission=NotePermission.ALL,
        )
        assert chain_public.read_permission == NotePermission.ALL

        # NoteChainCreate defaults
        chain_create = NoteChainCreate()
        assert chain_create.read_permission == NotePermission.ADMIN
        assert chain_create.write_permission == NotePermission.ADMIN

        # NoteChainRead
        chain_read = NoteChainRead(
            note_chain_id=uuid4(),
            read_permission=NotePermission.ALL,
            write_permission=NotePermission.ADMIN,
        )
        assert chain_read.note_chain_id is not None

        # Create note
        note = Note(
            note_chain_id=uuid4(),
            user_id=uuid4(),
            message="Test note",
        )
        assert note.message == "Test note"
        assert note.is_system is False  # Default
        assert note.created_at is not None

        # System note (no user)
        system_note = Note(
            note_chain_id=uuid4(),
            user_id=None,
            message="System generated",
            is_system=True,
        )
        assert system_note.user_id is None
        assert system_note.is_system is True

        # Note with attachments
        note_with_attachments = Note(
            note_chain_id=uuid4(),
            user_id=uuid4(),
            message="Note with images",
            attachments=[
                Attachment(filename="img1.png", url="https://example.com/img1.png"),
                Attachment(filename="img2.jpg", url="https://example.com/img2.jpg"),
            ],
        )
        assert note_with_attachments.attachments == [
            Attachment(filename="img1.png", url="https://example.com/img1.png"),
            Attachment(filename="img2.jpg", url="https://example.com/img2.jpg"),
        ]

        # Note without attachments defaults to empty list
        note_no_attachments = Note(
            note_chain_id=uuid4(),
            user_id=uuid4(),
            message="No attachments",
        )
        assert note_no_attachments.attachments == []

        # NoteCreate
        note_create = NoteCreate(message="Hello")
        assert note_create.message == "Hello"

        # NoteRead
        note_read = NoteRead(
            note_id=uuid4(),
            note_chain_id=uuid4(),
            user_id=None,
            message="Read test",
            is_system=True,
        )
        assert note_read.note_id is not None

        # NoteUpdate
        note_update = NoteUpdate(message="Updated")
        assert note_update.message == "Updated"

    def test_relationship_models_core_operations(self) -> None:
        """Test RouteStop creation."""
        from uuid import uuid4

        # RouteStop
        route_stop = RouteStop(
            route_id=uuid4(),
            location_id=uuid4(),
            stop_number=1,
        )
        assert route_stop.stop_number == 1
        assert route_stop.created_at is not None


class TestEnumsAndSerialization:
    """Test suite for enums and serialization (consolidated)."""

    def test_all_enum_values_and_serialization(self) -> None:
        """Comprehensive test for all enums and their serialization."""
        # Test RoleEnum
        assert RoleEnum.DRIVER.value == "driver"
        assert RoleEnum.ADMIN.value == "admin"

        # Test ProgressEnum
        assert ProgressEnum.PENDING.value == "Pending"
        assert ProgressEnum.RUNNING.value == "Running"
        assert ProgressEnum.COMPLETED.value == "Completed"
        assert ProgressEnum.FAILED.value == "Failed"

        # Test NotePermission
        assert NotePermission.ADMIN.value == "Admin"
        assert NotePermission.ALL.value == "All"

        # Test enum serialization in models

        # Test ProgressEnum serialization
        job = Job(
            route_group_id=uuid4(),
            progress=ProgressEnum.RUNNING,
        )
        job_dict = job.model_dump()
        assert job_dict["progress"] == "Running"

        # Test RoleEnum serialization (if used in models)
        user = User(
            first_name="Test",
            last_name="Driver",
            email="test@example.com",
            auth_id="test-123",
        )
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="123 Main St",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
        )
        user_dict = user.model_dump()
        driver_dict = driver.model_dump()
        assert user_dict["first_name"] == "Test"
        assert user_dict["last_name"] == "Driver"
        assert user_dict["full_name"] == "Test Driver"
        assert user_dict["email"] == "test@example.com"
        assert driver_dict["phone"] == "+12125551234"
        assert driver_dict["license_plate"] == "ABC123"

    def test_model_serialization_and_defaults(self) -> None:
        """Test model serialization and default value handling."""
        # Test that model_dump works correctly
        user = User(
            first_name="Test",
            last_name="Driver",
            email="test@example.com",
            auth_id="test-123",
        )
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="123 Main St",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
        )

        user_dict = user.model_dump()
        driver_dict = driver.model_dump()
        assert "first_name" in user_dict
        assert "last_name" in user_dict
        assert "full_name" in user_dict
        assert "created_at" in driver_dict
        # updated_at is stamped on insert (equal to created_at within microseconds)
        assert driver_dict["updated_at"] is not None
        assert driver_dict["active"] is True  # Default value
        assert user_dict["role"] == "driver"

        # Test default values across models
        location = Location(
            location_group_id=uuid4(),
            name="John Doe",
            contact_name="John Doe",
            delivery_type="Family",
            address="456 Oak Ave",
            phone_primary="(555) 987-6543",
            longitude=-122.5000,
            latitude=37.8000,
            halal=True,
        )
        assert location.delivery_type == "Family"
        assert location.dietary_restrictions == ""  # Default value
        assert location.num_children == 0  # Default value


class TestModelValidation:
    """Test suite for model validation edge cases."""

    def test_string_field_validation(self) -> None:
        """Test string field validation across models."""
        # Test empty string validation
        with pytest.raises(ValidationError) as exc_info:
            user = User(
                first_name="",  # Empty first name should fail
                last_name="Driver",
                email="test@example.com",
                auth_id="test-123",
            )
            Driver(
                user_id=user.user_id,
                phone="+12125551234",
                address="123 Main St",
                license_plate="ABC123",
                car_make_model="Toyota Camry",
            )
        assert "first_name" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            user = User(
                first_name="Test",
                last_name="Admin",
                email="admin@example.com",
                auth_id="test-123",
            )
            Admin(
                user_id=user.user_id,
                admin_phone="",  # Empty phone fails
            )
        assert "admin_phone" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Driver(
                user_id=uuid4(),
                phone="+12125551234",
                availability=[True, False],
                address="123 Main St",
                license_plate="ABC123",
                car_make_model="Toyota Camry",
            )
        assert "availability" in str(exc_info.value)

    def test_note_message_validation(self) -> None:
        """Test note message validation (empty and too long)."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(message="")
        assert "message" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(message="x" * 2001)
        assert "message" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            NoteUpdate(message="")
        assert "message" in str(exc_info.value)

        # Max length should be accepted
        valid = NoteCreate(message="x" * 2000)
        assert len(valid.message) == 2000

    def test_numeric_field_validation(self) -> None:
        """Test numeric field validation."""
        # Test negative int validation (if any models have this)
        # Most models use positive numbers, but this tests the pattern

        # Test float validation (Route length)
        with pytest.raises(ValidationError) as exc_info:
            Route(
                name="Test Route",
                length=-5.0,  # Negative length should fail
                route_group_id=uuid4(),
            )
        assert "length" in str(exc_info.value)

    def test_optional_field_handling(self) -> None:
        """Test that optional fields work correctly."""
        # Test Admin with only required fields
        user = User(
            first_name="Jane",
            last_name="Admin",
            email="jane@example.com",
            auth_id="test-123",
            role="admin",
        )
        admin = Admin(
            user_id=user.user_id,
            admin_phone="+12125551234",
        )
        system_settings = SystemSettings()
        assert admin.receive_email_notifications is True
        assert system_settings.default_cap is None
        assert system_settings.route_start_time is None
        assert system_settings.warehouse_location is None
        assert system_settings.boxes_per_car == 10
        assert system_settings.dropoff_minutes == 3
        assert system_settings.children_per_box == 2
        assert system_settings.delivery_types == ["School", "Family"]
        assert system_settings.email_reminders == [
            EmailReminder(days_before=1, time=time(9, 0))
        ]

        # Test Job without route_group_id
        job = Job(
            progress=ProgressEnum.RUNNING,
        )
        assert job.route_group_id is None
        assert job.progress == ProgressEnum.RUNNING


class TestAnnouncementModel:
    """Test suite for announcement model validation."""

    def test_announcement_creation(self) -> None:
        """Test creating a valid announcement."""
        user = User(
            first_name="Test",
            last_name="Admin",
            email="admin@example.com",
            auth_id="test-admin-123",
            role="admin",
        )
        announcement = Announcement(
            subject="Test Subject",
            message="Test message body",
            user_id=user.user_id,
            attachments=["https://example.com/image.png"],
        )
        assert announcement.subject == "Test Subject"
        assert announcement.message == "Test message body"
        assert announcement.user_id == user.user_id
        assert announcement.attachments == ["https://example.com/image.png"]
        assert announcement.created_at is not None
        assert announcement.announcement_id is not None

    def test_announcement_create_schema(self) -> None:
        """Test AnnouncementCreate validation."""
        user_id = uuid4()
        create = AnnouncementCreate(
            subject="New Announcement",
            message="Details here",
            user_id=user_id,
        )
        assert create.subject == "New Announcement"
        assert create.attachments == []

        create_with_attachments = AnnouncementCreate(
            subject="With Images",
            message="See attached",
            user_id=user_id,
            attachments=["https://example.com/img1.png"],
        )
        assert len(create_with_attachments.attachments) == 1

    def test_announcement_update_schema(self) -> None:
        """Test AnnouncementUpdate optional fields."""
        update = AnnouncementUpdate(subject="Updated Subject")
        assert update.subject == "Updated Subject"
        assert update.message is None
        assert update.attachments is None

        empty_update = AnnouncementUpdate()
        assert empty_update.subject is None

    def test_announcement_required_fields(self) -> None:
        """Test that subject and message are required."""
        with pytest.raises(ValidationError) as exc_info:
            AnnouncementCreate(
                message="No subject",
                user_id=uuid4(),
            )
        assert "subject" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AnnouncementCreate(
                subject="No message",
                user_id=uuid4(),
            )
        assert "message" in str(exc_info.value)

    def test_announcement_subject_validation(self) -> None:
        """Test subject field min/max length validation."""
        with pytest.raises(ValidationError):
            AnnouncementCreate(
                subject="",
                message="Some message",
                user_id=uuid4(),
            )
