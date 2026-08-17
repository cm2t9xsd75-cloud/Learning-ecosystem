-- Learning Ecosystem POC — Phase 1 persistence schema.
-- LearnerConceptState.status is maintained state.
-- Evidence, LearningEvent, and Session history are the auditable source of truth.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS curriculum (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    authority TEXT NOT NULL,
    scope_description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived'))
);

CREATE TABLE IF NOT EXISTS curriculum_node (
    id TEXT PRIMARY KEY,
    curriculum_id TEXT NOT NULL REFERENCES curriculum(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES curriculum_node(id) ON DELETE SET NULL,
    node_type TEXT NOT NULL CHECK (node_type IN ('domain', 'topic', 'fundamental', 'objective')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    scope_status TEXT NOT NULL CHECK (scope_status IN ('in_scope', 'out_of_scope')),
    sequence_order INTEGER NOT NULL,
    UNIQUE (curriculum_id, parent_id, sequence_order)
);

CREATE TABLE IF NOT EXISTS prerequisite (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES curriculum_node(id) ON DELETE CASCADE,
    prerequisite_node_id TEXT NOT NULL REFERENCES curriculum_node(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('required', 'recommended')),
    rationale TEXT NOT NULL,
    CHECK (node_id <> prerequisite_node_id),
    UNIQUE (node_id, prerequisite_node_id)
);

CREATE TABLE IF NOT EXISTS concept (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    explanation TEXT NOT NULL,
    scope_tags TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS concept_relationship (
    source_concept_id TEXT NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    target_concept_id TEXT NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (
        relationship_type IN (
            'prerequisite',
            'contains',
            'contrasts_with',
            'depends_on',
            'example_of',
            'commonly_confused_with'
        )
    ),
    PRIMARY KEY (source_concept_id, target_concept_id, relationship_type),
    CHECK (source_concept_id <> target_concept_id)
);

CREATE TABLE IF NOT EXISTS source (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    authority TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    version_or_release TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_artifact (
    id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL CHECK (
        artifact_type IN ('definition', 'example', 'counterexample', 'misconception', 'scenario')
    ),
    content TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES source(id),
    authority_level TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mastery_criterion (
    id TEXT PRIMARY KEY,
    curriculum_node_id TEXT NOT NULL REFERENCES curriculum_node(id) ON DELETE CASCADE,
    criterion TEXT NOT NULL,
    evidence_type TEXT NOT NULL CHECK (
        evidence_type IN ('recall', 'explanation', 'application', 'transfer', 'correction', 'synthesis')
    ),
    minimum_strength TEXT NOT NULL CHECK (minimum_strength IN ('weak', 'moderate', 'strong'))
);

CREATE TABLE IF NOT EXISTS learner (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session (
    id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES learner(id) ON DELETE CASCADE,
    curriculum_id TEXT NOT NULL REFERENCES curriculum(id),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'abandoned')),
    summary TEXT,
    takeaways TEXT NOT NULL DEFAULT '[]',
    unresolved_items TEXT NOT NULL DEFAULT '[]',
    next_recommended_objectives TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS learner_concept_state (
    learner_id TEXT NOT NULL REFERENCES learner(id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (
        status IN (
            'not_started',
            'introduced',
            'novice',
            'developing',
            'demonstrated',
            'mastered',
            'needs_review'
        )
    ),
    confidence REAL,
    first_seen_at TEXT NOT NULL,
    last_assessed_at TEXT,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    misconception_flag INTEGER NOT NULL DEFAULT 0 CHECK (misconception_flag IN (0, 1)),
    notes TEXT,
    PRIMARY KEY (learner_id, concept_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    learner_id TEXT NOT NULL REFERENCES learner(id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concept(id),
    evidence_type TEXT NOT NULL CHECK (
        evidence_type IN ('recall', 'explanation', 'application', 'transfer', 'correction', 'synthesis')
    ),
    learner_text TEXT NOT NULL,
    evaluator_assessment TEXT NOT NULL,
    strength TEXT NOT NULL CHECK (strength IN ('weak', 'moderate', 'strong')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_event (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'concept_introduced',
            'misconception_detected',
            'misconception_corrected',
            'mastery_evidence',
            'mastery_transition',
            'frustration_detected',
            'direct_instruction_requested',
            'prerequisite_gap',
            'out_of_scope_dependency'
        )
    ),
    concept_id TEXT REFERENCES concept(id),
    evidence_id TEXT REFERENCES evidence(id),
    details TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_objective (
    session_id TEXT NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    curriculum_node_id TEXT NOT NULL REFERENCES curriculum_node(id),
    starting_status TEXT NOT NULL CHECK (
        starting_status IN (
            'not_started',
            'introduced',
            'novice',
            'developing',
            'demonstrated',
            'mastered',
            'needs_review'
        )
    ),
    ending_status TEXT CHECK (
        ending_status IS NULL OR ending_status IN (
            'not_started',
            'introduced',
            'novice',
            'developing',
            'demonstrated',
            'mastered',
            'needs_review'
        )
    ),
    evidence_summary TEXT,
    outcome TEXT,
    PRIMARY KEY (session_id, curriculum_node_id)
);

CREATE INDEX IF NOT EXISTS idx_curriculum_node_curriculum
    ON curriculum_node (curriculum_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_prerequisite_node
    ON prerequisite (node_id);
CREATE INDEX IF NOT EXISTS idx_concept_relationship_source
    ON concept_relationship (source_concept_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_artifact_concept
    ON knowledge_artifact (concept_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_artifact_source
    ON knowledge_artifact (source_id);
CREATE INDEX IF NOT EXISTS idx_mastery_criterion_node
    ON mastery_criterion (curriculum_node_id);
CREATE INDEX IF NOT EXISTS idx_session_learner
    ON session (learner_id, started_at);
CREATE INDEX IF NOT EXISTS idx_evidence_learner_concept
    ON evidence (learner_id, concept_id, created_at);
CREATE INDEX IF NOT EXISTS idx_learning_event_session
    ON learning_event (session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_learning_event_concept
    ON learning_event (concept_id, event_type);
