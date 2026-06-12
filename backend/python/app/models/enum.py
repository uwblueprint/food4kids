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
    SCHOOL = "School"
    FAMILY = "Family"


class LocationStatusEnum(str, Enum):
    ACTIVE = "Active"
    UNSCHEDULED = "Unscheduled"
    INACTIVE = "Inactive"


class RouteStatusEnum(str, Enum):
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class DriverAssignmentStatusEnum(str, Enum):
    ASSIGNED = "Assigned"
    UNASSIGNED = "Unassigned"
