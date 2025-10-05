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

    USER = "User"
    ADMIN = "Admin"

class StatusEnum(str, Enum):
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"