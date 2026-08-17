# Learning Ecosystem — POC Handoff

## Purpose

Build a learning system that does more than answer questions. It maintains a bounded curriculum and authoritative knowledge base, teaches using an explicit pedagogical protocol, evaluates demonstrated mastery, and persists learner/session state.

The first proof of concept (POC) is Salesforce Platform Developer I (PD1), focused on **Process Automation and Logic**.

## POC success criterion

A learner can enter a problem, be taught Socratically, have prerequisite gaps detected, receive targeted instruction only when needed, demonstrate mastery, and resume later without losing the learning state.

The POC must be able to explain:
- what was taught,
- what the learner demonstrated,
- what misconceptions occurred,
- what changed in learner state,
- what remains unresolved,
- what the next recommended learning objective is.

## Core architecture

- **Knowledge Base = truth**
- **Curriculum = scope, sequence, prerequisites, mastery criteria**
- **Tutor = pedagogy and interaction**
- **Learner Model = current demonstrated state**
- **Session Tracking = auditable learning history**
- **Learning Recorder = observes sessions and writes structured learning evidence/state**

## Files

- `architecture.md`
- `data_model.md`
- `tutor_protocol.md`
- `curriculum_poc.md`
- `knowledge_base_poc.md`
- `learner_state_example.json`
- `session_record_example.json`
- `builder_acceptance_tests.md`
- `implementation_plan.md`
