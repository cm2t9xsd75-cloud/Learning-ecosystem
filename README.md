# Learning Ecosystem

POC for a bounded tutor: curriculum, knowledge base, learner model, session history, and a recorder that evaluates evidence without teaching.

Phase 1 implements relational persistence only. Curriculum seeding, tutor runtime, and the recorder loop come later.

## Phase 1 — Persistence

SQLite stores the data-model tables:

| Area | Tables |
| --- | --- |
| Curriculum | `curriculum`, `curriculum_node`, `prerequisite`, `mastery_criterion` |
| Knowledge | `concept`, `source`, `knowledge_artifact` |
| Learner | `learner`, `learner_concept_state` |
| Audit | `evidence`, `learning_event`, `session`, `session_objective` |

`LearnerConceptState.status` is maintained state. **Evidence**, **LearningEvent**, and **Session** history are the auditable source of truth (AT-13, AT-14).

Mastery cannot be written from a single repeated definition (AT-07). Session close persists assessed concepts, transitions, evidence, misconceptions, takeaways, unresolved gaps, and the next objective (AT-08), including the Flow bulk-execution gap (AT-10). Resume loads that state (AT-09).

## Setup

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

```python
from learning_ecosystem import LearningEcosystemRepository, create_database

repo = LearningEcosystemRepository(create_database("learning_ecosystem.db"))
```

## Out of scope for this phase

Vector retrieval, tutor dialogue, recorder evaluation, and PD1 curriculum seed data (Phase 2).
