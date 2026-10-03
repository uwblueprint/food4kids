from enum import Enum


class RoleEnum(str, Enum):
    """User role enum with string values"""

    DRIVER = "driver"
    ADMIN = "admin"


class ProgressEnum(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    FAILED = "Failed"


class RouteGenerationMethod(str, Enum):
    """Which engine route generation should use.

    ``AUTO`` walks the tiers in quality order, spending each API's free monthly
    allowance before moving on. The rest pin generation to one engine
    regardless of remaining quota — including past it, into paid usage.
    """

    AUTO = "auto"
    FLEET_ROUTING = "fleet_routing"
    SINGLE_VEHICLE = "single_vehicle"
    CLUSTER_SWEEP = "cluster_sweep"


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
