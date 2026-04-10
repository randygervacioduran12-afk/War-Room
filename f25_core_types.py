from enum import Enum


class RunStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    RETRY = "retry"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    PLAN = "plan"
    RESEARCH = "research"
    ENGINEER = "engineer"
    REVIEW = "review"
    ARCHIVE = "archive"
    REPORT = "report"


class AgentName(str, Enum):
    ARMY = "general_of_the_army"
    INTELLIGENCE = "general_of_intelligence"
    ENGINEERING = "general_of_engineering"
    REVIEW = "general_of_review"
    ARCHIVE = "general_of_the_archive"


class MemoryScope(str, Enum):
    RUN = "run"
    PROJECT = "project"
    GLOBAL = "global"


class MemoryKind(str, Enum):
    FACT = "fact"
    DECISION = "decision"
    SUMMARY = "summary"
    ARTIFACT = "artifact"
    FAILURE = "failure"
    NOTE = "note"


class ArtifactKind(str, Enum):
    REPORT = "report"
    CODE_PATCH = "code_patch"
    RESEARCH_BRIEF = "research_brief"
    DECISION_LOG = "decision_log"
    FAILURE_DIGEST = "failure_digest"
    JSON_BLOB = "json_blob"


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"