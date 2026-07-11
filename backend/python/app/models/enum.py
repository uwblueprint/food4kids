from enum import Enum


class RoleEnum(str, Enum):
    """User role enum with string values"""

    DRIVER = "driver"
    ADMIN = "admin"


class ProgressEnum(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class NotePermission(str, Enum):
    """Controls who can read/write on a note chain"""

    ADMIN = "Admin"
    ALL = "All"


# Used in route group filtering
class DriveDaysOfWeekEnum(str, Enum):
    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"


class LocationStatusEnum(str, Enum):
    """Derived status surfaced on LocationRead. Not stored — computed from
    Location.in_roster + whether the location appears in a present/future
    route. Precedence: any present/future route → ACTIVE (regardless of
    roster); otherwise in_roster → UNSCHEDULED; otherwise → INACTIVE."""

    ACTIVE = "Active"
    UNSCHEDULED = "Unscheduled"
    INACTIVE = "Inactive"


class RouteStatusEnum(str, Enum):
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class DriverAssignmentStatusEnum(str, Enum):
    """Whether the routes in a RouteGroup have drivers assigned (read from
    Route.driver_id)."""

    ASSIGNED = "Assigned"
    UNASSIGNED = "Unassigned"


class MileageEntryKindEnum(str, Enum):
    """Provenance of a driver mileage ledger entry (see DriverHistory)."""

    # Posted by the nightly freeze job when a driven route is frozen.
    AUTO = "auto"
    # Compensating entry posted when a frozen route's driver is changed
    # (signed: -km from the old driver, +km to the new one).
    REASSIGNMENT = "reassignment"
    # Admin correction (signed), or a frozen-route amendment's length delta.
    # Requires a note.
    MANUAL_ADJUSTMENT = "manual_adjustment"
