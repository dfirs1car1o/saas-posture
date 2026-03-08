# Architecture Overview

## Design Philosophy

**OpenClaw**: CLIs not MCPs. Every tool is a Python CLI callable from the shell. No hidden MCP state. No Docker-required infrastructure. The agent loop is an OpenAI `tool_use` ReAct loop.

---

## System Diagram

```
┌───────────────────────────────────────────────────────────────┐
│              agent-loop (gpt-5.3-chat-latest orchestrator)                │
│              OpenAI tool_use ReAct loop, max 14 turns         │
└──────┬──────────┬──────────┬──────────┬──────────┬───────────┘
       │          │          │          │          │
 ┌─────▼──┐ ┌────▼───┐ ┌────▼──┐ ┌─────▼────┐ ┌──▼────────┐
 │sfdc-   │ │oscal-  │ │oscal_ │ │sscf-     │ │nist-      │
 │connect │ │assess  │ │gap_map│ │benchmark │ │review     │
 │(collect)│ │(assess)│ │(map)  │ │(score)   │ │(validate) │
 └─────┬──┘ └────┬───┘ └────┬──┘ └─────┬────┘ └──┬────────┘
       │         │           │          │          │
  sfdc_raw  gap_analysis  backlog   sscf_report  nist_review
  .json      .json         .json     .json        .json
       └─────────┴───────────┴──────────┴──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │   report-gen        │
                          │  (gpt-4o-mini)      │
                          │  app-owner MD       │
                          │  security MD + DOCX │
                          └────────────────────┘
```

---

## Agent Architecture

### 7 Agents

| Agent | Model | Role | Tools |
|---|---|---|---|
| `orchestrator` | gpt-5.3-chat-latest | Routes tasks, manages the ReAct loop, quality gates | All 5 CLI tools |
| `collector` | gpt-5.3-chat-latest | Extracts Salesforce org config via REST/Metadata API | sfdc-connect |
| `assessor` | gpt-5.3-chat-latest | Maps findings to OSCAL/SBS/SSCF controls | oscal-assess, oscal_gap_map |
| `reporter` | gpt-4o-mini | Generates DOCX/MD governance outputs | report-gen |
| `nist-reviewer` | gpt-5.3-chat-latest | Validates outputs against NIST AI RMF | None (text analysis) |
| `security-reviewer` | gpt-5.3-chat-latest | AppSec + DevSecOps review of CI/CD and skills | None (text analysis) |
| `sfdc-expert` | gpt-5.3-chat-latest | On-call Salesforce/Apex specialist | None (text + code) |

### Model Assignment Rationale

- **gpt-5.3-chat-latest** for all analytical and orchestration work: complex routing, API extraction, control mapping, regulatory QA, security review
- **gpt-4o-mini** for templated output: structured data → formatted report (low-complexity, high-volume, cost-efficient)
- **No tools for review/expert agents**: text-only analysis prevents accidental state modification

> **Note:** This repo migrated from Anthropic Claude models to OpenAI models following a government supply chain risk designation that classified Claude as a restricted dependency. Azure OpenAI Government is supported as a drop-in via `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`.

---

## 5 Skills (CLI Tools)

| Skill | Binary | Purpose |
|---|---|---|
| `sfdc-connect` | `skills/sfdc_connect/sfdc_connect.py` | Authenticates to Salesforce org via REST/JWT; collects SecuritySettings, Auth providers, Permission Sets, Network Access, Connected Apps, Profiles |
| `oscal-assess` | `skills/oscal_assess/oscal_assess.py` | Evaluates 45 SBS controls against collected org data; produces findings with status (pass/fail/partial/not_applicable) and severity |
| `sscf-benchmark` | `skills/sscf_benchmark/sscf_benchmark.py` | Maps SBS findings to SSCF domains; calculates domain scores and overall posture (RED/AMBER/GREEN) |
| `nist-review` | `skills/nist_review/nist_review.py` | Validates assessment outputs against NIST AI RMF 1.0 (govern/map/measure/manage); issues pass/flag/block verdict |
| `report-gen` | `skills/report_gen/report_gen.py` | Generates audience-specific outputs: app-owner Markdown, security Markdown + DOCX |

---

## Data Flow

```
sfdc-connect collect
    → sfdc_raw.json (Salesforce org snapshot)
        → oscal-assess assess
            → gap_analysis.json (45 SBS control findings)
                → oscal_gap_map.py
                    → backlog.json (remediation items)
                        → sscf-benchmark benchmark
                            → sscf_report.json (domain scorecard)
                                → nist-review assess
                                    → nist_review.json (governance verdict)
                                        → report-gen generate
                                            → {org}_remediation_report.md (app-owner)
                                            → {org}_security_assessment.md + .docx (security)
```

All outputs land in `docs/oscal-salesforce-poc/generated/<org>/<date>/`.

---

## Report Structure

Reports are assembled from deterministic Python-rendered sections plus a focused LLM narrative:

```
[Gate banner]                  ← ⛔ block / 🚩 flag if NIST verdict requires it
Executive Scorecard            ← overall score + severity × status matrix  [HARNESS]
OSCAL Framework Provenance     ← catalog → profile → component → CCM chain [HARNESS]
Domain Posture (ASCII chart)   ← bar chart of all SSCF domain scores       [HARNESS]
Immediate Actions              ← top-10 critical/fail findings sorted       [HARNESS]
Executive Summary + Analysis   ← LLM narrative (2 sections only)           [LLM]
Full Control Matrix            ← complete sorted findings table             [HARNESS]
Plan of Action & Milestones    ← POAM-IDs, owners, due dates, status       [HARNESS]
Not Assessed Controls          ← out-of-scope appendix for auditors        [HARNESS]
NIST AI RMF Governance Review  ← function table + blockers + recs          [HARNESS]
```

---

## Memory Architecture

Session memory uses **Mem0 + Qdrant**. By default:
- `QDRANT_IN_MEMORY=1` — in-process Qdrant (no Docker needed)
- Memory stores: org alias, prior assessment score, critical findings
- Each new assessment loads prior org context as prefix to the first user message
- This allows the orchestrator to detect regression ("score dropped from 48% to 34%")

For persistent cross-session memory, run a Qdrant container and set `QDRANT_HOST=localhost`.

---

## Control Mapping Architecture

```
Platform Config (Salesforce or Workday)
       ↓
  Platform OSCAL Catalog
    SBS: config/oscal-salesforce/sbs_catalog.json    (45 controls, OSCAL 1.1.2)
    WD:  config/workday/workday_catalog.json          (30 controls, OSCAL 1.1.2)
       ↓
  Platform → SSCF mapping
    SBS: config/oscal-salesforce/sbs_to_sscf_mapping.yaml
    WD:  config/workday/workday_to_sscf_mapping.yaml
       ↓
  SSCF Catalog (config/sscf/sscf_catalog.json — 14 controls, OSCAL 1.1.2)
       ↓
  SSCF → CCM v4.1 bridge (config/sscf/sscf_to_ccm_mapping.yaml)
       ↓
  CCM v4.1 (config/ccm/ccm_v4.1_oscal_ref.yaml — 197 controls)
       ↓
  Regulatory crosswalk: SOX · HIPAA · SOC2 TSC · ISO 27001 · NIST 800-53 · PCI DSS · GDPR
       ↓
  Domain Scores (IAM, Data Security, Configuration Hardening, etc.)
```

---

## Key File Locations

| Location | Purpose |
|---|---|
| `mission.md` | Agent identity + authorized scope (loaded every session) |
| `AGENTS.md` | Canonical agent roster |
| `agents/orchestrator.md` | Orchestrator routing table, quality gates, finish() trigger |
| `config/sscf/sscf_catalog.json` | SSCF OSCAL 1.1.2 catalog (14 controls) |
| `config/sscf/sscf_to_ccm_mapping.yaml` | SSCF→CCM v4.1 bridge |
| `config/oscal-salesforce/sbs_catalog.json` | SBS OSCAL 1.1.2 catalog (45 controls) |
| `config/workday/workday_catalog.json` | Workday OSCAL 1.1.2 catalog (30 controls) |
| `config/workday/workday_to_sscf_mapping.yaml` | Workday→SSCF mappings |
| `schemas/baseline_assessment_schema.json` | v2 platform-agnostic assessment schema |
| `skills/workday_connect/BLUEPRINT.md` | Workday connector specification |
| `docs/oscal-salesforce-poc/generated/` | All assessment outputs |
| `docs/architecture.png` | Auto-generated reference architecture diagram |
