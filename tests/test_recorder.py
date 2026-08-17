from learning_ecosystem.enums import ConceptStatus
from learning_ecosystem.protocol import ErrorClass
from learning_ecosystem.recorder import LearningRecorder, classify_response
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import CONCEPT_BULKIFICATION, LEARNER_ID, seed_pd1_poc


def test_at06_classifies_issue_types() -> None:
    assert classify_response("Apex is automatically bulkified")[0] is ErrorClass.MISCONCEPTION
    assert classify_response("Apex is not automatically bulkified")[0] is ErrorClass.CORRECTED_MISCONCEPTION
    assert classify_response("SELECT * from Account")[0] is ErrorClass.TECHNICAL_ERROR
    assert classify_response("$Record is all records")[0] is ErrorClass.CONTEXT_MISMATCH
    assert classify_response("The question is ambiguous")[0] is ErrorClass.TUTOR_AMBIGUITY
    assert classify_response("I don't know how interviews relate to collections")[0] is ErrorClass.KNOWLEDGE_GAP


def test_recorder_does_not_downgrade_mastered_on_weak_answer(
    repo: LearningEcosystemRepository,
) -> None:
    seed_pd1_poc(repo)
    recorder = LearningRecorder(repo)
    concept = repo.get_concept(CONCEPT_BULKIFICATION)
    evaluation = recorder.evaluate("maybe?", concept=concept)
    recorder.persist(
        session_id="POC-SESSION-001",
        learner_id=LEARNER_ID,
        evaluation=evaluation,
        learner_text="maybe?",
    )
    state = repo.get_concept_state(LEARNER_ID, CONCEPT_BULKIFICATION)
    assert state is not None
    assert state.status is ConceptStatus.MASTERED
