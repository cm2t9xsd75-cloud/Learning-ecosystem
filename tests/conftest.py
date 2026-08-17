from __future__ import annotations

import pytest

from learning_ecosystem.database import create_database
from learning_ecosystem.enums import (
    ArtifactType,
    EvidenceStrength,
    EvidenceType,
    NodeType,
    PrerequisiteType,
)
from learning_ecosystem.repository import LearningEcosystemRepository


@pytest.fixture
def repo() -> LearningEcosystemRepository:
    return LearningEcosystemRepository(create_database())


@pytest.fixture
def seeded(repo: LearningEcosystemRepository) -> dict[str, str]:
    curriculum = repo.create_curriculum(
        name="Salesforce PD1 POC",
        version="0.1.0",
        authority="Salesforce Platform Developer I — Process Automation and Logic",
        scope_description="POC domain: Process Automation and Logic",
    )
    domain = repo.create_node(
        curriculum_id=curriculum.id,
        node_type=NodeType.DOMAIN,
        title="Process Automation and Logic",
        description="POC domain",
        sequence_order=1,
    )
    soql = repo.create_node(
        curriculum_id=curriculum.id,
        parent_id=domain.id,
        node_type=NodeType.TOPIC,
        title="SOQL",
        description="Query language fundamentals",
        sequence_order=1,
    )
    bulk = repo.create_node(
        curriculum_id=curriculum.id,
        parent_id=domain.id,
        node_type=NodeType.TOPIC,
        title="Bulkification",
        description="Record volume vs operation volume",
        sequence_order=2,
    )
    flow = repo.create_node(
        curriculum_id=curriculum.id,
        parent_id=domain.id,
        node_type=NodeType.TOPIC,
        title="Flow bulk execution semantics",
        description="Interview-local state vs cross-interview bulk execution",
        sequence_order=3,
    )
    repo.add_prerequisite(
        node_id=bulk.id,
        prerequisite_node_id=soql.id,
        relationship_type=PrerequisiteType.REQUIRED,
        rationale="Bulk query patterns depend on SOQL",
    )
    repo.add_mastery_criterion(
        curriculum_node_id=bulk.id,
        criterion="Identifies SOQL/DML in loops",
        evidence_type=EvidenceType.APPLICATION,
        minimum_strength=EvidenceStrength.MODERATE,
    )
    repo.add_mastery_criterion(
        curriculum_node_id=bulk.id,
        criterion="Proposes collection-based processing",
        evidence_type=EvidenceType.EXPLANATION,
        minimum_strength=EvidenceStrength.MODERATE,
    )

    concept = repo.create_concept(
        canonical_name="soql-in-loops",
        definition="Issuing SOQL inside a loop scales queries with record volume.",
        explanation="Governor limits are transaction-scoped; query count is a separate dimension from returned rows.",
        scope_tags=["bulkification", "soql", "governor-limits"],
    )
    source = repo.create_source(
        title="Apex Developer Guide — Governor Limits",
        url="https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm",
        authority="Salesforce",
        version_or_release="Summer '24",
    )
    repo.add_knowledge_artifact(
        concept_id=concept.id,
        artifact_type=ArtifactType.DEFINITION,
        content="SOQL query count is a transaction-scoped governor limit.",
        source_id=source.id,
        authority_level="authoritative",
    )
    learner = repo.create_learner("POC Learner")
    session = repo.start_session(learner_id=learner.id, curriculum_id=curriculum.id)
    return {
        "curriculum_id": curriculum.id,
        "domain_id": domain.id,
        "soql_node_id": soql.id,
        "bulk_node_id": bulk.id,
        "flow_node_id": flow.id,
        "concept_id": concept.id,
        "source_id": source.id,
        "learner_id": learner.id,
        "session_id": session.id,
    }
