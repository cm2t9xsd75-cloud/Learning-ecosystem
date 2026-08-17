from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learning_ecosystem.enums import (
    ArtifactType,
    ConceptStatus,
    CurriculumStatus,
    EventType,
    EvidenceStrength,
    EvidenceType,
    NodeType,
    PrerequisiteType,
    ScopeStatus,
    SessionStatus,
)


@dataclass(frozen=True)
class Curriculum:
    id: str
    name: str
    version: str
    authority: str
    scope_description: str
    status: CurriculumStatus


@dataclass(frozen=True)
class CurriculumNode:
    id: str
    curriculum_id: str
    parent_id: str | None
    node_type: NodeType
    title: str
    description: str
    scope_status: ScopeStatus
    sequence_order: int


@dataclass(frozen=True)
class Prerequisite:
    id: str
    node_id: str
    prerequisite_node_id: str
    relationship_type: PrerequisiteType
    rationale: str


@dataclass(frozen=True)
class Concept:
    id: str
    canonical_name: str
    definition: str
    explanation: str
    scope_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    url: str | None
    authority: str
    retrieved_at: str
    version_or_release: str | None


@dataclass(frozen=True)
class KnowledgeArtifact:
    id: str
    concept_id: str
    artifact_type: ArtifactType
    content: str
    source_id: str
    authority_level: str


@dataclass(frozen=True)
class MasteryCriterion:
    id: str
    curriculum_node_id: str
    criterion: str
    evidence_type: EvidenceType
    minimum_strength: EvidenceStrength


@dataclass(frozen=True)
class Learner:
    id: str
    display_name: str


@dataclass(frozen=True)
class LearnerConceptState:
    learner_id: str
    concept_id: str
    status: ConceptStatus
    confidence: float | None
    first_seen_at: str
    last_assessed_at: str | None
    evidence_count: int
    misconception_flag: bool
    notes: str | None


@dataclass(frozen=True)
class Evidence:
    id: str
    session_id: str
    learner_id: str
    concept_id: str
    evidence_type: EvidenceType
    learner_text: str
    evaluator_assessment: str
    strength: EvidenceStrength
    created_at: str


@dataclass(frozen=True)
class LearningEvent:
    id: str
    session_id: str
    event_type: EventType
    concept_id: str | None
    evidence_id: str | None
    details: dict[str, Any]
    timestamp: str


@dataclass(frozen=True)
class Session:
    id: str
    learner_id: str
    curriculum_id: str
    started_at: str
    ended_at: str | None
    status: SessionStatus
    summary: str | None
    takeaways: list[str]
    unresolved_items: list[str]
    next_recommended_objectives: list[str]


@dataclass(frozen=True)
class SessionObjective:
    session_id: str
    curriculum_node_id: str
    starting_status: ConceptStatus
    ending_status: ConceptStatus | None
    evidence_summary: str | None
    outcome: str | None


@dataclass(frozen=True)
class ConceptStateExplanation:
    """AT-13: why a learner concept is in its current status."""

    state: LearnerConceptState
    evidence: list[Evidence]
    transitions: list[LearningEvent]


@dataclass(frozen=True)
class ResumeState:
    """AT-09 / Phase 6 shape, loadable from persistence alone."""

    learner: Learner
    concept_states: list[LearnerConceptState]
    unresolved_gaps: list[str]
    next_recommended_objectives: list[str]
    recent_misconceptions: list[LearningEvent]
    last_session: Session | None
