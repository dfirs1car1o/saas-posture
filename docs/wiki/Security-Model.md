# Security Model

The security model for this system is defined in `mission.md` and enforced at multiple layers.

---

## Core Rules (Non-Negotiable)

| Rule | Enforcement |
|---|---|
| Read-only against Salesforce | Coded in sfdc-connect; no write methods exist |
| No credentials in code or logs | bandit, gitleaks, CodeQL in CI; CodeRabbit review |
| Evidence stays in `docs/oscal-salesforce-poc/generated/` | Path validation in all CLIs |
| All findings need `assessment_id` + `generated_at_utc` | Schema validation in orchestrator |
| Critical/fail gate on live runs | `harness/loop.py` lines 246–256 |
| NIST AI RMF validation before output | nist-reviewer agent, final step |

---

## Quality Gates (Layered)

### Gate 1: Python critical/fail gate (`harness/loop.py`)
- **When:** Live runs only (not dry-run)
- **Bypass:** `--approve-critical` flag
- **Blocks:** Writing final output if `status=fail AND severity=critical`

### Gate 2: Orchestrator prompt gate (`agents/orchestrator.md`)
- **When:** All modes including dry-run
- **Bypass:** Task prompt includes dry-run bypass note
- **Blocks:** Output delivery if nist-reviewer gap, schema violation, or security-reviewer CRITICAL/HIGH

### Gate 3: CI/CD gates (`.github/workflows/`)
- **When:** Every PR and push to main
- **Bypass:** Admin merge only
- **Blocks:** Merge if bandit HIGH, CVE, GPL dep, gitleaks hit, zizmor HIGH, actionlint error, pytest failure

---

## Sensitive Data Handling

| Data type | Where it lives | What to never do |
|---|---|---|
| Salesforce credentials | `.env` (gitignored) | Put in code, commit, log |
| OPENAI_API_KEY | `.env` (gitignored) | Put in code, commit, log to stdout |
| WD_CLIENT_SECRET | `.env` (gitignored) | Put in code, commit, log |
| Salesforce config data | `docs/oscal-salesforce-poc/generated/<org>/` | Write to `/tmp`, commit, put in /tmp |
| Assessment findings | `docs/oscal-salesforce-poc/generated/<org>/` | Write to external systems without approval |

The `gitleaks` CI job scans full commit history on every PR. If a credential is ever committed, rotate it immediately.

---

## Escalation Paths

| Finding | Who is notified | Blocks what |
|---|---|---|
| `critical/fail` Salesforce control | Human (via loop exit + message) | Live assessment output |
| NIST AI RMF gap | Human (via orchestrator gate) | All assessment output |
| security-reviewer CRITICAL | Human (via orchestrator gate) | CI merge |
| security-reviewer HIGH | Human (via orchestrator gate) | CI merge |
| gitleaks credential detection | CI failure → PR author | Merge to main |
| bandit HIGH finding | CI failure → PR author | Merge to main |
| CVE in dependency | CI failure → PR author | Merge to main |

---

## What the Security Reviewer Checks

The `security-reviewer` agent (6th agent, text-only) reviews:

**Workflow files:**
- Expression injection (`${{ github.event.*.body }}` in `run:` blocks)
- Overly broad permissions
- Third-party actions not pinned to SHA
- `pull_request_target` + fork checkout (critical injection vector)
- Secret interpolation in `run:` steps

**Python CLI tools:**
- `subprocess.run(..., shell=True)` with any non-static input (HIGH)
- HTTP calls without `timeout=` (MEDIUM)
- Path traversal from CLI args
- SOQL injection (user input in queries)
- Credential logging in exception handlers

**Harness:**
- `sys.exit()` outside CLI entrypoints
- Unvalidated tool_use input passed to subprocess

**Agent definitions:**
- Instructions that override `mission.md` scope
- Prompt injection vectors
- Overly broad tool grants

**Always-flag anti-patterns:**
`shell=True` / `eval()` / `exec()` / `pickle.loads()` on untrusted input / `yaml.load()` without SafeLoader / `os.system()` with variables / credentials in committed files / `verify=False` on TLS

---

## Audit Trail

Every assessment produces:

| Field | Purpose |
|---|---|
| `assessment_id` | Unique ID for this run (format: `sfdc-assess-<org>-<env>-loop`) |
| `generated_at_utc` | ISO 8601 timestamp of when findings were generated |
| `evidence_ref` | URI pointing to the collector snapshot (`collector://salesforce/<env>/<control_id>/snapshot-<date>`) |
| `loop_result.json` | Full metadata: org, env, dry_run, turns, score, critical_fails, output paths |

The `schemas/baseline_assessment_schema.json` enforces these fields on all output.
