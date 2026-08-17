from learning_ecosystem.enums import EventType
from learning_ecosystem.protocol import ContextLabel, TutorMode
from learning_ecosystem.recorder import LearningRecorder
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    CONCEPT_FLOW_BULK,
    LEARNER_ID,
    NODE_FLOW_BULK,
    NODE_SOQL,
    seed_pd1_poc,
)
from learning_ecosystem.tutor import TutorRuntime


def test_at09_resume_does_not_reteach_mastered(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(LEARNER_ID)
    assert turn.objective_node_id == NODE_FLOW_BULK
    assert turn.concept_id == CONCEPT_FLOW_BULK
    assert "Mastered concepts will not be retaught" in turn.message
    assert turn.mode is TutorMode.PROBLEM_BASED
    assert turn.question
    assert "bulkification" not in (turn.question or "").lower() or "Trigger.new" not in (
        turn.question or ""
    )


def test_at01_out_of_scope_is_not_added_as_fundamental(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(LEARNER_ID)
    reply = tutor.respond(turn.session_id, "Can we cover OAuth architecture first? It feels required.")
    assert reply.out_of_scope
    assert "OUT_OF_SCOPE_DEPENDENCY" in reply.message
    assert "will not add it as a required fundamental" in reply.message
    events = repo.list_events(session_id=turn.session_id, event_type=EventType.OUT_OF_SCOPE_DEPENDENCY)
    assert events
    titles = {node.title for node in repo.list_nodes("salesforce-pd1-process-automation-poc")}
    assert "OAuth architecture" in titles


def test_at02_fundamentals_gate_blocks_unmastered_prereq(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    learner = repo.create_learner("New Learner")
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(learner.id)
    assert turn.objective_node_id == NODE_SOQL
    assert turn.objective_node_id != NODE_FLOW_BULK
    events = repo.list_events(session_id=turn.session_id, event_type=EventType.PREREQUISITE_GAP)
    assert events
    assert events[0].details["blocked_target"] == NODE_FLOW_BULK


def test_at03_socratic_default_does_not_reveal_answer(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(LEARNER_ID)
    reply = tutor.respond(
        turn.session_id,
        "Apex has bulkification built in, so this Flow question is easy.",
    )
    assert reply.revealed_answer is False
    assert reply.question
    combined = f"{reply.message} {reply.question}"
    assert "design/implementation practice" not in combined
    assert "I will not supply the answer yet" in reply.message


def test_at04_frustration_asks_permission_before_direct_instruction(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(LEARNER_ID)
    assert turn.mode is TutorMode.PROBLEM_BASED
    reply = tutor.respond(turn.session_id, "I don't know, just tell me.")
    assert reply.awaiting_permission
    assert reply.revealed_answer is False
    assert "permission" in reply.message.lower()
    assert "Multiple triggering records can produce multiple Flow interviews" not in reply.message
    granted = tutor.respond(turn.session_id, "yes")
    assert granted.revealed_answer is True
    assert "Now apply it in your own words" in granted.message


def test_at05_context_reset_is_explicit(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    tutor = TutorRuntime(repo)
    turn = tutor.start_session(LEARNER_ID)
    reset = tutor.signal_context_reset(turn.session_id, ContextLabel.STANDALONE_QUERY)
    assert reset.context_reset is True
    assert reset.message.startswith("Context reset:")
    assert "standalone SOQL query" in reset.message


def test_at12_recorder_does_not_teach(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    recorder = LearningRecorder(repo)
    concept = repo.get_concept(CONCEPT_FLOW_BULK)
    evaluation = recorder.evaluate(
        "I don't understand collections yet.",
        concept=concept,
        artifacts=repo.list_artifacts_for_concept(CONCEPT_FLOW_BULK),
    )
    assert evaluation.teaches is False
    assert not hasattr(evaluation, "question")
