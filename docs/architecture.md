# Learning Ecosystem Architecture

## 1. System overview

```text
                    ┌───────────────────────────┐
                    │        TUTOR AGENT        │
                    │                           │
                    │ Socratic default          │
                    │ Mastery learning          │
                    │ Problem-based learning    │
                    │ Direct instruction gate   │
                    └─────────────┬─────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
        CURRICULUM           LEARNER MODEL       SESSION TRACKING
             │                    │                    │
             └─────────────┬──────┴─────────────┬──────┘
                           ▼                    ▼
                    KNOWLEDGE BASE       LEARNING RECORDER
```

## 2. Component responsibilities

### Knowledge Base
The authoritative body of subject knowledge.

Contains:
- concepts
- definitions
- relationships
- examples
- counterexamples
- misconceptions
- authoritative sources
- scope tags

It answers: **What is true?**

### Curriculum
The educational structure.

Contains:
- domains
- topics
- fundamentals
- prerequisites
- learning objectives
- mastery criteria
- allowed problem types
- in-scope/out-of-scope boundaries

It answers: **What should be learned, and in what dependency order?**

### Tutor Agent
The runtime teacher.

Responsibilities:
- inspect learner state
- select an appropriate objective
- ask questions
- generate problems
- detect frustration
- scaffold
- request permission before direct instruction
- stay inside curriculum scope
- create opportunities for mastery evidence

It answers: **How should the learner learn this?**

### Learner Model
Persistent state of demonstrated knowledge.

A concept should not become "mastered" from one correct answer. State must be supported by evidence.

Suggested states:
- not_started
- introduced
- novice
- developing
- demonstrated
- mastered
- needs_review

### Session Tracking
Auditable history of learning.

Captures:
- session metadata
- objectives
- concepts assessed
- learner responses/evidence
- misconceptions
- interventions
- mastery transitions
- unresolved gaps
- takeaways
- next objectives

### Learning Recorder
A state-tracking/evaluation component, not a second teacher.

It:
1. observes the session,
2. identifies learning events,
3. maps evidence to curriculum concepts,
4. compares evidence against mastery criteria,
5. proposes learner-state transitions,
6. writes session outcomes.

It must not invent curriculum scope or independently teach.

## 3. Runtime loop

```text
START SESSION
    ↓
Load learner state + relevant curriculum
    ↓
Select objective/problem
    ↓
Tutor interaction
    ↓
Evidence generated
    ↓
Learning Recorder evaluates evidence
    ↓
Update learner state/session events
    ↓
Mastery?
 ┌──┴───┐
 No    Yes
 │      │
Targeted  Advance to
prereq    next objective
 │
Return to problem
    ↓
SESSION SUMMARY
```

## 4. Critical boundary rule

The Tutor must never silently redefine the curriculum.

If a required concept is outside the bounded knowledge base, classify it as:

`OUT_OF_SCOPE_DEPENDENCY`

Then:
- route to an authorized prerequisite, or
- ask to expand scope.

This protects the learner from surprise fundamentals during frustration.

## 5. Separation of concerns

```text
Curriculum      defines what mastery means
Knowledge Base  supplies authoritative truth
Tutor           creates learning interactions
Recorder        evaluates evidence
Learner Model   stores current state
Session Log     stores history
```
