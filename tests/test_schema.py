from learning_ecosystem.database import create_database

PHASE1_TABLES = {
    "curriculum",
    "curriculum_node",
    "prerequisite",
    "concept",
    "source",
    "knowledge_artifact",
    "mastery_criterion",
    "learner",
    "learner_concept_state",
    "evidence",
    "learning_event",
    "session",
    "session_objective",
}


def test_phase1_tables_exist() -> None:
    connection = create_database()
    names = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert PHASE1_TABLES <= names


def test_foreign_keys_are_enforced() -> None:
    connection = create_database()
    try:
        connection.execute(
            "INSERT INTO curriculum_node VALUES ('n1', 'missing', NULL, 'topic', 't', 'd', 'in_scope', 1)"
        )
        connection.commit()
        raised = False
    except Exception:
        raised = True
    assert raised
