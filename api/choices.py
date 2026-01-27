from enum import Enum

class ReportPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class ReportType(Enum):
    INFRASTRUCTURE = "infrastructure"
    SAFETY = "safety"
    ENVIRONMENT = "environment"
    OTHER = "other"

class ReportStatusEnum(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class AssignedUnit(Enum):
    MAINTENANCE = "maintenance"
    POLICE = "police"
    ENVIRONMENTAL = "environmental"
    GENERAL = "general"