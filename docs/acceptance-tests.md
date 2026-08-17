# Builder Acceptance Tests

## AT-01 — Bounded curriculum
The Tutor cannot silently introduce an out-of-scope concept as a required fundamental.

## AT-02 — Fundamental gate
The Tutor does not advance through a critical prerequisite without mastery evidence or explicit scaffolding.

## AT-03 — Socratic default
Given a solvable misconception, the Tutor asks a targeted question before supplying the answer.

## AT-04 — Direct instruction permission
When frustration is evident during application, the Tutor asks permission before switching to direct instruction unless the learner explicitly requested it.

## AT-05 — Context preservation
The Tutor explicitly signals a scenario/context reset.

## AT-06 — Misconception classification
The Recorder distinguishes:
- technical error
- ambiguity
- context mismatch
- knowledge gap
- corrected misconception

## AT-07 — Evidence-backed mastery
A concept cannot become mastered from a single repeated definition.

## AT-08 — Session persistence
At session end, persist:
- concepts assessed
- state transitions
- evidence
- misconceptions
- unresolved gaps
- learner takeaways
- next recommended objective

## AT-09 — Resume behavior
A future session loads learner state and does not unnecessarily reteach mastered concepts.

## AT-10 — POC Flow gap
The unresolved Flow bulk-execution gap persists into the next session.

## AT-11 — Source traceability
Every authoritative knowledge-base claim can be traced to a source/version.

## AT-12 — Tutor/Recorder separation
The Recorder may evaluate and persist state but may not independently teach or redefine curriculum.

## AT-13 — Explainability
Given a learner concept marked `mastered`, the system can return the evidence that justified the state.

## AT-14 — State downgrade without history loss
A mastered concept may move to `needs_review` when contradictory evidence appears, without deleting prior mastery evidence.
