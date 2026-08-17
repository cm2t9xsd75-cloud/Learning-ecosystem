# Salesforce PD1 POC Curriculum

## Scope

Certification: Salesforce Platform Developer I
POC domain: **Process Automation and Logic**

This POC intentionally does not attempt to model the entire certification.

## Cluster 1 — Declarative vs Programmatic Automation

Must understand:
- capabilities of Flow
- capabilities of Apex
- complexity tradeoffs
- maintainability tradeoffs
- transaction requirements
- bulk-processing implications
- when synchronous completion is required

Mastery evidence:
- selects Flow/Apex from requirements rather than preference
- rejects "Apex is automatically bulkified"
- can explain when either tool could be valid

## Cluster 2 — Bulkification

Must understand:
- record volume vs operation volume
- collections
- SOQL in loops
- DML in loops
- bulk query patterns
- bulk DML patterns

Mastery evidence:
- identifies SOQL/DML in loops
- explains why operations scaling linearly with records is brittle
- proposes collection-based processing

## Cluster 3 — Governor Limits

Must understand:
- limits are transaction-scoped resource controls
- SOQL query count
- returned record count as separate dimension
- DML statement count
- affected record count as separate dimension
- why multi-tenant architecture drives limits

Current POC learner status: **developing**

## Cluster 4 — SOQL

Must understand:
- SELECT
- FROM
- WHERE
- filtering
- relationship traversal
- parent relationship queries
- query context vs record context

Current POC learner status: **mastered at current scope**

## Cluster 5 — Transactions

Must understand:
- transaction boundary
- synchronous execution
- asynchronous execution
- commit behavior
- eventual consistency
- cascaded automation in a transaction

Current POC learner status: **mastered at conceptual scope**

## Cluster 6 — Flow Bulk Execution Semantics

Must understand:
- record-triggered Flow interviews
- multiple interviews within a transaction
- element-level bulkification
- `$Record`
- `$Record__Prior`
- collection scope
- Get Records behavior
- Update Records behavior
- transaction/governor implications

Current POC learner status: **developing**

Known learner gap:
The learner understands the need for bulk processing but does not yet have a complete model of Flow interview-local state versus cross-interview bulk database execution.

## Cluster 7 — Apex Classes and Triggers

Not yet tested.

## Cluster 8 — Exceptions and Error Handling

Not yet tested.

## Cluster 9 — Order of Execution / Recursion / Cascading

Not yet tested.

## Dependency graph

```text
Salesforce data model
        ↓
       SOQL
        ↓
    Collections
        ↓
   Bulkification
        ↓
 Governor limits
        ↓
   Transactions
        ↓
Flow/Apex execution semantics
        ↓
Order of execution / recursion
```
