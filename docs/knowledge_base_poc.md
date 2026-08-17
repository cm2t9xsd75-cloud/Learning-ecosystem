# PD1 Knowledge Base Seed — Process Automation & Logic

This is a seed knowledge base for the POC, not a complete Salesforce reference.

## Concept: Bulkification

Definition:
Design automation so that platform/database operations do not scale linearly with the number of records being processed within a transaction.

Common misconception:
"Apex is automatically bulkified."

Correction:
Apex supports bulk patterns, but code can still be non-bulkified. Bulkification is a design/implementation practice.

Mastery evidence:
- identifies DML in loops
- identifies SOQL in loops
- explains record volume vs platform-operation volume
- proposes collection-based processing

## Concept: SOQL Query Count vs Returned Records

Definition:
These are separate resource dimensions.

Common misconception:
"A query returning more than 150 records exceeds the SOQL query limit."

Correction:
Query count measures executed queries. Returned-row volume is a separate concern.

## Concept: Relationship SOQL

Definition:
SOQL can traverse supported Salesforce relationships.

Example:

```apex
SELECT Name, Account.Name
FROM Contact
WHERE Account.AnnualRevenue > 1000000
```

Underlying model:
Contact exposes a relationship to Account, allowing parent fields to be traversed.

## Concept: Transaction

Definition:
A transaction is a unit of Salesforce work that shares an execution context, applicable limits, and commit/rollback behavior.

Key distinction:
Separate automation components do not automatically mean separate transactions.

## Concept: Asynchronous Execution

Definition:
Work is deferred so it executes outside the current synchronous execution path.

Tradeoff:
The initiating transaction can commit before deferred work completes, introducing eventual consistency.

## Concept: `$Record__Prior`

Purpose:
Used to reason about the previous state of the triggering record and detect transitions.

Important distinction:
Previous-value context can detect a field transition; it does not aggregate all triggering records or create a new transaction.

## Concept: Flow Record-Triggered Execution

Seed model:
Multiple triggering records can produce multiple Flow interviews within a transaction. Salesforce can bulkify compatible database operations across interviews.

Critical nuance:
Interview-local state is not automatically one shared collection across all interviews.

POC gap:
The exact mechanics of collection scope, Get Records, and Update Records bulk execution must be represented explicitly in the knowledge base.

## Scope boundary

In scope:
- Flow vs Apex
- SOQL/SOSL/DML
- bulkification
- governor limits
- transactions
- Flow execution
- triggers/classes
- order of execution
- recursion/cascading

Out of scope unless explicitly added:
- OAuth architecture
- unrelated integration architecture
- mobile development
- advanced packaging
- broad DevOps architecture
- unrelated clouds

## Source policy

Every authoritative technical fact should eventually store:
- source URL
- source title
- authority
- retrieval date
- Salesforce release/version where relevant

Prefer official Salesforce sources for platform behavior.
