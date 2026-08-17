from learning_ecosystem.enums import ArtifactType, NodeType, ScopeStatus
from learning_ecosystem.repository import LearningEcosystemRepository
from learning_ecosystem.seed import (
    CONCEPT_BULKIFICATION,
    CONCEPT_FLOW_BULK,
    CONCEPT_QUERY_COUNT,
    CURRICULUM_ID,
    FLOW_BULK_GAP,
    IN_SCOPE_TOPIC_IDS,
    seed_pd1_poc,
)


def test_phase2_loads_only_six_in_scope_topics(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    topics = repo.list_nodes(
        CURRICULUM_ID,
        scope_status=ScopeStatus.IN_SCOPE,
        node_type=NodeType.TOPIC,
    )
    titles = {node.title for node in topics}
    assert titles == {
        "SOQL",
        "Bulkification",
        "Governor Limits",
        "Transactions",
        "Declarative vs Programmatic Automation",
        "Flow Bulk Execution Semantics",
    }
    assert {node.id for node in topics} == set(IN_SCOPE_TOPIC_IDS)
    all_titles = {node.title for node in repo.list_nodes(CURRICULUM_ID)}
    assert "Apex Classes and Triggers" not in all_titles
    assert "Exceptions and Error Handling" not in all_titles
    assert "Order of Execution / Recursion / Cascading" not in all_titles


def test_seed_concepts_and_misconceptions(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    names = {concept.canonical_name for concept in repo.list_concepts()}
    assert {
        "bulkification",
        "soql-query-count-vs-returned-records",
        "relationship-soql",
        "transaction",
        "asynchronous-execution",
        "record-prior",
        "flow-record-triggered-execution",
        "flow-vs-apex",
        "governor-limits",
        "soql",
    } <= names

    bulk_artifacts = repo.list_artifacts_for_concept(CONCEPT_BULKIFICATION)
    by_type = {item.artifact_type: item.content for item in bulk_artifacts}
    assert by_type[ArtifactType.MISCONCEPTION] == "Apex is automatically bulkified."
    assert "design/implementation practice" in by_type[ArtifactType.COUNTEREXAMPLE]

    query_artifacts = repo.list_artifacts_for_concept(CONCEPT_QUERY_COUNT)
    misconceptions = [
        item.content
        for item in query_artifacts
        if item.artifact_type is ArtifactType.MISCONCEPTION
    ]
    assert any("150 records" in text for text in misconceptions)


def test_at11_every_artifact_has_official_source(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    for concept in repo.list_concepts():
        artifacts = repo.list_artifacts_for_concept(concept.id)
        assert artifacts, f"{concept.canonical_name} has no artifacts"
        sources = repo.list_sources_for_concept(concept.id)
        assert sources, f"{concept.canonical_name} has no sources"
        for source in sources:
            assert source.authority == "Salesforce"
            assert source.url
            assert source.url.startswith("https://")
            assert source.title
            assert source.retrieved_at
            assert source.version_or_release


def test_flow_bulk_gap_is_explicit(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    contents = [item.content for item in repo.list_artifacts_for_concept(CONCEPT_FLOW_BULK)]
    assert any(FLOW_BULK_GAP in content for content in contents)
    assert any("interview-local" in content for content in contents)


def test_out_of_scope_boundary_nodes(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    oos = repo.list_nodes(CURRICULUM_ID, scope_status=ScopeStatus.OUT_OF_SCOPE)
    titles = {node.title for node in oos}
    assert "OAuth architecture" in titles
    assert "Mobile development" in titles
    assert all(node.scope_status is ScopeStatus.OUT_OF_SCOPE for node in oos)


def test_seed_is_idempotent(repo: LearningEcosystemRepository) -> None:
    first = seed_pd1_poc(repo)
    second = seed_pd1_poc(repo)
    assert first.curriculum_id == second.curriculum_id
    assert len(repo.list_concepts()) == len(first.concept_ids)
    assert repo.get_curriculum(CURRICULUM_ID).name == "Salesforce PD1 POC"


def test_dependency_graph_prerequisites(repo: LearningEcosystemRepository) -> None:
    seed_pd1_poc(repo)
    bulk_prereqs = repo.list_prerequisites("pd1-node-bulkification")
    assert any(item.prerequisite_node_id == "pd1-node-soql" for item in bulk_prereqs)
    flow_prereqs = repo.list_prerequisites("pd1-node-flow-bulk")
    assert any(item.prerequisite_node_id == "pd1-node-transactions" for item in flow_prereqs)
