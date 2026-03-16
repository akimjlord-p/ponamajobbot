from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    WORKER = "worker"


class SessionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    AUTO_CLOSED = "auto_closed"


class ReportStatus(str, Enum):
    PARSED = "parsed"
    SHOULD_BE_SENT_TO_ADMIN = "should_be_sent_to_admin"
    SENT_TO_ADMIN = "sent_to_admin"
    REVIEWED_BY_ADMIN = "reviewed_by_admin"


class WorkerCommentTag(str, Enum):
    IDEA = "idea"
    COMPLAINT = "complaint"
    OTHER = "other"


class ReportResultType(str, Enum):
    OPERATIONS_CREATED = "operations_created"
    TEXT_ONLY = "text_only"
    NO_ACTIONABLE_DATA = "no_actionable_data"