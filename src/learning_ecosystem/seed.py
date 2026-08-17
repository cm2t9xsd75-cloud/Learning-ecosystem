"""Phase 2 — seed the bounded PD1 Process Automation & Logic POC."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from learning_ecosystem.database import create_database
from learning_ecosystem.enums import (
    ArtifactType,
    ConceptRelationshipType,
    EvidenceStrength,
    EvidenceType,
    NodeType,
    PrerequisiteType,
    ScopeStatus,
)
from learning_ecosystem.repository import LearningEcosystemRepository

CURRICULUM_ID = "pd1-poc"
RETRIEVED_AT = "2026-08-17T00:00:00+00:00"
RELEASE = "current as of 2026-08-17"

NODE_DOMAIN = "pd1-node-domain"
NODE_SOQL = "pd1-node-soql"
NODE_BULKIFICATION = "pd1-node-bulkification"
NODE_GOVERNORS = "pd1-node-governor-limits"
NODE_TRANSACTIONS = "pd1-node-transactions"
NODE_FLOW_VS_APEX = "pd1-node-flow-vs-apex"
NODE_FLOW_BULK = "pd1-node-flow-bulk"
NODE_OOS = "pd1-node-out-of-scope"

IN_SCOPE_TOPIC_IDS = (
    NODE_SOQL,
    NODE_BULKIFICATION,
    NODE_GOVERNORS,
    NODE_TRANSACTIONS,
    NODE_FLOW_VS_APEX,
    NODE_FLOW_BULK,
)

CONCEPT_BULKIFICATION = "pd1-concept-bulkification"
CONCEPT_SOQL = "pd1-concept-soql"
CONCEPT_QUERY_COUNT = "pd1-concept-soql-query-count-vs-returned-records"
CONCEPT_RELATIONSHIP_SOQL = "pd1-concept-relationship-soql"
CONCEPT_GOVERNORS = "pd1-concept-governor-limits"
CONCEPT_TRANSACTION = "pd1-concept-transaction"
CONCEPT_ASYNC = "pd1-concept-asynchronous-execution"
CONCEPT_RECORD_PRIOR = "pd1-concept-record-prior"
CONCEPT_FLOW_BULK = "pd1-concept-flow-record-triggered-execution"
CONCEPT_FLOW_VS_APEX = "pd1-concept-flow-vs-apex"

CONCEPT_IDS = (
    CONCEPT_BULKIFICATION,
    CONCEPT_SOQL,
    CONCEPT_QUERY_COUNT,
    CONCEPT_RELATIONSHIP_SOQL,
    CONCEPT_GOVERNORS,
    CONCEPT_TRANSACTION,
    CONCEPT_ASYNC,
    CONCEPT_RECORD_PRIOR,
    CONCEPT_FLOW_BULK,
    CONCEPT_FLOW_VS_APEX,
)

SOURCE_GOV_LIMITS = "pd1-source-apex-governor-limits"
SOURCE_SOQL = "pd1-source-soql-reference"
SOURCE_RELATIONSHIP_SOQL = "pd1-source-soql-relationships"
SOURCE_TRANSACTION = "pd1-source-apex-transactions"
SOURCE_ASYNC = "pd1-source-async-apex"
SOURCE_TRIGGERS = "pd1-source-apex-triggers"
SOURCE_FLOW_BULK = "pd1-source-flow-bulkification"
SOURCE_FLOW_GLOBALS = "pd1-source-flow-global-variables"
SOURCE_RECORD_TRIGGERED = "pd1-source-record-triggered-automation"

SOURCE_IDS = (
    SOURCE_GOV_LIMITS,
    SOURCE_SOQL,
    SOURCE_RELATIONSHIP_SOQL,
    SOURCE_TRANSACTION,
    SOURCE_ASYNC,
    SOURCE_TRIGGERS,
    SOURCE_FLOW_BULK,
    SOURCE_FLOW_GLOBALS,
    SOURCE_RECORD_TRIGGERED,
)

FLOW_BULK_GAP = (
    "The learner understands the need for bulk processing but does not yet have "
    "a complete model of Flow interview-local state versus cross-interview bulk "
    "database execution. Collection scope, Get Records, and Update Records bulk "
    "execution must be represented explicitly; this seed does not invent those mechanics."
)


@dataclass(frozen=True)
class SeedResult:
    curriculum_id: str
    in_scope_topic_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    out_of_scope_node_ids: tuple[str, ...]


def clear_pd1_seed(repo: LearningEcosystemRepository) -> None:
    repo.delete_curriculum(CURRICULUM_ID)
    for concept_id in CONCEPT_IDS:
        repo.connection.execute("DELETE FROM concept WHERE id = ?", (concept_id,))
    for source_id in SOURCE_IDS:
        repo.connection.execute("DELETE FROM source WHERE id = ?", (source_id,))
    repo.connection.commit()


def seed_pd1_poc(
    repo: LearningEcosystemRepository, *, replace: bool = True
) -> SeedResult:
    """Load only the Phase 2 PD1 clusters. Does not invent learner session history."""
    if replace:
        clear_pd1_seed(repo)
    _seed_sources(repo)
    _seed_curriculum(repo)
    _seed_concepts(repo)
    _seed_artifacts(repo)
    _seed_relationships(repo)
    return SeedResult(
        curriculum_id=CURRICULUM_ID,
        in_scope_topic_ids=IN_SCOPE_TOPIC_IDS,
        concept_ids=CONCEPT_IDS,
        out_of_scope_node_ids=tuple(
            node.id
            for node in repo.list_nodes(CURRICULUM_ID, scope_status=ScopeStatus.OUT_OF_SCOPE)
        ),
    )


def _seed_sources(repo: LearningEcosystemRepository) -> None:
    sources = (
        (
            SOURCE_GOV_LIMITS,
            "Apex Governor Limits",
            "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm",
        ),
        (
            SOURCE_SOQL,
            "Salesforce Object Query Language (SOQL)",
            "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm",
        ),
        (
            SOURCE_RELATIONSHIP_SOQL,
            "SOQL Relationship Queries",
            "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships.htm",
        ),
        (
            SOURCE_TRANSACTION,
            "Apex Transactions and Execution Context",
            "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction.htm",
        ),
        (
            SOURCE_ASYNC,
            "Asynchronous Apex",
            "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_async_overview.htm",
        ),
        (
            SOURCE_TRIGGERS,
            "Apex Triggers",
            "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm",
        ),
        (
            SOURCE_FLOW_BULK,
            "Flow Bulkification in Transactions",
            "https://help.salesforce.com/s/articleView?id=platform.flow_concepts_bulkification.htm",
        ),
        (
            SOURCE_FLOW_GLOBALS,
            "Flow Global Variables",
            "https://help.salesforce.com/s/articleView?id=platform.flow_ref_global_variables.htm",
        ),
        (
            SOURCE_RECORD_TRIGGERED,
            "Record-Triggered Automation Decision Guide",
            "https://architect.salesforce.com/docs/architect/decision-guides/guide/record-triggered",
        ),
    )
    for source_id, title, url in sources:
        repo.create_source(
            source_id=source_id,
            title=title,
            url=url,
            authority="Salesforce",
            retrieved_at=RETRIEVED_AT,
            version_or_release=RELEASE,
        )


def _seed_curriculum(repo: LearningEcosystemRepository) -> None:
    repo.create_curriculum(
        curriculum_id=CURRICULUM_ID,
        name="Salesforce PD1 POC",
        version="0.2.0",
        authority="Salesforce Platform Developer I — Process Automation and Logic",
        scope_description=(
            "POC domain only: Process Automation and Logic. "
            "In scope: Flow vs Apex, SOQL/SOSL/DML, bulkification, governor limits, "
            "transactions, Flow execution, triggers/classes, order of execution, "
            "recursion/cascading. Out of scope unless explicitly added: OAuth, "
            "unrelated integration architecture, mobile development, advanced packaging, "
            "broad DevOps architecture, unrelated clouds."
        ),
    )
    repo.create_node(
        node_id=NODE_DOMAIN,
        curriculum_id=CURRICULUM_ID,
        node_type=NodeType.DOMAIN,
        title="Process Automation and Logic",
        description="Bounded PD1 POC domain. Not the full certification.",
        sequence_order=1,
    )
    topics = (
        (
            NODE_SOQL,
            "SOQL",
            "Cluster 4 — SELECT, FROM, WHERE, filtering, relationship traversal, "
            "parent relationship queries, query context vs record context.",
            1,
        ),
        (
            NODE_BULKIFICATION,
            "Bulkification",
            "Cluster 2 — record volume vs operation volume, collections, "
            "SOQL/DML in loops, bulk query and DML patterns.",
            2,
        ),
        (
            NODE_GOVERNORS,
            "Governor Limits",
            "Cluster 3 — transaction-scoped resource controls; query count vs "
            "returned rows; DML statement count vs affected records; multi-tenant rationale.",
            3,
        ),
        (
            NODE_TRANSACTIONS,
            "Transactions",
            "Cluster 5 — transaction boundary, sync vs async, commit behavior, "
            "eventual consistency, cascaded automation in a transaction.",
            4,
        ),
        (
            NODE_FLOW_VS_APEX,
            "Declarative vs Programmatic Automation",
            "Cluster 1 — Flow vs Apex capabilities, complexity and maintainability "
            "tradeoffs, transaction requirements, bulk-processing implications, "
            "when synchronous completion is required.",
            5,
        ),
        (
            NODE_FLOW_BULK,
            "Flow Bulk Execution Semantics",
            "Cluster 6 — record-triggered interviews, element-level bulkification, "
            "$Record / $Record__Prior, collection scope, Get Records / Update Records, "
            "transaction and governor implications.",
            6,
        ),
    )
    for node_id, title, description, order in topics:
        repo.create_node(
            node_id=node_id,
            curriculum_id=CURRICULUM_ID,
            parent_id=NODE_DOMAIN,
            node_type=NodeType.TOPIC,
            title=title,
            description=description,
            sequence_order=order,
        )

    repo.create_node(
        node_id=NODE_OOS,
        curriculum_id=CURRICULUM_ID,
        parent_id=NODE_DOMAIN,
        node_type=NodeType.TOPIC,
        title="Out of scope unless explicitly added",
        description="Boundary topics. Tutor must classify these as OUT_OF_SCOPE_DEPENDENCY.",
        sequence_order=100,
        scope_status=ScopeStatus.OUT_OF_SCOPE,
    )
    out_of_scope = (
        ("pd1-node-oos-oauth", "OAuth architecture", 1),
        ("pd1-node-oos-integration", "Unrelated integration architecture", 2),
        ("pd1-node-oos-mobile", "Mobile development", 3),
        ("pd1-node-oos-packaging", "Advanced packaging", 4),
        ("pd1-node-oos-devops", "Broad DevOps architecture", 5),
        ("pd1-node-oos-clouds", "Unrelated clouds", 6),
    )
    for node_id, title, order in out_of_scope:
        repo.create_node(
            node_id=node_id,
            curriculum_id=CURRICULUM_ID,
            parent_id=NODE_OOS,
            node_type=NodeType.FUNDAMENTAL,
            title=title,
            description="Out of scope for the PD1 Process Automation & Logic POC.",
            sequence_order=order,
            scope_status=ScopeStatus.OUT_OF_SCOPE,
        )

    required = (
        (
            NODE_BULKIFICATION,
            NODE_SOQL,
            "Bulk query patterns depend on SOQL.",
        ),
        (
            NODE_GOVERNORS,
            NODE_BULKIFICATION,
            "Governor-limit reasoning depends on operation volume vs record volume.",
        ),
        (
            NODE_TRANSACTIONS,
            NODE_GOVERNORS,
            "Limits are transaction-scoped resource controls.",
        ),
        (
            NODE_FLOW_BULK,
            NODE_TRANSACTIONS,
            "Flow interviews share a transaction and its limits.",
        ),
        (
            NODE_FLOW_VS_APEX,
            NODE_BULKIFICATION,
            "Tool choice must account for bulk-processing implications.",
        ),
    )
    for node_id, prereq_id, rationale in required:
        repo.add_prerequisite(
            prerequisite_id=f"pd1-prereq-{node_id}-requires-{prereq_id}",
            node_id=node_id,
            prerequisite_node_id=prereq_id,
            relationship_type=PrerequisiteType.REQUIRED,
            rationale=rationale,
        )
    repo.add_prerequisite(
        prerequisite_id="pd1-prereq-flow-vs-apex-transactions",
        node_id=NODE_FLOW_VS_APEX,
        prerequisite_node_id=NODE_TRANSACTIONS,
        relationship_type=PrerequisiteType.RECOMMENDED,
        rationale="Synchronous completion and transaction requirements inform Flow vs Apex.",
    )
    repo.add_prerequisite(
        prerequisite_id="pd1-prereq-flow-bulk-flow-vs-apex",
        node_id=NODE_FLOW_BULK,
        prerequisite_node_id=NODE_FLOW_VS_APEX,
        relationship_type=PrerequisiteType.RECOMMENDED,
        rationale="Flow execution semantics sit after choosing declarative vs programmatic automation.",
    )

    criteria = (
        (
            NODE_FLOW_VS_APEX,
            "Selects Flow or Apex from requirements rather than preference.",
            EvidenceType.APPLICATION,
        ),
        (
            NODE_FLOW_VS_APEX,
            "Rejects 'Apex is automatically bulkified'.",
            EvidenceType.CORRECTION,
        ),
        (
            NODE_FLOW_VS_APEX,
            "Explains when either Flow or Apex could be valid.",
            EvidenceType.EXPLANATION,
        ),
        (
            NODE_BULKIFICATION,
            "Identifies SOQL in loops.",
            EvidenceType.APPLICATION,
        ),
        (
            NODE_BULKIFICATION,
            "Identifies DML in loops.",
            EvidenceType.APPLICATION,
        ),
        (
            NODE_BULKIFICATION,
            "Explains record volume vs platform-operation volume.",
            EvidenceType.EXPLANATION,
        ),
        (
            NODE_BULKIFICATION,
            "Proposes collection-based processing.",
            EvidenceType.EXPLANATION,
        ),
        (
            NODE_GOVERNORS,
            "Treats SOQL query count and returned-row volume as separate dimensions.",
            EvidenceType.EXPLANATION,
        ),
        (
            NODE_SOQL,
            "Writes or explains a parent-relationship SOQL query.",
            EvidenceType.APPLICATION,
        ),
        (
            NODE_TRANSACTIONS,
            "Explains that separate automation components do not automatically mean separate transactions.",
            EvidenceType.EXPLANATION,
        ),
        (
            NODE_FLOW_BULK,
            "Distinguishes interview-local state from cross-interview bulk database execution.",
            EvidenceType.EXPLANATION,
        ),
    )
    for index, (node_id, criterion, evidence_type) in enumerate(criteria, start=1):
        repo.add_mastery_criterion(
            criterion_id=f"pd1-criterion-{index:02d}",
            curriculum_node_id=node_id,
            criterion=criterion,
            evidence_type=evidence_type,
            minimum_strength=EvidenceStrength.MODERATE,
        )


def _seed_concepts(repo: LearningEcosystemRepository) -> None:
    concepts = (
        (
            CONCEPT_BULKIFICATION,
            "bulkification",
            "Design automation so that platform/database operations do not scale "
            "linearly with the number of records being processed within a transaction.",
            "Apex supports bulk patterns, but code can still be non-bulkified. "
            "Bulkification is a design/implementation practice.",
            ["bulkification", "apex", "flow", "dml", "soql"],
        ),
        (
            CONCEPT_SOQL,
            "soql",
            "SOQL retrieves Salesforce records using SELECT, FROM, WHERE, filtering, "
            "and supported relationship traversal.",
            "Query context (the SOQL statement) is distinct from record context "
            "(the current triggering or looped record).",
            ["soql", "query"],
        ),
        (
            CONCEPT_QUERY_COUNT,
            "soql-query-count-vs-returned-records",
            "SOQL query count and returned-record volume are separate resource dimensions.",
            "Query count measures executed queries. Returned-row volume is a separate concern.",
            ["soql", "governor-limits"],
        ),
        (
            CONCEPT_RELATIONSHIP_SOQL,
            "relationship-soql",
            "SOQL can traverse supported Salesforce relationships.",
            "Contact exposes a relationship to Account, allowing parent fields to be traversed.",
            ["soql", "relationships"],
        ),
        (
            CONCEPT_GOVERNORS,
            "governor-limits",
            "Governor limits are transaction-scoped resource controls that keep "
            "multi-tenant orgs from monopolizing shared platform resources.",
            "SOQL query count, returned record count, DML statement count, and "
            "affected record count are separate dimensions.",
            ["governor-limits", "multi-tenant"],
        ),
        (
            CONCEPT_TRANSACTION,
            "transaction",
            "A transaction is a unit of Salesforce work that shares an execution "
            "context, applicable limits, and commit/rollback behavior.",
            "Separate automation components do not automatically mean separate transactions.",
            ["transactions"],
        ),
        (
            CONCEPT_ASYNC,
            "asynchronous-execution",
            "Work is deferred so it executes outside the current synchronous execution path.",
            "The initiating transaction can commit before deferred work completes, "
            "introducing eventual consistency.",
            ["transactions", "asynchronous"],
        ),
        (
            CONCEPT_RECORD_PRIOR,
            "record-prior",
            "$Record__Prior is used to reason about the previous state of the "
            "triggering record and detect transitions.",
            "Previous-value context can detect a field transition; it does not "
            "aggregate all triggering records or create a new transaction.",
            ["flow", "record-prior"],
        ),
        (
            CONCEPT_FLOW_BULK,
            "flow-record-triggered-execution",
            "Multiple triggering records can produce multiple Flow interviews within "
            "a transaction. Salesforce can bulkify compatible database operations "
            "across interviews.",
            "Interview-local state is not automatically one shared collection across "
            f"all interviews. {FLOW_BULK_GAP}",
            ["flow", "bulkification", "transactions"],
        ),
        (
            CONCEPT_FLOW_VS_APEX,
            "flow-vs-apex",
            "Choose Flow or Apex from requirements — complexity, maintainability, "
            "transaction needs, bulk-processing implications, and whether synchronous "
            "completion is required — rather than from preference.",
            "Flow includes built-in bulkification safeguards; Apex supports bulk "
            "patterns but does not make arbitrary code bulk-safe.",
            ["flow", "apex", "bulkification"],
        ),
    )
    for concept_id, name, definition, explanation, tags in concepts:
        repo.create_concept(
            concept_id=concept_id,
            canonical_name=name,
            definition=definition,
            explanation=explanation,
            scope_tags=tags,
        )


def _artifact(
    repo: LearningEcosystemRepository,
    artifact_id: str,
    concept_id: str,
    artifact_type: ArtifactType,
    content: str,
    source_id: str,
    authority_level: str = "authoritative",
) -> None:
    repo.add_knowledge_artifact(
        artifact_id=artifact_id,
        concept_id=concept_id,
        artifact_type=artifact_type,
        content=content,
        source_id=source_id,
        authority_level=authority_level,
    )


def _seed_artifacts(repo: LearningEcosystemRepository) -> None:
    _artifact(
        repo,
        "pd1-art-bulkification-definition",
        CONCEPT_BULKIFICATION,
        ArtifactType.DEFINITION,
        "Design automation so that platform/database operations do not scale "
        "linearly with the number of records being processed within a transaction.",
        SOURCE_TRIGGERS,
    )
    _artifact(
        repo,
        "pd1-art-bulkification-misconception",
        CONCEPT_BULKIFICATION,
        ArtifactType.MISCONCEPTION,
        "Apex is automatically bulkified.",
        SOURCE_TRIGGERS,
    )
    _artifact(
        repo,
        "pd1-art-bulkification-correction",
        CONCEPT_BULKIFICATION,
        ArtifactType.COUNTEREXAMPLE,
        "Apex supports bulk patterns, but code can still be non-bulkified. "
        "Bulkification is a design/implementation practice.",
        SOURCE_TRIGGERS,
    )
    _artifact(
        repo,
        "pd1-art-query-count-definition",
        CONCEPT_QUERY_COUNT,
        ArtifactType.DEFINITION,
        "SOQL query count and returned-record volume are separate resource dimensions.",
        SOURCE_GOV_LIMITS,
    )
    _artifact(
        repo,
        "pd1-art-query-count-misconception",
        CONCEPT_QUERY_COUNT,
        ArtifactType.MISCONCEPTION,
        "A query returning more than 150 records exceeds the SOQL query limit.",
        SOURCE_GOV_LIMITS,
    )
    _artifact(
        repo,
        "pd1-art-query-count-correction",
        CONCEPT_QUERY_COUNT,
        ArtifactType.COUNTEREXAMPLE,
        "Query count measures executed queries. Returned-row volume is a separate concern.",
        SOURCE_GOV_LIMITS,
    )
    _artifact(
        repo,
        "pd1-art-relationship-soql-definition",
        CONCEPT_RELATIONSHIP_SOQL,
        ArtifactType.DEFINITION,
        "SOQL can traverse supported Salesforce relationships.",
        SOURCE_RELATIONSHIP_SOQL,
    )
    _artifact(
        repo,
        "pd1-art-relationship-soql-example",
        CONCEPT_RELATIONSHIP_SOQL,
        ArtifactType.EXAMPLE,
        "SELECT Name, Account.Name FROM Contact WHERE Account.AnnualRevenue > 1000000. "
        "Contact exposes a relationship to Account, allowing parent fields to be traversed.",
        SOURCE_RELATIONSHIP_SOQL,
    )
    _artifact(
        repo,
        "pd1-art-soql-definition",
        CONCEPT_SOQL,
        ArtifactType.DEFINITION,
        "SOQL retrieves records with SELECT, FROM, WHERE, filtering, and relationship traversal.",
        SOURCE_SOQL,
    )
    _artifact(
        repo,
        "pd1-art-governors-definition",
        CONCEPT_GOVERNORS,
        ArtifactType.DEFINITION,
        "Governor limits are transaction-scoped resource controls driven by multi-tenant architecture.",
        SOURCE_GOV_LIMITS,
    )
    _artifact(
        repo,
        "pd1-art-transaction-definition",
        CONCEPT_TRANSACTION,
        ArtifactType.DEFINITION,
        "A transaction is a unit of Salesforce work that shares an execution context, "
        "applicable limits, and commit/rollback behavior.",
        SOURCE_TRANSACTION,
    )
    _artifact(
        repo,
        "pd1-art-transaction-misconception",
        CONCEPT_TRANSACTION,
        ArtifactType.MISCONCEPTION,
        "Separate automation components automatically run in separate transactions.",
        SOURCE_TRANSACTION,
    )
    _artifact(
        repo,
        "pd1-art-transaction-correction",
        CONCEPT_TRANSACTION,
        ArtifactType.COUNTEREXAMPLE,
        "Separate automation components do not automatically mean separate transactions.",
        SOURCE_TRANSACTION,
    )
    _artifact(
        repo,
        "pd1-art-async-definition",
        CONCEPT_ASYNC,
        ArtifactType.DEFINITION,
        "Work is deferred so it executes outside the current synchronous execution path.",
        SOURCE_ASYNC,
    )
    _artifact(
        repo,
        "pd1-art-async-scenario",
        CONCEPT_ASYNC,
        ArtifactType.SCENARIO,
        "The initiating transaction can commit before deferred work completes, "
        "introducing eventual consistency.",
        SOURCE_ASYNC,
    )
    _artifact(
        repo,
        "pd1-art-record-prior-definition",
        CONCEPT_RECORD_PRIOR,
        ArtifactType.DEFINITION,
        "$Record__Prior is used to reason about the previous state of the triggering "
        "record and detect transitions.",
        SOURCE_FLOW_GLOBALS,
    )
    _artifact(
        repo,
        "pd1-art-record-prior-counterexample",
        CONCEPT_RECORD_PRIOR,
        ArtifactType.COUNTEREXAMPLE,
        "Previous-value context can detect a field transition; it does not aggregate "
        "all triggering records or create a new transaction.",
        SOURCE_FLOW_GLOBALS,
    )
    _artifact(
        repo,
        "pd1-art-flow-bulk-definition",
        CONCEPT_FLOW_BULK,
        ArtifactType.DEFINITION,
        "Multiple triggering records can produce multiple Flow interviews within a "
        "transaction. Salesforce can bulkify compatible database operations across interviews.",
        SOURCE_FLOW_BULK,
    )
    _artifact(
        repo,
        "pd1-art-flow-bulk-nuance",
        CONCEPT_FLOW_BULK,
        ArtifactType.SCENARIO,
        "Interview-local state is not automatically one shared collection across all interviews.",
        SOURCE_FLOW_BULK,
    )
    _artifact(
        repo,
        "pd1-art-flow-bulk-gap",
        CONCEPT_FLOW_BULK,
        ArtifactType.SCENARIO,
        FLOW_BULK_GAP,
        SOURCE_FLOW_BULK,
        authority_level="derived",
    )
    _artifact(
        repo,
        "pd1-art-flow-vs-apex-definition",
        CONCEPT_FLOW_VS_APEX,
        ArtifactType.DEFINITION,
        "Choose Flow or Apex from requirements rather than preference. Consider complexity, "
        "maintainability, transaction requirements, bulk-processing implications, and "
        "whether synchronous completion is required.",
        SOURCE_RECORD_TRIGGERED,
    )
    _artifact(
        repo,
        "pd1-art-flow-vs-apex-misconception",
        CONCEPT_FLOW_VS_APEX,
        ArtifactType.MISCONCEPTION,
        "Apex is automatically bulkified, so Apex is always the safer bulk choice.",
        SOURCE_RECORD_TRIGGERED,
    )


def _seed_relationships(repo: LearningEcosystemRepository) -> None:
    pairs = (
        (CONCEPT_QUERY_COUNT, CONCEPT_GOVERNORS, ConceptRelationshipType.EXAMPLE_OF),
        (CONCEPT_RELATIONSHIP_SOQL, CONCEPT_SOQL, ConceptRelationshipType.EXAMPLE_OF),
        (CONCEPT_QUERY_COUNT, CONCEPT_SOQL, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_BULKIFICATION, CONCEPT_SOQL, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_GOVERNORS, CONCEPT_BULKIFICATION, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_TRANSACTION, CONCEPT_GOVERNORS, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_ASYNC, CONCEPT_TRANSACTION, ConceptRelationshipType.CONTRASTS_WITH),
        (CONCEPT_FLOW_BULK, CONCEPT_TRANSACTION, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_FLOW_BULK, CONCEPT_BULKIFICATION, ConceptRelationshipType.DEPENDS_ON),
        (CONCEPT_RECORD_PRIOR, CONCEPT_FLOW_BULK, ConceptRelationshipType.EXAMPLE_OF),
        (CONCEPT_FLOW_VS_APEX, CONCEPT_BULKIFICATION, ConceptRelationshipType.COMMONLY_CONFUSED_WITH),
        (CONCEPT_FLOW_BULK, CONCEPT_FLOW_VS_APEX, ConceptRelationshipType.DEPENDS_ON),
    )
    for source_id, target_id, rel in pairs:
        repo.add_concept_relationship(
            source_concept_id=source_id,
            target_concept_id=target_id,
            relationship_type=rel,
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed the PD1 Process Automation & Logic POC.")
    parser.add_argument(
        "database",
        nargs="?",
        default="learning_ecosystem.db",
        help="SQLite path (default: learning_ecosystem.db)",
    )
    args = parser.parse_args(argv)
    repo = LearningEcosystemRepository(create_database(args.database))
    result = seed_pd1_poc(repo)
    print(f"Seeded curriculum {result.curriculum_id}")
    print(f"In-scope topics: {len(result.in_scope_topic_ids)}")
    print(f"Concepts: {len(result.concept_ids)}")
    print(f"Out-of-scope nodes: {len(result.out_of_scope_node_ids)}")


if __name__ == "__main__":
    main()
