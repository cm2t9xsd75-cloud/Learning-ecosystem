import json
from pathlib import Path

from learning_ecosystem.enums import EventType
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    LEARNER_ID,
    SESSION_ID,
    SESSION_NEXT_OBJECTIVE,
    export_session_record,
    seed_pd1_poc,
)

RECORD_PATH = Path(__file__).resolve().parents[1] / "docs" / "session_record_example.json"


def test_session_record_matches_documented_example(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    expected = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    actual = export_session_record(repo)
    assert actual == expected
    assert actual["session_id"] == SESSION_ID == "POC-SESSION-001"
    assert actual["learner_id"] == LEARNER_ID


def test_session_close_snapshot_includes_hard_progress_and_takeaways(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    snapshot = repo.session_close_snapshot(SESSION_ID)
    assert snapshot["takeaways"][0].startswith("Bulkification is a design principle")
    assert SESSION_NEXT_OBJECTIVE in snapshot["next_recommended_objectives"]
    assert any(
        event.event_type is EventType.PREREQUISITE_GAP
        for event in snapshot["state_transitions"] + repo.list_events(session_id=SESSION_ID)
    )
    events = repo.list_events(session_id=SESSION_ID, event_type=EventType.PREREQUISITE_GAP)
    assert events
    assert "collection scope" in events[0].details["detail"]
