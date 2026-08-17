"""Learning Recorder — evaluates evidence and writes state. It does not teach."""

from __future__ import annotations

from dataclasses import dataclass

from learning_ecosystem.enums import (
    ArtifactType,
    ConceptStatus,
    EventType,
    EvidenceStrength,
    EvidenceType,
)
from learning_ecosystem.models import Concept, KnowledgeArtifact
from learning_ecosystem.protocol import ErrorClass, OUT_OF_SCOPE_MARKERS
from learning_ecosystem.repository import LearningEcosystemRepository

_STATUS_RANK = {
    ConceptStatus.NOT_STARTED: 0,
    ConceptStatus.INTRODUCED: 1,
    ConceptStatus.NOVICE: 2,
    ConceptStatus.DEVELOPING: 3,
    ConceptStatus.DEMONSTRATED: 4,
    ConceptStatus.MASTERED: 5,
    ConceptStatus.NEEDS_REVIEW: 3,
}

_MISCONCEPTION_PATTERNS = (
    ("automatically bulkified", "Apex is automatically bulkified."),
    ("bulkification built in", "Apex has bulkification built in."),
    ("150 records", "Returned record count confused with SOQL query count."),
    (
        "each automation is its own transaction",
        "Separate automation components automatically mean separate transactions.",
    ),
    (
        "all interviews share one collection",
        "All interviews share one collection of triggering records.",
    ),
)

_CORRECTION_PATTERNS = (
    "not automatically bulkified",
    "not an automatic property",
    "query count is separate",
    "returned rows are separate",
    "interview-local",
    "not one shared collection",
)

_CONTEXT_MISMATCH_PATTERNS = (
    "same as the trigger",
    "same record as soql",
    "async is the same transaction",
    "$record is all records",
)

_TECHNICAL_PATTERNS = (
    "select *",
    "soql syntax",
    "missing from",
    "compile error",
)

_CORRECT_SIGNALS = (
    "collection",
    "multiple interviews",
    "interview-local",
    "query count",
    "operation volume",
    "not automatically",
    "eventual consistency",
    "parent relationship",
    "account.name",
    "get records",
    "update records",
    "one dml",
    "one query",
)


@dataclass(frozen=True)
class Evaluation:
    concept_id: str | None
    error_class: ErrorClass | None
    evidence_type: EvidenceType
    strength: EvidenceStrength
    assessment: str
    proposed_status: ConceptStatus | None
    out_of_scope: bool
    teaches: bool = False


def classify_response(learner_text: str) -> tuple[ErrorClass | None, str]:
    """AT-06 classification. Returns (class, note). None means no issue detected."""
    text = learner_text.lower()
    if any(marker in text for marker in OUT_OF_SCOPE_MARKERS):
        return ErrorClass.KNOWLEDGE_GAP, "OUT_OF_SCOPE_DEPENDENCY"
    if any(pattern in text for pattern in _CORRECTION_PATTERNS):
        return ErrorClass.CORRECTED_MISCONCEPTION, "Learner restated a corrected model."
    for pattern, note in _MISCONCEPTION_PATTERNS:
        if pattern in text:
            return ErrorClass.MISCONCEPTION, note
    if any(pattern in text for pattern in _TECHNICAL_PATTERNS):
        return ErrorClass.TECHNICAL_ERROR, "Technical/syntax issue rather than a conceptual gap."
    if any(pattern in text for pattern in _CONTEXT_MISMATCH_PATTERNS):
        return ErrorClass.CONTEXT_MISMATCH, "Answer mixes a different scenario/context."
    if "unclear question" in text or "which context" in text or "ambiguous" in text:
        return ErrorClass.TUTOR_AMBIGUITY, "Learner flagged ambiguous tutor context."
    if "i don't know" in text or "don't understand" in text or "not sure how" in text:
        return ErrorClass.KNOWLEDGE_GAP, "Learner does not yet have a complete model."
    return None, "No classified issue."


class LearningRecorder:
    """Observes a turn and persists Evidence / LearningEvent. Never generates pedagogy."""

    def __init__(self, repo: LearningEcosystemRepository) -> None:
        self.repo = repo

    def evaluate(
        self,
        learner_text: str,
        *,
        concept: Concept | None,
        artifacts: list[KnowledgeArtifact] | None = None,
    ) -> Evaluation:
        text = learner_text.lower()
        error_class, note = classify_response(learner_text)
        if note == "OUT_OF_SCOPE_DEPENDENCY":
            return Evaluation(
                concept_id=concept.id if concept else None,
                error_class=error_class,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.WEAK,
                assessment=note,
                proposed_status=None,
                out_of_scope=True,
            )
        if concept is None:
            return Evaluation(
                concept_id=None,
                error_class=ErrorClass.INCOMPLETE_REASONING,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.WEAK,
                assessment="Response is not mapped to an in-scope concept.",
                proposed_status=None,
                out_of_scope=False,
            )
        if artifacts:
            for artifact in artifacts:
                if artifact.artifact_type is ArtifactType.MISCONCEPTION:
                    if artifact.content.lower() in text or _overlap(artifact.content, text):
                        error_class = error_class or ErrorClass.MISCONCEPTION
                        note = artifact.content
        if error_class is ErrorClass.MISCONCEPTION:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.CORRECTION,
                strength=EvidenceStrength.MODERATE,
                assessment=note,
                proposed_status=ConceptStatus.DEVELOPING,
                out_of_scope=False,
            )
        if error_class is ErrorClass.CORRECTED_MISCONCEPTION:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.CORRECTION,
                strength=EvidenceStrength.STRONG,
                assessment=note,
                proposed_status=ConceptStatus.DEMONSTRATED,
                out_of_scope=False,
            )
        if error_class is ErrorClass.CONTEXT_MISMATCH:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.WEAK,
                assessment=note,
                proposed_status=ConceptStatus.DEVELOPING,
                out_of_scope=False,
            )
        if error_class is ErrorClass.TECHNICAL_ERROR:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.APPLICATION,
                strength=EvidenceStrength.WEAK,
                assessment=note,
                proposed_status=None,
                out_of_scope=False,
            )
        if error_class is ErrorClass.TUTOR_AMBIGUITY:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.WEAK,
                assessment=note,
                proposed_status=None,
                out_of_scope=False,
            )
        if error_class is ErrorClass.KNOWLEDGE_GAP:
            return Evaluation(
                concept_id=concept.id,
                error_class=error_class,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.MODERATE,
                assessment=note,
                proposed_status=ConceptStatus.DEVELOPING,
                out_of_scope=False,
            )
        hits = sum(1 for signal in _CORRECT_SIGNALS if signal in text)
        if hits >= 2:
            return Evaluation(
                concept_id=concept.id,
                error_class=None,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.STRONG,
                assessment="Learner generated a relevant explanation.",
                proposed_status=ConceptStatus.DEMONSTRATED,
                out_of_scope=False,
            )
        if hits == 1:
            return Evaluation(
                concept_id=concept.id,
                error_class=ErrorClass.INCOMPLETE_REASONING,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.MODERATE,
                assessment="Partial reasoning; more evidence needed.",
                proposed_status=ConceptStatus.DEVELOPING,
                out_of_scope=False,
            )
        return Evaluation(
            concept_id=concept.id,
            error_class=ErrorClass.INCOMPLETE_REASONING,
            evidence_type=EvidenceType.EXPLANATION,
            strength=EvidenceStrength.WEAK,
            assessment="Response does not yet meet mastery criteria.",
            proposed_status=None,
            out_of_scope=False,
        )

    def persist(
        self,
        *,
        session_id: str,
        learner_id: str,
        evaluation: Evaluation,
        learner_text: str,
    ) -> None:
        if evaluation.out_of_scope:
            self.repo.record_event(
                session_id=session_id,
                event_type=EventType.OUT_OF_SCOPE_DEPENDENCY,
                concept_id=evaluation.concept_id,
                details={"assessment": evaluation.assessment, "learner_text": learner_text},
            )
            return
        if evaluation.concept_id is None:
            return
        evidence = self.repo.record_evidence(
            session_id=session_id,
            learner_id=learner_id,
            concept_id=evaluation.concept_id,
            evidence_type=evaluation.evidence_type,
            learner_text=learner_text,
            evaluator_assessment=evaluation.assessment,
            strength=evaluation.strength,
        )
        event_type = None
        if evaluation.error_class is ErrorClass.MISCONCEPTION:
            event_type = EventType.MISCONCEPTION_DETECTED
        elif evaluation.error_class is ErrorClass.CORRECTED_MISCONCEPTION:
            event_type = EventType.MISCONCEPTION_CORRECTED
        elif evaluation.error_class is ErrorClass.KNOWLEDGE_GAP:
            event_type = EventType.PREREQUISITE_GAP
        if event_type:
            self.repo.record_event(
                session_id=session_id,
                event_type=event_type,
                concept_id=evaluation.concept_id,
                evidence_id=evidence.id,
                details={"classification": evaluation.error_class.value},
            )
        current = self.repo.get_concept_state(learner_id, evaluation.concept_id)
        target = evaluation.proposed_status
        if current and current.status is ConceptStatus.MASTERED:
            if evaluation.error_class is ErrorClass.MISCONCEPTION:
                target = ConceptStatus.NEEDS_REVIEW
            else:
                return
        if target is None or target is ConceptStatus.MASTERED:
            return
        if (
            current
            and target is not ConceptStatus.NEEDS_REVIEW
            and _STATUS_RANK[target] < _STATUS_RANK[current.status]
        ):
            return
        self.repo.apply_state_transition(
            session_id=session_id,
            learner_id=learner_id,
            concept_id=evaluation.concept_id,
            status=target,
            notes=evaluation.assessment,
            misconception_flag=evaluation.error_class is ErrorClass.MISCONCEPTION,
        )


def _overlap(artifact_content: str, learner_text: str) -> bool:
    tokens = [token for token in artifact_content.lower().split() if len(token) > 4]
    return sum(1 for token in tokens if token in learner_text) >= 3
