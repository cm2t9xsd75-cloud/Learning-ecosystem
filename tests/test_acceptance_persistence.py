from learning_ecosystem.enums import (
    ConceptStatus,
    EventType,
    EvidenceStrength,
    EvidenceType,
    SessionStatus,
)
from learning_ecosystem.errors import MasteryNotJustifiedError
from learning_ecosystem.repository import LearningEcosystemRepository


def _recall(repo: LearningEcosystemRepository, seeded: dict[str, str], text: str) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.RECALL,
        learner_text=text,
        evaluator_assessment="Repeated definition",
        strength=EvidenceStrength.STRONG,
    )


def test_at07_single_or_repeated_definition_cannot_master(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    _recall(repo, seeded, "SOQL in a loop is bad.")
    try:
        repo.apply_state_transition(
            session_id=seeded["session_id"],
            learner_id=seeded["learner_id"],
            concept_id=seeded["concept_id"],
            status=ConceptStatus.MASTERED,
        )
        assert False, "expected MasteryNotJustifiedError"
    except MasteryNotJustifiedError:
        assert repo.get_concept_state(seeded["learner_id"], seeded["concept_id"]) is None

    _recall(repo, seeded, "SOQL in a loop is bad because it is SOQL in a loop.")
    try:
        repo.apply_state_transition(
            session_id=seeded["session_id"],
            learner_id=seeded["learner_id"],
            concept_id=seeded["concept_id"],
            status=ConceptStatus.MASTERED,
        )
        assert False, "expected MasteryNotJustifiedError"
    except MasteryNotJustifiedError:
        pass


def test_at07_application_and_explanation_can_master(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.APPLICATION,
        learner_text="This trigger queries inside the for-loop over Trigger.new.",
        evaluator_assessment="Identified SOQL in a loop",
        strength=EvidenceStrength.STRONG,
    )
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.EXPLANATION,
        learner_text="Collect IDs first, then one query, then DML once.",
        evaluator_assessment="Proposed collection-based processing",
        strength=EvidenceStrength.STRONG,
    )
    state = repo.apply_state_transition(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        status=ConceptStatus.MASTERED,
        criteria=repo.list_mastery_criteria(seeded["bulk_node_id"]),
    )
    assert state.status is ConceptStatus.MASTERED
    assert state.evidence_count == 2


def test_at08_session_end_persists_required_fields(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.EXPLANATION,
        learner_text="Flow interviews still share bulkified Get Records.",
        evaluator_assessment="Partial model of Flow bulk execution",
        strength=EvidenceStrength.MODERATE,
    )
    repo.record_event(
        session_id=seeded["session_id"],
        event_type=EventType.MISCONCEPTION_DETECTED,
        concept_id=seeded["concept_id"],
        details={"classification": "knowledge_gap", "gap": "interview-local vs bulk DB"},
    )
    repo.add_session_objective(
        session_id=seeded["session_id"],
        curriculum_node_id=seeded["flow_node_id"],
        starting_status=ConceptStatus.DEVELOPING,
        ending_status=ConceptStatus.DEVELOPING,
        evidence_summary="Flow bulk-execution gap remains",
        outcome="unresolved",
    )
    closed = repo.close_session(
        seeded["session_id"],
        summary="Assessed Flow bulk execution; gap persists.",
        takeaways=["Bulkification is about operation volume, not just record volume."],
        unresolved_items=["Flow interview-local state vs cross-interview bulk DB execution"],
        next_recommended_objectives=[seeded["flow_node_id"]],
    )
    assert closed.status is SessionStatus.COMPLETED
    assert closed.ended_at is not None
    snapshot = repo.session_close_snapshot(seeded["session_id"])
    assert seeded["concept_id"] in snapshot["concepts_assessed"]
    assert snapshot["evidence"]
    assert snapshot["misconceptions"]
    assert snapshot["unresolved_gaps"]
    assert snapshot["takeaways"]
    assert snapshot["next_recommended_objectives"] == [seeded["flow_node_id"]]


def test_at09_and_at10_resume_loads_state_and_flow_gap(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.APPLICATION,
        learner_text="Identified DML in a loop.",
        evaluator_assessment="Correct",
        strength=EvidenceStrength.STRONG,
    )
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.EXPLANATION,
        learner_text="Use a list and one update.",
        evaluator_assessment="Correct",
        strength=EvidenceStrength.STRONG,
    )
    repo.apply_state_transition(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        status=ConceptStatus.MASTERED,
    )
    repo.record_event(
        session_id=seeded["session_id"],
        event_type=EventType.MISCONCEPTION_DETECTED,
        details={"gap": "Flow interview-local vs bulk execution"},
    )
    repo.close_session(
        seeded["session_id"],
        summary="Bulkification mastered; Flow gap open.",
        takeaways=["Do not reteach collection-based DML."],
        unresolved_items=["Flow interview-local state vs cross-interview bulk DB execution"],
        next_recommended_objectives=[seeded["flow_node_id"]],
    )

    resume = repo.load_resume_state(seeded["learner_id"])
    mastered = [state for state in resume.concept_states if state.status is ConceptStatus.MASTERED]
    assert mastered
    assert resume.unresolved_gaps == [
        "Flow interview-local state vs cross-interview bulk DB execution"
    ]
    assert resume.next_recommended_objectives == [seeded["flow_node_id"]]
    assert resume.recent_misconceptions
    assert resume.last_session is not None
    assert resume.last_session.id == seeded["session_id"]


def test_at13_explainability_returns_justifying_evidence(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.APPLICATION,
        learner_text="SOQL is inside the loop.",
        evaluator_assessment="Correct identification",
        strength=EvidenceStrength.STRONG,
    )
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.EXPLANATION,
        learner_text="One query for all IDs.",
        evaluator_assessment="Correct pattern",
        strength=EvidenceStrength.STRONG,
    )
    repo.apply_state_transition(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        status=ConceptStatus.MASTERED,
    )
    explanation = repo.explain_concept_state(seeded["learner_id"], seeded["concept_id"])
    assert explanation.state.status is ConceptStatus.MASTERED
    assert len(explanation.evidence) == 2
    assert explanation.transitions
    assert explanation.transitions[-1].details["to_status"] == "mastered"


def test_at14_downgrade_keeps_prior_mastery_evidence(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.APPLICATION,
        learner_text="Identified SOQL in a loop.",
        evaluator_assessment="Correct",
        strength=EvidenceStrength.STRONG,
    )
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.EXPLANATION,
        learner_text="Use collections.",
        evaluator_assessment="Correct",
        strength=EvidenceStrength.STRONG,
    )
    repo.apply_state_transition(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        status=ConceptStatus.MASTERED,
    )
    prior_evidence = repo.list_evidence(
        learner_id=seeded["learner_id"], concept_id=seeded["concept_id"]
    )
    repo.record_evidence(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        evidence_type=EvidenceType.APPLICATION,
        learner_text="Apex is automatically bulkified so loops are fine.",
        evaluator_assessment="Contradicts prior mastery",
        strength=EvidenceStrength.STRONG,
    )
    downgraded = repo.apply_state_transition(
        session_id=seeded["session_id"],
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        status=ConceptStatus.NEEDS_REVIEW,
        misconception_flag=True,
        notes="Contradictory evidence after prior mastery",
    )
    assert downgraded.status is ConceptStatus.NEEDS_REVIEW
    remaining = repo.list_evidence(
        learner_id=seeded["learner_id"], concept_id=seeded["concept_id"]
    )
    assert {item.id for item in prior_evidence} <= {item.id for item in remaining}
    transitions = repo.list_events(
        learner_id=seeded["learner_id"],
        concept_id=seeded["concept_id"],
        event_type=EventType.MASTERY_TRANSITION,
    )
    assert [event.details["to_status"] for event in transitions] == ["mastered", "needs_review"]
