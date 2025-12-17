# TEMPLATE NON-AUTHORITY CONTRACT (AUTHORITATIVE)

This contract ensures templates are pluggable, versioned, and non-authoritative. Templates are presentation artifacts and must not be used to infer or assert authority over checklist outcomes.

Principles
- Templates provide rendering and placeholder defaults only; they must never inject BLOCKER or REFUSAL outcomes or otherwise alter authoritative decisioning.
- Template metadata (name/version) is recorded for provenance only and must not change primary outcomes or authority ceilings.
- Missing templates must fallback deterministically and must not escalate authority.

Enforcement
- Tests assert checklist invariance across template versions and that templates cannot generate authority outcomes.
- Any evidence of template-induced authority must fail deterministic tests and be addressed immediately.

Signed: Governance
Date: 2025-12-17
