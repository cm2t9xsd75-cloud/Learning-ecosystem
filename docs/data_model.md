# Data Model — POC

A relational model is recommended for the POC because curriculum, prerequisites, concepts, learners, and sessions have explicit relationships. Vector retrieval can be added later but should not be the source of truth.

## Curriculum
- id
- name
- version
- authority
- scope_description
- status

## CurriculumNode
Represents domain/topic/fundamental/objective.

- id
- curriculum_id
- parent_id
- node_type
- title
- description
- scope_status
- sequence_order

`node_type`:
- domain
- topic
- fundamental
- objective

## Prerequisite
- id
- node_id
- prerequisite_node_id
- relationship_type
- rationale

`relationship_type`:
- required
- recommended

## Concept
- id
- canonical_name
- definition
- explanation
- scope_tags

## ConceptRelationship
- source_concept_id
- target_concept_id
- relationship_type

Types:
- prerequisite
- contains
- contrasts_with
- depends_on
- example_of
- commonly_confused_with

## Source
- id
- title
- url
- authority
- retrieved_at
- version_or_release

## KnowledgeArtifact
- id
- concept_id
- artifact_type
- content
- source_id
- authority_level

Types:
- definition
- example
- counterexample
- misconception
- scenario

## MasteryCriterion
- id
- curriculum_node_id
- criterion
- evidence_type
- minimum_strength

Evidence types:
- recall
- explanation
- application
- transfer
- correction
- synthesis

## Learner
- id
- display_name

## LearnerConceptState
- learner_id
- concept_id
- status
- confidence
- first_seen_at
- last_assessed_at
- evidence_count
- misconception_flag
- notes

Status enum:
`not_started, introduced, novice, developing, demonstrated, mastered, needs_review`

## Evidence
- id
- session_id
- learner_id
- concept_id
- evidence_type
- learner_text
- evaluator_assessment
- strength
- created_at

Strength:
- weak
- moderate
- strong

## LearningEvent
- id
- session_id
- event_type
- concept_id
- evidence_id
- details
- timestamp

Event types:
- concept_introduced
- misconception_detected
- misconception_corrected
- mastery_evidence
- mastery_transition
- frustration_detected
- direct_instruction_requested
- prerequisite_gap
- out_of_scope_dependency

## Session
- id
- learner_id
- curriculum_id
- started_at
- ended_at
- status
- summary
- takeaways
- unresolved_items
- next_recommended_objectives

## SessionObjective
- session_id
- curriculum_node_id
- starting_status
- ending_status
- evidence_summary
- outcome

## Modeling principle

`LearnerConceptState.status` is maintained state, not the only durable learning record.

The auditable source is:
- Evidence
- LearningEvent
- Session history

This allows the system to explain *why* a learner is considered mastered.
