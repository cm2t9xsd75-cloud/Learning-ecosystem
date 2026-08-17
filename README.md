# Learning Ecosystem

POC for a bounded tutor: curriculum, knowledge base, learner model, session history, and a recorder that evaluates evidence without teaching.

The first POC is Salesforce Platform Developer I, focused on **Process Automation and Logic**. Specs live in `docs/` (see `docs/handoff.md`):

| Handoff file | Status |
| --- | --- |
| `architecture.md` | present |
| `data_model.md` | present |
| `curriculum_poc.md` | present |
| `knowledge_base_poc.md` | present |
| `learner_state_example.json` | present |
| `session_record_example.json` | present |
| `builder_acceptance_tests.md` | present |
| `implementation_plan.md` | present |
| `tutor_protocol.md` | present |

Phase 1 is relational persistence. Phase 2 seeds the bounded knowledge base and `poc-learner-001`. Phase 3 is the Socratic tutor runtime in `TutorRuntime`.

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

## Phase 2 — PD1 seed

```bash
python3 -m learning_ecosystem.seed learning_ecosystem.db
```

Loads the six POC clusters, source-traced knowledge artifacts, out-of-scope boundary nodes, and `poc-learner-001` with evidence-backed concept states. Resume starts at Flow bulk execution semantics; the collection-scope gap stays unresolved.

## Phase 3 — Tutor

`TutorRuntime` loads resume state, enforces the fundamentals gate, asks one Socratic/problem question at a time, and will not switch to direct instruction during application without permission.

## UI

```bash
python3 -m pip install -e ".[dev]"
python3 -m learning_ecosystem.web
```

Open http://127.0.0.1:8000

- **Learner:** resume or start a session, answer one question, reopen `POC-SESSION-001`
- **Admin:** curriculum map, concepts/sources, add a sourced artifact (does not invent required fundamentals)

## Out of scope for this phase

Vector retrieval and a full LLM-authored dialogue loop. The recorder evaluates and persists; it does not teach.
