**Governance Spine (v1)**

Purpose:

- Establish authoritative policies for spec contracts, verification, and release gating within ShieldCraft Engine.

Core responsibilities:

- Maintain and publish authoritative contracts and invariants (see `CONTRACTS.md`).
- Owns decision logs and rationale for opt-in guards (e.g., TAC enforcement).
- Onboard and document owners for verification, persona, and engine contracts.

Key artifacts and references:

- `docs/governance/CONTRACTS.md` — concrete contracts and required artifacts.
- `docs/governance/VERIFICATION_SPINE.md` — verification responsibilities and artifacts.
- `docs/persona/PERSONA_PROTOCOL.md` — persona governance and non-interference rules.

Change management:

- All governance changes must be recorded in `docs/governance/decision_log.md` and audited via `scripts/audit_docs.py`.
