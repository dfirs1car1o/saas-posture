# Agent Reference

All 7 agents in the system. Each has a definition file in `agents/` with YAML frontmatter and a full role description.

---

## Orchestrator

| Field | Value |
|---|---|
| **File** | `agents/orchestrator.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | All 5 CLI skills |
| **Invoked by** | Human (entry point for all requests) |

**Role:** Routes all tasks. Manages the ReAct loop. Enforces quality gates. Assembles final output.

**Does NOT:**
- Call `sfdc-connect` and interpret raw results itself (delegates to collector)
- Write report content (delegates to reporter)
- Assume defaults — always asks if org/env/audience is unclear

**Quality gates it enforces:**
1. Any `critical/fail` finding → blocks output on live runs (bypass: `--approve-critical`)
2. nist-reviewer blocking gap → blocks output
3. Output schema violation → blocks output
4. Missing `assessment_id` or `generated_at_utc` → blocks output
5. security-reviewer CRITICAL/HIGH on CI change → blocks merge

**Routing table:**

| Request | Sequence |
|---|---|
| Full org assessment | sfdc-connect → oscal-assess → gap_map → sscf-benchmark → nist-review → report-gen × 2 |
| Gap map from existing JSON | gap_map → sscf-benchmark → report-gen |
| Report refresh | report-gen × 2 |
| NIST AI RMF validation | nist-reviewer (text) |
| CI/CD security review | security-reviewer (text) |
| New skill added | security-reviewer (text) → review subprocess dispatcher |
| Control research | assessor context, no tools |
| Apex / complex SFDC question | sfdc-expert (on-call) |

---

## Collector

| Field | Value |
|---|---|
| **File** | `agents/collector.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | `sfdc-connect` |
| **Invoked by** | Orchestrator |

**Role:** Authenticates to Salesforce and extracts org configuration. Parses the raw JSON from `sfdc-connect` and packages it for the assessor.

**Critical constraint:** Never logs credentials. Never queries record-level data (Contacts, Accounts, Opportunities). Read-only.

---

## Assessor

| Field | Value |
|---|---|
| **File** | `agents/assessor.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | `oscal-assess`, `oscal_gap_map` |
| **Invoked by** | Orchestrator |

**Role:** Maps collected Salesforce config to the 45 SBS controls. Runs the rule engine. Produces findings with status and severity. Maps findings to SSCF controls via gap map.

**Control assignment:** Conservative — only marks `pass` when definitively met. Ambiguous → `partial`.

---

## Reporter

| Field | Value |
|---|---|
| **File** | `agents/reporter.md` |
| **Model** | `gpt-4o-mini` |
| **Tools** | `report-gen` |
| **Invoked by** | Orchestrator (after assessor completes) |

**Role:** Generates governance outputs. Two runs per assessment: once for `app-owner` (Markdown), once for `security` (Markdown + DOCX).

**Why gpt-4o-mini?** Report generation is narrative output from structured data — low complexity, high volume. gpt-4o-mini is the fastest and most cost-efficient model for this task.

---

## NIST Reviewer

| Field | Value |
|---|---|
| **File** | `agents/nist-reviewer.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | None (text analysis only) |
| **Invoked by** | Orchestrator (final validation step) |

**Role:** Validates all outputs against the NIST AI RMF (AI Risk Management Framework). Checks for:
- Transparency documentation
- Bias and fairness considerations in AI-generated findings
- Accountability trail (assessment_id, generated_at_utc, evidence_ref)
- Risk categorization alignment

**Verdicts:** `pass` → `flag` (review required) → `block` (do not distribute). A `block` verdict prepends ⛔ banner to both reports; `flag` prepends 🚩.

**Why no tools?** Review is analytical. Giving it tool access would risk accidental state modification.

---

## Security Reviewer

| Field | Value |
|---|---|
| **File** | `agents/security-reviewer.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | None (text analysis only) |
| **Invoked by** | Orchestrator on CI/CD, workflow, or skill changes |

**Role:** Expert AppSec + DevSecOps reviewer. Reviews:
- `.github/workflows/` — expression injection, permissions, unpinned actions
- `skills/**/*.py` — subprocess safety, SOQL injection, HTTP timeouts, path traversal
- `harness/**/*.py` — control flow leaks, tool input validation, credential logging
- `agents/**/*.md` — scope creep, bypass instructions, prompt injection
- `pyproject.toml` — version ranges, license conflicts, deprecated packages

**Severity levels:** CRITICAL, HIGH, MEDIUM, LOW. CRITICAL/HIGH block merge.

**Anti-patterns it always flags** (never acceptable):
1. `subprocess.run(..., shell=True)` with any non-static argument
2. `eval()` or `exec()`
3. `pickle.loads()` on untrusted input
4. `yaml.load()` without `Loader=yaml.SafeLoader`
5. `os.system()` with variable content
6. Credentials in any committed file
7. `allow_redirects=True` on user-supplied URLs
8. `verify=False` on TLS connections

---

## SFDC Expert

| Field | Value |
|---|---|
| **File** | `agents/sfdc-expert.md` |
| **Model** | `gpt-5.3-chat-latest` |
| **Tools** | None (text analysis + code generation only) |
| **Invoked by** | Orchestrator when findings have `needs_expert_review=true` |

**Role:** On-call Salesforce specialist. Handles complex questions that the assessor cannot resolve through CLI tools — Apex code review, Flow/Process Builder security issues, SOQL injection patterns, and Connected App scope analysis. See `apex-scripts/README.md` for Apex security patterns.

**Outputs:** Plain-text analysis and Apex code snippets (never executed — for human review only).

---

## Adding a New Agent

1. Create `agents/<name>.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-agent
   description: What it does and when to use it
   model: gpt-5.3-chat-latest
   tools: []
   ---
   ```
2. Add `AgentConfig` to `harness/agents.py`
3. Add row to `AGENTS.md`
4. Add routing entry to `agents/orchestrator.md`
5. Run `security-reviewer` on the new agent file before merging
