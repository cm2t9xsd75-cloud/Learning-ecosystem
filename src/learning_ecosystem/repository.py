from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

from learning_ecosystem.enums import (
    ArtifactType,
    ConceptRelationshipType,
    ConceptStatus,
    CurriculumStatus,
    EventType,
    EvidenceStrength,
    EvidenceType,
    NodeType,
    PrerequisiteType,
    ScopeStatus,
    SessionStatus,
)
from learning_ecosystem.errors import NotFoundError
from learning_ecosystem.mastery import assert_can_transition
from learning_ecosystem.models import (
    Concept,
    ConceptRelationship,
    ConceptStateExplanation,
    Curriculum,
    CurriculumNode,
    Evidence,
    KnowledgeArtifact,
    Learner,
    LearnerConceptState,
    LearningEvent,
    MasteryCriterion,
    Prerequisite,
    ResumeState,
    Session,
    SessionObjective,
    Source,
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id() -> str:
    return str(uuid.uuid4())


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None, default: Any) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)


def _require_row(row: sqlite3.Row | None, entity: str, entity_id: str) -> sqlite3.Row:
    if row is None:
        raise NotFoundError(entity, entity_id)
    return row


class LearningEcosystemRepository:
    """Relational persistence for curriculum, knowledge, learner state, and audit."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    # --- Curriculum --------------------------------------------------------

    def create_curriculum(
        self,
        *,
        name: str,
        version: str,
        authority: str,
        scope_description: str,
        status: CurriculumStatus = CurriculumStatus.ACTIVE,
        curriculum_id: str | None = None,
    ) -> Curriculum:
        item = Curriculum(
            id=curriculum_id or _id(),
            name=name,
            version=version,
            authority=authority,
            scope_description=scope_description,
            status=status,
        )
        self.connection.execute(
            """
            INSERT INTO curriculum (id, name, version, authority, scope_description, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.name,
                item.version,
                item.authority,
                item.scope_description,
                item.status.value,
            ),
        )
        self.connection.commit()
        return item

    def get_curriculum(self, curriculum_id: str) -> Curriculum:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM curriculum WHERE id = ?", (curriculum_id,)
            ).fetchone(),
            "Curriculum",
            curriculum_id,
        )
        return self._curriculum_from_row(row)

    def create_node(
        self,
        *,
        curriculum_id: str,
        node_type: NodeType,
        title: str,
        description: str,
        sequence_order: int,
        parent_id: str | None = None,
        scope_status: ScopeStatus = ScopeStatus.IN_SCOPE,
        node_id: str | None = None,
    ) -> CurriculumNode:
        item = CurriculumNode(
            id=node_id or _id(),
            curriculum_id=curriculum_id,
            parent_id=parent_id,
            node_type=node_type,
            title=title,
            description=description,
            scope_status=scope_status,
            sequence_order=sequence_order,
        )
        self.connection.execute(
            """
            INSERT INTO curriculum_node (
                id, curriculum_id, parent_id, node_type, title, description,
                scope_status, sequence_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.curriculum_id,
                item.parent_id,
                item.node_type.value,
                item.title,
                item.description,
                item.scope_status.value,
                item.sequence_order,
            ),
        )
        self.connection.commit()
        return item

    def get_node(self, node_id: str) -> CurriculumNode:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM curriculum_node WHERE id = ?", (node_id,)
            ).fetchone(),
            "CurriculumNode",
            node_id,
        )
        return self._node_from_row(row)

    def list_nodes(
        self,
        curriculum_id: str,
        *,
        scope_status: ScopeStatus | None = None,
        node_type: NodeType | None = None,
    ) -> list[CurriculumNode]:
        query = "SELECT * FROM curriculum_node WHERE curriculum_id = ?"
        params: list[Any] = [curriculum_id]
        if scope_status:
            query += " AND scope_status = ?"
            params.append(scope_status.value)
        if node_type:
            query += " AND node_type = ?"
            params.append(node_type.value)
        query += " ORDER BY sequence_order, title"
        return [self._node_from_row(row) for row in self.connection.execute(query, params)]

    def delete_curriculum(self, curriculum_id: str) -> None:
        self.connection.execute("DELETE FROM curriculum WHERE id = ?", (curriculum_id,))
        self.connection.commit()

    def add_prerequisite(
        self,
        *,
        node_id: str,
        prerequisite_node_id: str,
        relationship_type: PrerequisiteType,
        rationale: str,
        prerequisite_id: str | None = None,
    ) -> Prerequisite:
        item = Prerequisite(
            id=prerequisite_id or _id(),
            node_id=node_id,
            prerequisite_node_id=prerequisite_node_id,
            relationship_type=relationship_type,
            rationale=rationale,
        )
        self.connection.execute(
            """
            INSERT INTO prerequisite (
                id, node_id, prerequisite_node_id, relationship_type, rationale
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.node_id,
                item.prerequisite_node_id,
                item.relationship_type.value,
                item.rationale,
            ),
        )
        self.connection.commit()
        return item

    def list_prerequisites(self, node_id: str) -> list[Prerequisite]:
        rows = self.connection.execute(
            "SELECT * FROM prerequisite WHERE node_id = ?", (node_id,)
        ).fetchall()
        return [self._prerequisite_from_row(row) for row in rows]

    def add_mastery_criterion(
        self,
        *,
        curriculum_node_id: str,
        criterion: str,
        evidence_type: EvidenceType,
        minimum_strength: EvidenceStrength,
        criterion_id: str | None = None,
    ) -> MasteryCriterion:
        item = MasteryCriterion(
            id=criterion_id or _id(),
            curriculum_node_id=curriculum_node_id,
            criterion=criterion,
            evidence_type=evidence_type,
            minimum_strength=minimum_strength,
        )
        self.connection.execute(
            """
            INSERT INTO mastery_criterion (
                id, curriculum_node_id, criterion, evidence_type, minimum_strength
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.curriculum_node_id,
                item.criterion,
                item.evidence_type.value,
                item.minimum_strength.value,
            ),
        )
        self.connection.commit()
        return item

    def list_mastery_criteria(self, curriculum_node_id: str) -> list[MasteryCriterion]:
        rows = self.connection.execute(
            "SELECT * FROM mastery_criterion WHERE curriculum_node_id = ?",
            (curriculum_node_id,),
        ).fetchall()
        return [self._criterion_from_row(row) for row in rows]

    # --- Knowledge ---------------------------------------------------------

    def create_concept(
        self,
        *,
        canonical_name: str,
        definition: str,
        explanation: str,
        scope_tags: Iterable[str] = (),
        concept_id: str | None = None,
    ) -> Concept:
        item = Concept(
            id=concept_id or _id(),
            canonical_name=canonical_name,
            definition=definition,
            explanation=explanation,
            scope_tags=list(scope_tags),
        )
        self.connection.execute(
            """
            INSERT INTO concept (id, canonical_name, definition, explanation, scope_tags)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.canonical_name,
                item.definition,
                item.explanation,
                _json_dumps(item.scope_tags),
            ),
        )
        self.connection.commit()
        return item

    def get_concept(self, concept_id: str) -> Concept:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM concept WHERE id = ?", (concept_id,)
            ).fetchone(),
            "Concept",
            concept_id,
        )
        return self._concept_from_row(row)

    def get_concept_by_name(self, canonical_name: str) -> Concept:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM concept WHERE canonical_name = ?", (canonical_name,)
            ).fetchone(),
            "Concept",
            canonical_name,
        )
        return self._concept_from_row(row)

    def list_concepts(self) -> list[Concept]:
        rows = self.connection.execute(
            "SELECT * FROM concept ORDER BY canonical_name"
        ).fetchall()
        return [self._concept_from_row(row) for row in rows]

    def delete_concept(self, concept_id: str) -> None:
        self.connection.execute("DELETE FROM concept WHERE id = ?", (concept_id,))
        self.connection.commit()

    def delete_source(self, source_id: str) -> None:
        self.connection.execute("DELETE FROM source WHERE id = ?", (source_id,))
        self.connection.commit()

    def add_concept_relationship(
        self,
        *,
        source_concept_id: str,
        target_concept_id: str,
        relationship_type: ConceptRelationshipType,
    ) -> ConceptRelationship:
        item = ConceptRelationship(
            source_concept_id=source_concept_id,
            target_concept_id=target_concept_id,
            relationship_type=relationship_type,
        )
        self.connection.execute(
            """
            INSERT INTO concept_relationship (
                source_concept_id, target_concept_id, relationship_type
            ) VALUES (?, ?, ?)
            """,
            (
                item.source_concept_id,
                item.target_concept_id,
                item.relationship_type.value,
            ),
        )
        self.connection.commit()
        return item

    def list_concept_relationships(
        self, concept_id: str | None = None
    ) -> list[ConceptRelationship]:
        if concept_id:
            rows = self.connection.execute(
                """
                SELECT * FROM concept_relationship
                WHERE source_concept_id = ? OR target_concept_id = ?
                """,
                (concept_id, concept_id),
            ).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM concept_relationship").fetchall()
        return [self._relationship_from_row(row) for row in rows]

    def create_source(
        self,
        *,
        title: str,
        authority: str,
        retrieved_at: str | None = None,
        url: str | None = None,
        version_or_release: str | None = None,
        source_id: str | None = None,
    ) -> Source:
        item = Source(
            id=source_id or _id(),
            title=title,
            url=url,
            authority=authority,
            retrieved_at=retrieved_at or _now(),
            version_or_release=version_or_release,
        )
        self.connection.execute(
            """
            INSERT INTO source (id, title, url, authority, retrieved_at, version_or_release)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.title,
                item.url,
                item.authority,
                item.retrieved_at,
                item.version_or_release,
            ),
        )
        self.connection.commit()
        return item

    def get_source(self, source_id: str) -> Source:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM source WHERE id = ?", (source_id,)
            ).fetchone(),
            "Source",
            source_id,
        )
        return self._source_from_row(row)

    def add_knowledge_artifact(
        self,
        *,
        concept_id: str,
        artifact_type: ArtifactType,
        content: str,
        source_id: str,
        authority_level: str,
        artifact_id: str | None = None,
    ) -> KnowledgeArtifact:
        item = KnowledgeArtifact(
            id=artifact_id or _id(),
            concept_id=concept_id,
            artifact_type=artifact_type,
            content=content,
            source_id=source_id,
            authority_level=authority_level,
        )
        self.connection.execute(
            """
            INSERT INTO knowledge_artifact (
                id, concept_id, artifact_type, content, source_id, authority_level
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.concept_id,
                item.artifact_type.value,
                item.content,
                item.source_id,
                item.authority_level,
            ),
        )
        self.connection.commit()
        return item

    def list_artifacts_for_concept(self, concept_id: str) -> list[KnowledgeArtifact]:
        rows = self.connection.execute(
            "SELECT * FROM knowledge_artifact WHERE concept_id = ?", (concept_id,)
        ).fetchall()
        return [self._artifact_from_row(row) for row in rows]

    def list_sources_for_concept(self, concept_id: str) -> list[Source]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT source.*
            FROM source
            JOIN knowledge_artifact ON knowledge_artifact.source_id = source.id
            WHERE knowledge_artifact.concept_id = ?
            """,
            (concept_id,),
        ).fetchall()
        return [self._source_from_row(row) for row in rows]

    # --- Learner + session -------------------------------------------------

    def create_learner(self, display_name: str, learner_id: str | None = None) -> Learner:
        item = Learner(id=learner_id or _id(), display_name=display_name)
        self.connection.execute(
            "INSERT INTO learner (id, display_name) VALUES (?, ?)",
            (item.id, item.display_name),
        )
        self.connection.commit()
        return item

    def delete_learner(self, learner_id: str) -> None:
        self.connection.execute("DELETE FROM learner WHERE id = ?", (learner_id,))
        self.connection.commit()

    def get_learner(self, learner_id: str) -> Learner:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM learner WHERE id = ?", (learner_id,)
            ).fetchone(),
            "Learner",
            learner_id,
        )
        return Learner(id=row["id"], display_name=row["display_name"])

    def start_session(
        self,
        *,
        learner_id: str,
        curriculum_id: str,
        session_id: str | None = None,
        started_at: str | None = None,
    ) -> Session:
        item = Session(
            id=session_id or _id(),
            learner_id=learner_id,
            curriculum_id=curriculum_id,
            started_at=started_at or _now(),
            ended_at=None,
            status=SessionStatus.ACTIVE,
            summary=None,
            takeaways=[],
            unresolved_items=[],
            next_recommended_objectives=[],
        )
        self.connection.execute(
            """
            INSERT INTO session (
                id, learner_id, curriculum_id, started_at, ended_at, status,
                summary, takeaways, unresolved_items, next_recommended_objectives
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.learner_id,
                item.curriculum_id,
                item.started_at,
                item.ended_at,
                item.status.value,
                item.summary,
                _json_dumps(item.takeaways),
                _json_dumps(item.unresolved_items),
                _json_dumps(item.next_recommended_objectives),
            ),
        )
        self.connection.commit()
        return item

    def get_session(self, session_id: str) -> Session:
        row = _require_row(
            self.connection.execute(
                "SELECT * FROM session WHERE id = ?", (session_id,)
            ).fetchone(),
            "Session",
            session_id,
        )
        return self._session_from_row(row)

    def add_session_objective(
        self,
        *,
        session_id: str,
        curriculum_node_id: str,
        starting_status: ConceptStatus,
        ending_status: ConceptStatus | None = None,
        evidence_summary: str | None = None,
        outcome: str | None = None,
    ) -> SessionObjective:
        item = SessionObjective(
            session_id=session_id,
            curriculum_node_id=curriculum_node_id,
            starting_status=starting_status,
            ending_status=ending_status,
            evidence_summary=evidence_summary,
            outcome=outcome,
        )
        self.connection.execute(
            """
            INSERT INTO session_objective (
                session_id, curriculum_node_id, starting_status, ending_status,
                evidence_summary, outcome
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item.session_id,
                item.curriculum_node_id,
                item.starting_status.value,
                item.ending_status.value if item.ending_status else None,
                item.evidence_summary,
                item.outcome,
            ),
        )
        self.connection.commit()
        return item

    def update_session_objective(
        self,
        *,
        session_id: str,
        curriculum_node_id: str,
        ending_status: ConceptStatus | None = None,
        evidence_summary: str | None = None,
        outcome: str | None = None,
    ) -> SessionObjective:
        self.connection.execute(
            """
            UPDATE session_objective
            SET ending_status = COALESCE(?, ending_status),
                evidence_summary = COALESCE(?, evidence_summary),
                outcome = COALESCE(?, outcome)
            WHERE session_id = ? AND curriculum_node_id = ?
            """,
            (
                ending_status.value if ending_status else None,
                evidence_summary,
                outcome,
                session_id,
                curriculum_node_id,
            ),
        )
        self.connection.commit()
        return self.get_session_objective(session_id, curriculum_node_id)

    def get_session_objective(
        self, session_id: str, curriculum_node_id: str
    ) -> SessionObjective:
        row = _require_row(
            self.connection.execute(
                """
                SELECT * FROM session_objective
                WHERE session_id = ? AND curriculum_node_id = ?
                """,
                (session_id, curriculum_node_id),
            ).fetchone(),
            "SessionObjective",
            f"{session_id}:{curriculum_node_id}",
        )
        return self._session_objective_from_row(row)

    def list_session_objectives(self, session_id: str) -> list[SessionObjective]:
        rows = self.connection.execute(
            "SELECT * FROM session_objective WHERE session_id = ?", (session_id,)
        ).fetchall()
        return [self._session_objective_from_row(row) for row in rows]

    def close_session(
        self,
        session_id: str,
        *,
        summary: str,
        takeaways: Iterable[str],
        unresolved_items: Iterable[str],
        next_recommended_objectives: Iterable[str],
        status: SessionStatus = SessionStatus.COMPLETED,
        ended_at: str | None = None,
    ) -> Session:
        """AT-08: persist session-end progress, takeaways, gaps, and next objective."""
        self.connection.execute(
            """
            UPDATE session
            SET ended_at = ?,
                status = ?,
                summary = ?,
                takeaways = ?,
                unresolved_items = ?,
                next_recommended_objectives = ?
            WHERE id = ?
            """,
            (
                ended_at or _now(),
                status.value,
                summary,
                _json_dumps(list(takeaways)),
                _json_dumps(list(unresolved_items)),
                _json_dumps(list(next_recommended_objectives)),
                session_id,
            ),
        )
        self.connection.commit()
        return self.get_session(session_id)

    # --- Evidence, events, state ------------------------------------------

    def record_evidence(
        self,
        *,
        session_id: str,
        learner_id: str,
        concept_id: str,
        evidence_type: EvidenceType,
        learner_text: str,
        evaluator_assessment: str,
        strength: EvidenceStrength,
        evidence_id: str | None = None,
        created_at: str | None = None,
        emit_event: bool = True,
    ) -> Evidence:
        item = Evidence(
            id=evidence_id or _id(),
            session_id=session_id,
            learner_id=learner_id,
            concept_id=concept_id,
            evidence_type=evidence_type,
            learner_text=learner_text,
            evaluator_assessment=evaluator_assessment,
            strength=strength,
            created_at=created_at or _now(),
        )
        self.connection.execute(
            """
            INSERT INTO evidence (
                id, session_id, learner_id, concept_id, evidence_type,
                learner_text, evaluator_assessment, strength, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.session_id,
                item.learner_id,
                item.concept_id,
                item.evidence_type.value,
                item.learner_text,
                item.evaluator_assessment,
                item.strength.value,
                item.created_at,
            ),
        )
        self._refresh_evidence_count(learner_id, concept_id)
        if emit_event:
            self.record_event(
                session_id=session_id,
                event_type=EventType.MASTERY_EVIDENCE,
                concept_id=concept_id,
                evidence_id=item.id,
                details={"evidence_type": item.evidence_type.value, "strength": item.strength.value},
            )
        else:
            self.connection.commit()
        return item

    def list_evidence(
        self,
        *,
        learner_id: str,
        concept_id: str | None = None,
        session_id: str | None = None,
    ) -> list[Evidence]:
        query = "SELECT * FROM evidence WHERE learner_id = ?"
        params: list[Any] = [learner_id]
        if concept_id:
            query += " AND concept_id = ?"
            params.append(concept_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        query += " ORDER BY created_at"
        return [self._evidence_from_row(row) for row in self.connection.execute(query, params)]

    def record_event(
        self,
        *,
        session_id: str,
        event_type: EventType,
        concept_id: str | None = None,
        evidence_id: str | None = None,
        details: dict[str, Any] | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> LearningEvent:
        item = LearningEvent(
            id=event_id or _id(),
            session_id=session_id,
            event_type=event_type,
            concept_id=concept_id,
            evidence_id=evidence_id,
            details=details or {},
            timestamp=timestamp or _now(),
        )
        self.connection.execute(
            """
            INSERT INTO learning_event (
                id, session_id, event_type, concept_id, evidence_id, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.session_id,
                item.event_type.value,
                item.concept_id,
                item.evidence_id,
                _json_dumps(item.details),
                item.timestamp,
            ),
        )
        self.connection.commit()
        return item

    def list_events(
        self,
        *,
        session_id: str | None = None,
        learner_id: str | None = None,
        concept_id: str | None = None,
        event_type: EventType | None = None,
    ) -> list[LearningEvent]:
        clauses = ["1=1"]
        params: list[Any] = []
        if session_id:
            clauses.append("learning_event.session_id = ?")
            params.append(session_id)
        if learner_id:
            clauses.append("session.learner_id = ?")
            params.append(learner_id)
        if concept_id:
            clauses.append("learning_event.concept_id = ?")
            params.append(concept_id)
        if event_type:
            clauses.append("learning_event.event_type = ?")
            params.append(event_type.value)
        query = f"""
            SELECT learning_event.*
            FROM learning_event
            JOIN session ON session.id = learning_event.session_id
            WHERE {' AND '.join(clauses)}
            ORDER BY learning_event.timestamp
        """
        return [self._event_from_row(row) for row in self.connection.execute(query, params)]

    def get_concept_state(
        self, learner_id: str, concept_id: str
    ) -> LearnerConceptState | None:
        row = self.connection.execute(
            """
            SELECT * FROM learner_concept_state
            WHERE learner_id = ? AND concept_id = ?
            """,
            (learner_id, concept_id),
        ).fetchone()
        return self._state_from_row(row) if row else None

    def list_concept_states(self, learner_id: str) -> list[LearnerConceptState]:
        rows = self.connection.execute(
            "SELECT * FROM learner_concept_state WHERE learner_id = ?",
            (learner_id,),
        ).fetchall()
        return [self._state_from_row(row) for row in rows]

    def apply_state_transition(
        self,
        *,
        session_id: str,
        learner_id: str,
        concept_id: str,
        status: ConceptStatus,
        confidence: float | None = None,
        notes: str | None = None,
        misconception_flag: bool | None = None,
        criteria: list[MasteryCriterion] | None = None,
        assessed_at: str | None = None,
    ) -> LearnerConceptState:
        """Update maintained state and write a mastery_transition event.

        Never deletes Evidence or prior LearningEvents (AT-14).
        Refuses `mastered` when evidence is only a repeated definition (AT-07).
        """
        evidence = self.list_evidence(learner_id=learner_id, concept_id=concept_id)
        assert_can_transition(status, evidence, criteria)

        now = assessed_at or _now()
        current = self.get_concept_state(learner_id, concept_id)
        previous_status = current.status if current else ConceptStatus.NOT_STARTED
        first_seen = current.first_seen_at if current else now
        flag = (
            current.misconception_flag
            if misconception_flag is None and current
            else bool(misconception_flag)
        )
        merged_notes = notes if notes is not None else (current.notes if current else None)

        self.connection.execute(
            """
            INSERT INTO learner_concept_state (
                learner_id, concept_id, status, confidence, first_seen_at,
                last_assessed_at, evidence_count, misconception_flag, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id, concept_id) DO UPDATE SET
                status = excluded.status,
                confidence = excluded.confidence,
                last_assessed_at = excluded.last_assessed_at,
                evidence_count = excluded.evidence_count,
                misconception_flag = excluded.misconception_flag,
                notes = excluded.notes
            """,
            (
                learner_id,
                concept_id,
                status.value,
                confidence if confidence is not None else (current.confidence if current else None),
                first_seen,
                now,
                len(evidence),
                int(flag),
                merged_notes,
            ),
        )
        self.record_event(
            session_id=session_id,
            event_type=EventType.MASTERY_TRANSITION,
            concept_id=concept_id,
            details={
                "from_status": previous_status.value,
                "to_status": status.value,
                "evidence_count": len(evidence),
            },
            timestamp=now,
        )
        state = self.get_concept_state(learner_id, concept_id)
        if state is None:
            raise NotFoundError("LearnerConceptState", f"{learner_id}:{concept_id}")
        return state

    def explain_concept_state(
        self, learner_id: str, concept_id: str
    ) -> ConceptStateExplanation:
        """AT-13: return the evidence and transitions that justify current status."""
        state = self.get_concept_state(learner_id, concept_id)
        if state is None:
            raise NotFoundError("LearnerConceptState", f"{learner_id}:{concept_id}")
        return ConceptStateExplanation(
            state=state,
            evidence=self.list_evidence(learner_id=learner_id, concept_id=concept_id),
            transitions=self.list_events(
                learner_id=learner_id,
                concept_id=concept_id,
                event_type=EventType.MASTERY_TRANSITION,
            ),
        )

    def load_resume_state(self, learner_id: str) -> ResumeState:
        """AT-09: load persisted learner state for a future session."""
        learner = self.get_learner(learner_id)
        last_row = self.connection.execute(
            """
            SELECT * FROM session
            WHERE learner_id = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (learner_id,),
        ).fetchone()
        last_session = self._session_from_row(last_row) if last_row else None
        misconceptions = [
            event
            for event in self.list_events(
                learner_id=learner_id,
                event_type=EventType.MISCONCEPTION_DETECTED,
            )
        ]
        unresolved = last_session.unresolved_items if last_session else []
        next_objectives = (
            last_session.next_recommended_objectives if last_session else []
        )
        return ResumeState(
            learner=learner,
            concept_states=self.list_concept_states(learner_id),
            unresolved_gaps=list(unresolved),
            next_recommended_objectives=list(next_objectives),
            recent_misconceptions=misconceptions,
            last_session=last_session,
        )

    def session_close_snapshot(self, session_id: str) -> dict[str, Any]:
        """Hard progress data persisted at session end (AT-08 / Phase 5)."""
        session = self.get_session(session_id)
        evidence = self.list_evidence(learner_id=session.learner_id, session_id=session_id)
        events = self.list_events(session_id=session_id)
        assessed = sorted({item.concept_id for item in evidence})
        transitions = [
            event for event in events if event.event_type is EventType.MASTERY_TRANSITION
        ]
        misconceptions = [
            event
            for event in events
            if event.event_type
            in {EventType.MISCONCEPTION_DETECTED, EventType.MISCONCEPTION_CORRECTED}
        ]
        return {
            "session": session,
            "concepts_assessed": assessed,
            "state_transitions": transitions,
            "evidence": evidence,
            "misconceptions": misconceptions,
            "unresolved_gaps": session.unresolved_items,
            "takeaways": session.takeaways,
            "next_recommended_objectives": session.next_recommended_objectives,
            "objectives": self.list_session_objectives(session_id),
        }

    def _refresh_evidence_count(self, learner_id: str, concept_id: str) -> None:
        count = self.connection.execute(
            """
            SELECT COUNT(*) AS n FROM evidence
            WHERE learner_id = ? AND concept_id = ?
            """,
            (learner_id, concept_id),
        ).fetchone()["n"]
        self.connection.execute(
            """
            UPDATE learner_concept_state
            SET evidence_count = ?
            WHERE learner_id = ? AND concept_id = ?
            """,
            (count, learner_id, concept_id),
        )

    # --- Row mappers -------------------------------------------------------

    @staticmethod
    def _curriculum_from_row(row: sqlite3.Row) -> Curriculum:
        return Curriculum(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            authority=row["authority"],
            scope_description=row["scope_description"],
            status=CurriculumStatus(row["status"]),
        )

    @staticmethod
    def _node_from_row(row: sqlite3.Row) -> CurriculumNode:
        return CurriculumNode(
            id=row["id"],
            curriculum_id=row["curriculum_id"],
            parent_id=row["parent_id"],
            node_type=NodeType(row["node_type"]),
            title=row["title"],
            description=row["description"],
            scope_status=ScopeStatus(row["scope_status"]),
            sequence_order=row["sequence_order"],
        )

    @staticmethod
    def _prerequisite_from_row(row: sqlite3.Row) -> Prerequisite:
        return Prerequisite(
            id=row["id"],
            node_id=row["node_id"],
            prerequisite_node_id=row["prerequisite_node_id"],
            relationship_type=PrerequisiteType(row["relationship_type"]),
            rationale=row["rationale"],
        )

    @staticmethod
    def _concept_from_row(row: sqlite3.Row) -> Concept:
        return Concept(
            id=row["id"],
            canonical_name=row["canonical_name"],
            definition=row["definition"],
            explanation=row["explanation"],
            scope_tags=_json_loads(row["scope_tags"], []),
        )

    @staticmethod
    def _relationship_from_row(row: sqlite3.Row) -> ConceptRelationship:
        return ConceptRelationship(
            source_concept_id=row["source_concept_id"],
            target_concept_id=row["target_concept_id"],
            relationship_type=ConceptRelationshipType(row["relationship_type"]),
        )

    @staticmethod
    def _source_from_row(row: sqlite3.Row) -> Source:
        return Source(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            authority=row["authority"],
            retrieved_at=row["retrieved_at"],
            version_or_release=row["version_or_release"],
        )

    @staticmethod
    def _artifact_from_row(row: sqlite3.Row) -> KnowledgeArtifact:
        return KnowledgeArtifact(
            id=row["id"],
            concept_id=row["concept_id"],
            artifact_type=ArtifactType(row["artifact_type"]),
            content=row["content"],
            source_id=row["source_id"],
            authority_level=row["authority_level"],
        )

    @staticmethod
    def _criterion_from_row(row: sqlite3.Row) -> MasteryCriterion:
        return MasteryCriterion(
            id=row["id"],
            curriculum_node_id=row["curriculum_node_id"],
            criterion=row["criterion"],
            evidence_type=EvidenceType(row["evidence_type"]),
            minimum_strength=EvidenceStrength(row["minimum_strength"]),
        )

    @staticmethod
    def _state_from_row(row: sqlite3.Row) -> LearnerConceptState:
        return LearnerConceptState(
            learner_id=row["learner_id"],
            concept_id=row["concept_id"],
            status=ConceptStatus(row["status"]),
            confidence=row["confidence"],
            first_seen_at=row["first_seen_at"],
            last_assessed_at=row["last_assessed_at"],
            evidence_count=row["evidence_count"],
            misconception_flag=bool(row["misconception_flag"]),
            notes=row["notes"],
        )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> Evidence:
        return Evidence(
            id=row["id"],
            session_id=row["session_id"],
            learner_id=row["learner_id"],
            concept_id=row["concept_id"],
            evidence_type=EvidenceType(row["evidence_type"]),
            learner_text=row["learner_text"],
            evaluator_assessment=row["evaluator_assessment"],
            strength=EvidenceStrength(row["strength"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> LearningEvent:
        return LearningEvent(
            id=row["id"],
            session_id=row["session_id"],
            event_type=EventType(row["event_type"]),
            concept_id=row["concept_id"],
            evidence_id=row["evidence_id"],
            details=_json_loads(row["details"], {}),
            timestamp=row["timestamp"],
        )

    @staticmethod
    def _session_from_row(row: sqlite3.Row) -> Session:
        return Session(
            id=row["id"],
            learner_id=row["learner_id"],
            curriculum_id=row["curriculum_id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            status=SessionStatus(row["status"]),
            summary=row["summary"],
            takeaways=_json_loads(row["takeaways"], []),
            unresolved_items=_json_loads(row["unresolved_items"], []),
            next_recommended_objectives=_json_loads(row["next_recommended_objectives"], []),
        )

    @staticmethod
    def _session_objective_from_row(row: sqlite3.Row) -> SessionObjective:
        ending = row["ending_status"]
        return SessionObjective(
            session_id=row["session_id"],
            curriculum_node_id=row["curriculum_node_id"],
            starting_status=ConceptStatus(row["starting_status"]),
            ending_status=ConceptStatus(ending) if ending else None,
            evidence_summary=row["evidence_summary"],
            outcome=row["outcome"],
        )
