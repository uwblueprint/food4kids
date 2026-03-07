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


class NotePermission(str, Enum):
    """Controls who can read/write on a note chain"""

    ADMIN = "Admin"
    ALL = "All"
