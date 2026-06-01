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


class DeliveryTypeEnum(str, Enum):
    """Kind of recipient at a Location — set per location, enforced uniform
    within a RouteGroup at generation time."""

    SCHOOL = "School"
    FAMILY = "Family"


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
    """Whether the routes in a RouteGroup have drivers assigned.

    Kept (despite the DriverAssignment table being dropped) because the
    *concept* of assigned/unassigned remains — it just now reads from
    Route.driver_id rather than a separate join table."""

    ASSIGNED = "Assigned"
    UNASSIGNED = "Unassigned"
