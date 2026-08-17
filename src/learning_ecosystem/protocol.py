from enum import IntEnum, StrEnum


class ScaffoldLevel(IntEnum):
    SOCRATIC_QUESTION = 1
    CLARIFICATION = 2
    DIRECTIONAL_HINT = 3
    CONCEPTUAL_HINT = 4
    DIRECT_INSTRUCTION = 5


class TutorMode(StrEnum):
    SOCRATIC = "socratic"
    PROBLEM_BASED = "problem_based"
    FUNDAMENTALS = "fundamentals"
    DIRECT_INSTRUCTION = "direct_instruction"
    AWAITING_PERMISSION = "awaiting_permission"


class ErrorClass(StrEnum):
    TECHNICAL_ERROR = "technical_error"
    INCOMPLETE_REASONING = "incomplete_reasoning"
    TUTOR_AMBIGUITY = "tutor_ambiguity"
    CONTEXT_MISMATCH = "context_mismatch"
    KNOWLEDGE_GAP = "knowledge_gap"
    MISCONCEPTION = "misconception"


class ContextLabel(StrEnum):
    TRIGGER_RECORD = "trigger-record ($Record)"
    STANDALONE_QUERY = "standalone SOQL query"
    CURRENT_RECORD = "current record"
    ALL_RECORDS = "all records in the transaction"
    SYNC_TRANSACTION = "synchronous transaction"
    ASYNC_WORK = "asynchronous deferred work"


READY_STATUSES = frozenset({"demonstrated", "mastered"})
BLOCKING_STATUSES = frozenset(
    {"not_started", "introduced", "novice", "developing", "needs_review"}
)

FRUSTRATION_MARKERS = (
    "i don't know",
    "i dont know",
    "idk",
    "just tell me",
    "give me the answer",
    "this is frustrating",
    "i'm stuck",
    "im stuck",
    "skip",
    "this is stupid",
)

DIRECT_INSTRUCTION_REQUESTS = (
    "explain it to me",
    "just explain",
    "please explain",
    "direct instruction",
    "tell me the answer",
    "i want the explanation",
)

PERMISSION_YES = ("yes", "yeah", "yep", "ok", "okay", "please do", "go ahead", "sure")

OUT_OF_SCOPE_MARKERS = (
    "oauth",
    "connected app",
    "mobile sdk",
    "lightning app builder mobile",
    "unlocked package",
    "2gp",
    "devops center",
    "heroku",
    "marketing cloud",
    "commerce cloud",
    "mulesoft",
)
