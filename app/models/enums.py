from enum import Enum


class ToolStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ProcessingType(str, Enum):
    CLIENT = "client"
    SERVER = "server"
    HYBRID = "hybrid"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    USER = "user"
    SUPER_ADMIN = "super_admin"
