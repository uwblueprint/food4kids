from enum import Enum


class EntityEnum(str, Enum):
    """Entity enum with string values"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class SimpleEntityEnum(str, Enum):
    """Simple entity enum with string values"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class RoleEnum(str, Enum):
    """User role enum with string values"""

    DRIVER = "driver"
    ADMIN = "admin"


class ProgressEnum(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


# Used in route group filtering
class DriveDaysOfWeekEnum(str, Enum):
    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"


class DeliveryTypeEnum(str, Enum):
    SCHOOL_YEAR = "School Year"
    SUMMER = "Summer"


class RouteStatusEnum(str, Enum):
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class DriverAssignmentStatusEnum(str, Enum):
    ASSIGNED = "Assigned"
    UNASSIGNED = "Unassigned"
