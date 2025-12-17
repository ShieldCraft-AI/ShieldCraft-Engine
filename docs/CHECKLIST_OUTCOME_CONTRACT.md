# CHECKLIST OUTCOME CONTRACT (AUTHORITATIVE)

This document is AUTHORITATIVE: the single source of truth for deriving checklist run outcomes.

Contract
--------
- The primary outcome of a checklist run MUST be derived exclusively by `derive_primary_outcome(checklist, events)`.
- Authoritative precedence: **REFUSAL** > **BLOCKED** > **ACTION** > **DIAGNOSTIC**.
- Persona annotations are advisory only and MUST NOT override the derived primary outcome.
- The function MUST return: `primary_outcome`, `refusal` (bool), `blocking_reasons` (list), and `confidence_level` (one of `high|medium|low`).
- No component may infer or mutate the `primary_outcome` outside of this contract; any attempts are recorded as diagnostic events.

Rationale
---------
Centralizing outcome derivation improves auditability and prevents duplicated heuristics appearing in multiple modules. The canonical function is deterministic and tests enforce idempotence and precedence.
