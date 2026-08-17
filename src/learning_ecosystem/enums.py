from enum import StrEnum


class CurriculumStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class NodeType(StrEnum):
    DOMAIN = "domain"
    TOPIC = "topic"
    FUNDAMENTAL = "fundamental"
    OBJECTIVE = "objective"


class ScopeStatus(StrEnum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class PrerequisiteType(StrEnum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"


class ArtifactType(StrEnum):
    DEFINITION = "definition"
    EXAMPLE = "example"
    COUNTEREXAMPLE = "counterexample"
    MISCONCEPTION = "misconception"
    SCENARIO = "scenario"


class EvidenceType(StrEnum):
    RECALL = "recall"
    EXPLANATION = "explanation"
    APPLICATION = "application"
    TRANSFER = "transfer"
    CORRECTION = "correction"
    SYNTHESIS = "synthesis"


class EvidenceStrength(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


STRENGTH_RANK = {
    EvidenceStrength.WEAK: 1,
    EvidenceStrength.MODERATE: 2,
    EvidenceStrength.STRONG: 3,
}


class ConceptStatus(StrEnum):
    NOT_STARTED = "not_started"
    INTRODUCED = "introduced"
    NOVICE = "novice"
    DEVELOPING = "developing"
    DEMONSTRATED = "demonstrated"
    MASTERED = "mastered"
    NEEDS_REVIEW = "needs_review"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class EventType(StrEnum):
    CONCEPT_INTRODUCED = "concept_introduced"
    MISCONCEPTION_DETECTED = "misconception_detected"
    MISCONCEPTION_CORRECTED = "misconception_corrected"
    MASTERY_EVIDENCE = "mastery_evidence"
    MASTERY_TRANSITION = "mastery_transition"
    FRUSTRATION_DETECTED = "frustration_detected"
    DIRECT_INSTRUCTION_REQUESTED = "direct_instruction_requested"
    PREREQUISITE_GAP = "prerequisite_gap"
    OUT_OF_SCOPE_DEPENDENCY = "out_of_scope_dependency"
