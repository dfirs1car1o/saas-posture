# Brutal-Critic Audit (2026-02-24)

## Verdict
`approve-with-conditions`

The program foundation is strong, but it is not deployment-ready for sensitive SaaS/DFIR operations until blocking controls are implemented.

## Critical Findings (Ordered by Severity)

1. `[P1] Key Vault and storage network exposure defaults are too permissive for sensitive workflows.`
- Impact: increased risk of unauthorized access paths to secrets/evidence.
- Likelihood: medium-high once external integrations expand.
- Evidence: baseline Terraform enables public access defaults and lacks private endpoint enforcement.
- Remediation:
  - Add private endpoints for Key Vault/Storage.
  - Disable public network access where feasible.
  - Add deny-by-policy controls in Azure Policy baseline.

2. `[P1] APIM is on Consumption SKU with no explicit enterprise auth/policy bundle yet.`
- Impact: weak central enforcement for tool and model traffic.
- Likelihood: high if Copilot/custom connectors are enabled before hardening.
- Evidence: APIM provisioned, but no mandatory inbound policy pack (JWT, schema validation, request limits, threat protection).
- Remediation:
  - Add APIM policy artifacts and CI checks.
  - Require Entra/JWT validation for all sensitive routes.
  - Add per-role quotas and payload schema enforcement.

3. `[P1] No policy-as-code gate for Terraform security posture.`
- Impact: insecure infrastructure can pass CI unnoticed.
- Likelihood: high as infrastructure grows.
- Evidence: CI includes fmt + plan + lint, but no `tfsec`/`checkov` or policy gate.
- Remediation:
  - Add Terraform security scanning to PR gates.
  - Block merge on high/critical findings unless exception approved.

4. `[P1] SIFT image pipeline exists, but image build/release control is not yet codified.`
- Impact: inconsistent images, difficult rollback and provenance gaps.
- Likelihood: medium.
- Evidence: image factory scaffold and scripts exist, but no enforced image signing/provenance release flow.
- Remediation:
  - Add image build pipeline with immutable version tags.
  - Add image provenance metadata and approval gate before worker rollout.

5. `[P2] Role-model/tool policies are static with no runtime exception/override governance API.`
- Impact: operational friction and ad-hoc policy bypass risk.
- Likelihood: medium.
- Evidence: YAML policies are present, but no formal policy decision service/audit endpoint.
- Remediation:
  - Add signed policy release process.
  - Add policy decision logs and exception linkage.

6. `[P2] Baseline control IDs are provisional and not yet governed as enterprise canonical IDs.`
- Impact: audit confusion and control traceability drift.
- Likelihood: medium.
- Evidence: provisional SSCF control index explicitly marked for later normalization.
- Remediation:
  - Approve a control-ID governance process and freeze v1 control dictionary.

7. `[P2] SaaS baseline assessment flow is defined but collector implementations are not yet present.`
- Impact: program cannot produce evidence-backed compliance status.
- Likelihood: high until collectors are built.
- Evidence: schemas/catalogs exist without platform collector code.
- Remediation:
  - Implement read-only collectors for Salesforce, ServiceNow, Workday.
  - Output findings strictly against `baseline_assessment_schema.json`.

## Gaps by Pillar

- Security:
  - Missing private networking hardening for sensitive services.
  - Missing APIM policy pack and Terraform security gates.

- Reliability:
  - No defined deployment health gates for MCP gateway and SIFT worker path.
  - No deterministic image promotion flow for SIFT artifacts.

- Cost:
  - No usage guardrails for model routing budgets in runtime enforcement.
  - Limited cost telemetry and threshold alert definitions.

- Operational Excellence:
  - Strong governance docs exist, but automation for exception lifecycle is not yet integrated.
  - Collector pipeline and evidence freshness checks missing.

- Performance:
  - No performance SLO baselines yet for triage and tool execution APIs.

## Rollback Risk

- Primary backout path: git revert + terraform apply to last known-good state.
- Failure points:
  - If data plane controls change without migration planning, rollback can strand evidence access.
  - If APIM policy rollout is partial, service traffic can fail open/closed unexpectedly.
- Preconditions not validated:
  - No automated rollback drill for image version fallback and MCP routing fallback.

## Required Changes Before Proceeding (Blocking)

1. Add Terraform security scanner gate (`tfsec` or `checkov`) in CI.
2. Add APIM policy baseline and enforce auth/schema/rate rules.
3. Implement private endpoint strategy for Key Vault/Storage in dev design.
4. Define SIFT image release policy (versioning, provenance, rollback).
5. Implement at least one read-only SaaS collector (Salesforce first) producing schema-compliant output.

## Fast Wins (Non-blocking)

1. Add `CODEOWNERS` entries for `config/saas_baseline_controls/**` and `schemas/**`.
2. Add `make` or task runner commands for `lint`, `validate`, `audit`.
3. Add a baseline scorecard generator from assessment JSON outputs.
4. Add monthly model budget report from role policy and usage telemetry.

## Confidence
`high`

Rationale: repository content shows strong governance direction and structure, and findings are based on concrete gaps between documented intent and implemented enforcement.

