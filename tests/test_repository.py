from learning_ecosystem.enums import (
    ConceptStatus,
    EventType,
    EvidenceStrength,
    EvidenceType,
    NodeType,
    SessionStatus,
)
from learning_ecosystem.errors import NotFoundError
from learning_ecosystem.repository import LearningEcosystemRepository


def test_curriculum_graph_round_trip(repo: LearningEcosystemRepository, seeded: dict[str, str]) -> None:
    curriculum = repo.get_curriculum(seeded["curriculum_id"])
    assert curriculum.name == "Salesforce PD1 POC"
    nodes = repo.list_nodes(curriculum.id)
    assert [node.title for node in nodes] == [
        "Process Automation and Logic",
        "SOQL",
        "Bulkification",
        "Flow bulk execution semantics",
    ]
    prereqs = repo.list_prerequisites(seeded["bulk_node_id"])
    assert len(prereqs) == 1
    assert prereqs[0].prerequisite_node_id == seeded["soql_node_id"]
    criteria = repo.list_mastery_criteria(seeded["bulk_node_id"])
    assert {item.evidence_type for item in criteria} == {
        EvidenceType.APPLICATION,
        EvidenceType.EXPLANATION,
    }


def test_knowledge_artifact_is_source_traceable(
    repo: LearningEcosystemRepository, seeded: dict[str, str]
) -> None:
    artifacts = repo.list_artifacts_for_concept(seeded["concept_id"])
    assert len(artifacts) == 1
    sources = repo.list_sources_for_concept(seeded["concept_id"])
    assert sources[0].id == seeded["source_id"]
    assert sources[0].authority == "Salesforce"
    assert sources[0].version_or_release == "Summer '24"
    assert artifacts[0].source_id == sources[0].id


def test_missing_entity_raises(repo: LearningEcosystemRepository) -> None:
    try:
        repo.get_learner("does-not-exist")
        assert False, "expected NotFoundError"
    except NotFoundError as exc:
        assert exc.entity == "Learner"


def test_session_objective_updates(repo: LearningEcosystemRepository, seeded: dict[str, str]) -> None:
    repo.add_session_objective(
        session_id=seeded["session_id"],
        curriculum_node_id=seeded["flow_node_id"],
        starting_status=ConceptStatus.DEVELOPING,
    )
    updated = repo.update_session_objective(
        session_id=seeded["session_id"],
        curriculum_node_id=seeded["flow_node_id"],
        ending_status=ConceptStatus.DEVELOPING,
        evidence_summary="Gap remains: interview-local vs bulk DB execution",
        outcome="unresolved",
    )
    assert updated.starting_status is ConceptStatus.DEVELOPING
    assert updated.ending_status is ConceptStatus.DEVELOPING
    assert updated.outcome == "unresolved"


def test_node_types_match_data_model(repo: LearningEcosystemRepository, seeded: dict[str, str]) -> None:
    domain = repo.get_node(seeded["domain_id"])
    assert domain.node_type is NodeType.DOMAIN
    assert repo.get_session(seeded["session_id"]).status is SessionStatus.ACTIVE


def test_record_event_types(repo: LearningEcosystemRepository, seeded: dict[str, str]) -> None:
    repo.record_event(
        session_id=seeded["session_id"],
        event_type=EventType.OUT_OF_SCOPE_DEPENDENCY,
        details={"concept": "Platform Cache"},
    )
    events = repo.list_events(session_id=seeded["session_id"])
    assert events[-1].event_type is EventType.OUT_OF_SCOPE_DEPENDENCY
