# Change Control + Rollback Runbook

## Purpose
Provide a repeatable process so releases are traceable and reversible.

## Required for Every Change
1. PR includes:
   - scope summary
   - risk level (`low`, `medium`, `high`)
   - rollback steps
   - RV steps and expected output
2. `CHANGELOG.md` updated in `[Unreleased]`.
3. Terraform plan attached for infra changes.
4. Approval from at least one reviewer outside the author.
5. For phase or architecture changes, run `docs/agents/brutal-critic-agent.md` and attach results using `docs/templates/brutal-critic-review-template.md`.

## Release Process
1. Merge PR to main after checks pass.
2. Trigger `terraform-apply` workflow in `dev`.
3. Execute RV checks and record results.
4. Promote to next environment only after RV sign-off.
5. If brutal-critic verdict is `reject`, promotion is blocked.

## Rollback Process
1. Identify last known-good git tag/commit.
2. Revert offending commit(s) with new PR.
3. Re-run `terraform-apply` from reverted main state.
4. Re-deploy previous known-good container image tag.
5. Re-run smoke checks and close incident note.

## Minimum RV Commands
- API health:
```bash
curl -fsS https://<orchestrator-fqdn>/health
```
- Triage smoke:
```bash
curl -fsS -X POST https://<orchestrator-fqdn>/triage \\
  -H \"content-type: application/json\" \\
  -d '{\"case_text\":\"suspicious powershell launcher observed\"}'
```
- Terraform drift check:
```bash
cd infra/terraform\nterraform plan -var-file=envs/dev.tfvars
```

## Tagging Policy
- `vMAJOR.MINOR.PATCH` tags for each promoted release.
- Example:
  - `v0.1.0` foundation
  - `v0.2.0` provider integration
  - `v0.3.0` Copilot integration
