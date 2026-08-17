import json
from pathlib import Path

from learning_ecosystem.enums import ConceptStatus
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    CONCEPT_BULKIFICATION,
    CURRICULUM_ID,
    LEARNER_ID,
    NEXT_RECOMMENDED_OBJECTIVE,
    export_poc_learner_snapshot,
    seed_pd1_poc,
)

SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "docs" / "learner_state_example.json"


def test_poc_learner_snapshot_matches_documented_state(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = export_poc_learner_snapshot(repo)
    assert actual["learner_id"] == expected["learner_id"] == LEARNER_ID
    assert actual["curriculum_id"] == expected["curriculum_id"] == CURRICULUM_ID
    assert actual["next_recommended_objective"] == expected["next_recommended_objective"]
    assert actual["concept_states"] == expected["concept_states"]


def test_phase7_resume_states(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    resume = repo.load_resume_state(LEARNER_ID)
    by_id = {state.concept_id: state for state in resume.concept_states}
    assert by_id[CONCEPT_BULKIFICATION].status is ConceptStatus.MASTERED
    snapshot = {item["concept"]: item["status"] for item in export_poc_learner_snapshot(repo)["concept_states"]}
    assert snapshot == {
        "bulkification": "mastered",
        "SOQL": "mastered",
        "governor_limits": "developing",
        "transactions": "mastered",
        "declarative_vs_programmatic_automation": "mastered",
        "flow_bulk_execution": "developing",
    }
    assert NEXT_RECOMMENDED_OBJECTIVE in resume.next_recommended_objectives
    assert any("collection scope" in gap or "interview-local" in gap for gap in resume.unresolved_gaps)
    assert resume.recent_misconceptions


def test_mastered_states_are_explainable(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    explanation = repo.explain_concept_state(LEARNER_ID, CONCEPT_BULKIFICATION)
    assert explanation.state.status is ConceptStatus.MASTERED
    assert len(explanation.evidence) >= 2
    assert {item.evidence_type.value for item in explanation.evidence} != {"recall"}
