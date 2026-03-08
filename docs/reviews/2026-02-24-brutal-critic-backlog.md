# Brutal-Critic Remediation Backlog (2026-02-24)

Source audit: `docs/reviews/2026-02-24-brutal-critic-audit.md`  
Purpose: track blocking and follow-on remediation items for staged implementation.

## Backlog Status Legend
- `open`: not started
- `in_progress`: active implementation
- `blocked`: waiting dependency/decision
- `done`: completed and validated

## Priority Backlog

| ID | Priority | Status | Finding | Target Phase | Owner | Done Criteria |
|---|---|---|---|---|---|---|
| BC-001 | P0 | open | Protect public triage path with enforced auth/API gateway policy (not just input validation). | Phase 1 | Platform Security + Security Team | Direct app ingress is non-public or strictly gated; JWT/authz enforced; unauthorized requests rejected in RV checks. |
| BC-002 | P1 | open | Harden Key Vault and Storage network posture (private access model, purge protection, deny-by-default). | Phase 1 | Platform Security | `public_network_access_enabled` disabled where applicable; purge protection enabled; private endpoint pattern and policy checks merged. |
| BC-003 | P1 | open | Replace weak apply safety with stronger deployment gates (plan integrity + approval controls). | Phase 1 | DevSecOps | Apply no longer relies on blind `-auto-approve`; plan artifact and approval path enforced; CI blocks unsafe promotion. |
| BC-004 | P1 | open | Replace provider stubs with real clients and tested fallback path. | Phase 2 | App Engineering | Real provider calls implemented; timeout/retry/fallback behavior tested; forced-failure fallback test passes in CI. |
| BC-005 | P1 | open | Add APIM enterprise policy baseline (auth, schema validation, rate limits, threat controls). | Phase 2B | Platform Security | APIM policy artifacts versioned; policy checks in CI; RV proves reject behavior for invalid/unauthorized requests. |
| BC-006 | P1 | open | Codify SIFT image release controls (immutable versioning, provenance, rollback workflow). | Phase 4A | DFIR Platform | Image release process documented + automated; signed provenance and rollback to prior image version validated. |
| BC-007 | P2 | open | Establish mapping governance for OSCAL/SBS-to-SSCF (approval workflow, confidence enforcement). | Phase 1/2 | BSS + GRC | Mapping changes require approval; low-confidence mappings flagged; governance report excludes unapproved mappings. |
| BC-008 | P2 | open | Implement SaaS collectors to produce schema-compliant evidence outputs (Salesforce first). | Phase 2 | BSS SaaS Assurance | At least one read-only collector emits valid `baseline_assessment_schema.json` output with evidence refs. |
| BC-009 | P2 | open | Add runtime policy exception governance API/logging for model/tool policy overrides. | Phase 2/3 | App Engineering + Security Team | Exception create/approve/expire path auditable; policy decisions linked to case/correlation ID. |
| BC-010 | P2 | open | Define cost guardrails and budget enforcement telemetry beyond static policy caps. | Phase 5 | FinOps + Platform | Alert thresholds, budget report, and enforcement actions documented and tested in RV. |

## Execution Notes
- Sequence by risk: `BC-001` → `BC-002`/`BC-003` → `BC-004`/`BC-005` → remaining P2s.
- No promotion to production phases while any `P0` or unresolved `P1` required for target phase remains open.
- Every backlog closure requires:
  1. Code/config changes merged.
  2. RV evidence attached.
  3. Changelog entry recorded.

