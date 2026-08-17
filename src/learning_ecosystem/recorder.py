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

_MISCONCEPTION_PATTERNS = (
    (
        "automatically bulkified",
        ErrorClass.MISCONCEPTION,
        "Apex is automatically bulkified.",
    ),
    (
        "bulkification built in",
        ErrorClass.MISCONCEPTION,
        "Apex has bulkification built in.",
    ),
    (
        "150 records",
        ErrorClass.MISCONCEPTION,
        "Returned record count confused with SOQL query count.",
    ),
    (
        "each automation is its own transaction",
        ErrorClass.MISCONCEPTION,
        "Separate automation components automatically mean separate transactions.",
    ),
    (
        "one shared collection",
        ErrorClass.KNOWLEDGE_GAP,
        "Interview-local state treated as one shared collection.",
    ),
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
        if any(marker in text for marker in OUT_OF_SCOPE_MARKERS):
            return Evaluation(
                concept_id=concept.id if concept else None,
                error_class=ErrorClass.KNOWLEDGE_GAP,
                evidence_type=EvidenceType.EXPLANATION,
                strength=EvidenceStrength.WEAK,
                assessment="OUT_OF_SCOPE_DEPENDENCY",
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
        for pattern, error_class, note in _MISCONCEPTION_PATTERNS:
            if pattern in text:
                return Evaluation(
                    concept_id=concept.id,
                    error_class=error_class,
                    evidence_type=EvidenceType.CORRECTION,
                    strength=EvidenceStrength.MODERATE,
                    assessment=note,
                    proposed_status=ConceptStatus.DEVELOPING,
                    out_of_scope=False,
                )
        if artifacts:
            for artifact in artifacts:
                if artifact.artifact_type is ArtifactType.MISCONCEPTION:
                    if artifact.content.lower() in text or _overlap(artifact.content, text):
                        return Evaluation(
                            concept_id=concept.id,
                            error_class=ErrorClass.MISCONCEPTION,
                            evidence_type=EvidenceType.CORRECTION,
                            strength=EvidenceStrength.MODERATE,
                            assessment=artifact.content,
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
            proposed_status=ConceptStatus.INTRODUCED,
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
        if evaluation.error_class is ErrorClass.MISCONCEPTION:
            self.repo.record_event(
                session_id=session_id,
                event_type=EventType.MISCONCEPTION_DETECTED,
                concept_id=evaluation.concept_id,
                evidence_id=evidence.id,
                details={"classification": evaluation.error_class.value},
            )
        if evaluation.error_class is ErrorClass.KNOWLEDGE_GAP:
            self.repo.record_event(
                session_id=session_id,
                event_type=EventType.PREREQUISITE_GAP,
                concept_id=evaluation.concept_id,
                evidence_id=evidence.id,
                details={"classification": evaluation.error_class.value},
            )
        if evaluation.proposed_status is not None:
            current = self.repo.get_concept_state(learner_id, evaluation.concept_id)
            if current is None or current.status is not evaluation.proposed_status:
                if evaluation.proposed_status is ConceptStatus.MASTERED:
                    return
                self.repo.apply_state_transition(
                    session_id=session_id,
                    learner_id=learner_id,
                    concept_id=evaluation.concept_id,
                    status=evaluation.proposed_status,
                    notes=evaluation.assessment,
                    misconception_flag=evaluation.error_class is ErrorClass.MISCONCEPTION,
                )


def _overlap(artifact_content: str, learner_text: str) -> bool:
    tokens = [token for token in artifact_content.lower().split() if len(token) > 4]
    return sum(1 for token in tokens if token in learner_text) >= 3
