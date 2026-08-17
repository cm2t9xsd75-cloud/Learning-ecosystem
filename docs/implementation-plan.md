# Builder Implementation Plan

## Phase 1 — Persistence
Implement relational tables for:
- Curriculum
- CurriculumNode
- Prerequisite
- Concept
- Source
- KnowledgeArtifact
- MasteryCriterion
- Learner
- LearnerConceptState
- Evidence
- LearningEvent
- Session
- SessionObjective

## Phase 2 — Seed the POC
Load only:
- declarative vs programmatic automation
- bulkification
- SOQL
- governor limits
- transactions
- Flow bulk execution

Do not expand curriculum until the POC loop works.

## Phase 3 — Tutor runtime
Implement:
1. load learner state
2. identify next objective/prerequisite
3. run Socratic interaction
4. generate evidence
5. invoke mastery checks
6. move into problem-based learning after fundamentals
7. enforce frustration/direct-instruction gate

## Phase 4 — Learning Recorder
Evaluate learner responses in short batches or per turn:
- map response to concept(s)
- classify evidence
- detect misconceptions
- propose state transition
- persist LearningEvent/Evidence

Keep Tutor and Recorder responsibilities separate.

## Phase 5 — Session close
Generate both:
- hard progress data
- concise learner-facing takeaways

## Phase 6 — Resume
Start a new session from:
- learner concept states
- unresolved gaps
- next recommended objective
- recent misconception history

## Phase 7 — Validation
Replay the existing POC learning session and verify the system independently derives:
- bulkification = mastered
- SOQL = mastered at current scope
- governor limits = developing
- transactions = mastered at conceptual scope
- Flow bulk execution = developing
- next objective = Flow bulk execution semantics

## Later, not POC
- vector/semantic retrieval
- spaced repetition
- larger problem bank
- richer analytics
- adaptive review scheduling
- multiple curricula/domains
