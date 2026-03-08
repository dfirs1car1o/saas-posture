# Configuration Reference

All environment variables, configuration files, and YAML schemas used by this system.

---

## Environment Variables (`.env`)

### Required for Live Assessment

| Variable | Description | Example |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for all LLM calls | `sk-...` |
| `SF_USERNAME` | Salesforce login username | `admin@mycompany.com` |
| `SF_AUTH_METHOD` | Auth method: `jwt` (preferred) or `soap` | `jwt` |

### Salesforce Auth — JWT (Preferred)

| Variable | Description | Example |
|---|---|---|
| `SF_CONSUMER_KEY` | Connected app consumer key | `3MVG9...` |
| `SF_PRIVATE_KEY_PATH` | Path to JWT private key PEM file | `/home/user/sf.pem` |
| `SF_DOMAIN` | `login` for production, `test` for sandbox | `login` |

### Salesforce Auth — SOAP (Username/Password)

| Variable | Description | Example |
|---|---|---|
| `SF_PASSWORD` | Salesforce login password | `MyPassword123` |
| `SF_SECURITY_TOKEN` | Security token (appended to password for non-trusted IPs) | `AbcDef123...` |
| `SF_DOMAIN` | `login` for production, `test` for sandbox | `login` |

### Optional / Override

| Variable | Default | Description |
|---|---|---|
| `SF_INSTANCE_URL` | Auto-detected | Override if using a custom domain |
| `QDRANT_IN_MEMORY` | `1` | `1` = in-process (no Docker); `0` = use QDRANT_HOST |
| `QDRANT_HOST` | unset | Qdrant container hostname (only if `QDRANT_IN_MEMORY=0`) |
| `QDRANT_PORT` | `6333` | Qdrant container port |
| `MEMORY_ENABLED` | `0` | Set to `1` to enable Mem0 session memory |
| `LLM_MODEL_ORCHESTRATOR` | `gpt-5.3-chat-latest` | Override orchestrator model |
| `LLM_MODEL_ANALYST` | `gpt-5.3-chat-latest` | Override analyst/assessor model |
| `LLM_MODEL_REPORTER` | `gpt-4o-mini` | Override reporter model |

### Azure OpenAI Government (FedRAMP / IL5)

To route all calls through Azure OpenAI instead of the public OpenAI API, set:

| Variable | Description |
|---|---|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | e.g., `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_VERSION` | e.g., `2025-01-01-preview` |

---

## Configuration Files

### OSCAL Catalogs

| File | Platform | Controls | Format |
|---|---|---|---|
| `config/oscal-salesforce/sbs_catalog.json` | Salesforce | 45 SBS controls | OSCAL 1.1.2 |
| `config/workday/workday_catalog.json` | Workday | 30 WSCC controls | OSCAL 1.1.2 |
| `config/sscf/sscf_catalog.json` | Platform-agnostic | 14 SSCF controls | OSCAL 1.1.2 |
| `config/ccm/ccm_v4.1_oscal_ref.yaml` | Reference | 197 CCM v4.1 controls | Reference pointer |

### SSCF and CCM Mapping Files

| File | Purpose |
|---|---|
| `config/oscal-salesforce/sbs_to_sscf_mapping.yaml` | SBS control → SSCF domain + control ID |
| `config/workday/workday_to_sscf_mapping.yaml` | Workday control → SSCF domain + control ID |
| `config/sscf/sscf_to_ccm_mapping.yaml` | SSCF control → CCM v4.1 controls + regulatory highlights |
| `config/sscf_control_index.yaml` | Legacy SSCF control index (superseded by sscf_catalog.json) |

### `config/oscal-salesforce/sbs_to_sscf_mapping.yaml` schema

```yaml
version: 1
framework: CSA_SSCF
platform: salesforce
control_overrides:
  SBS-AUTH-001:
    - sscf_domain: identity_access_management
      sscf_control_id: SSCF-IAM-001
      mapping_strength: direct
      rationale: "..."
```

### `config/sscf/sscf_to_ccm_mapping.yaml` schema

```yaml
SSCF-IAM-001:
  ccm_controls:
    - id: IAM-01
      domain: Identity & Access Management
      regulatory_highlights:
        - SOC2_CC6.1
        - HIPAA_164.312d
        - ISO27001_A.9.4.2
```

---

## Output Schema

### `schemas/baseline_assessment_schema.json` (v2)

Platform-agnostic assessment schema. Supports Salesforce, Workday, and future platforms.

**Top-level required fields:**

```json
{
  "schema_version": "2.0",
  "assessment_id": "wd-assess-20260307-001",
  "platform": "workday",
  "assessment_time_utc": "2026-03-07T12:00:00Z",
  "assessor": "workday-connect v0.1.0",
  "oscal_catalog_ref": "config/workday/workday_catalog.json",
  "assessment_owner": "Jane Smith",
  "data_source": "workday-connect SOAP WWS v40.0 + RaaS",
  "findings": [...]
}
```

**Per-finding required fields:**

```json
{
  "control_id": "WD-IAM-001",
  "status": "fail",
  "severity": "critical",
  "evidence_source": "RaaS Security_Group_Domain_Access_Audit",
  "sscf_mappings": [
    {
      "sscf_domain": "identity_access_management",
      "sscf_control_id": "SSCF-IAM-002",
      "mapping_strength": "direct",
      "mapping_confidence": "high",
      "rationale": "...",
      "ccm_controls": [
        { "id": "IAM-01", "domain": "Identity & Access Management", "regulatory_highlights": ["SOC2_CC6.1"] }
      ]
    }
  ]
}
```

**Status values:** `pass` | `fail` | `partial` | `not_applicable`

**Severity values:** `critical` | `high` | `moderate` | `low`

**Platform values:** `salesforce` | `workday` | `servicenow`

---

## Workday Environment Variables

Required when running `workday-connect` (Phase E):

| Variable | Description |
|---|---|
| `WD_TENANT` | Workday tenant ID (e.g., `acme_dpt1`) |
| `WD_CLIENT_ID` | OAuth 2.0 API client ID (from Workday API Client registration) |
| `WD_CLIENT_SECRET` | OAuth 2.0 client secret (never logged) |
| `WD_TOKEN_URL` | Token endpoint (`https://{tenant}.workday.com/ccx/oauth2/{tenant}/token`) |
| `WD_API_VERSION` | WWS SOAP version (default: `v40.0`) |
| `WD_BASE_URL` | Override base URL (default: `https://{tenant}.workday.com`); set to `http://localhost:8080` for WireMock |

Auth method: **OAuth 2.0 Client Credentials** — no password credentials. All transports (REST, SOAP, RaaS) use short-lived Bearer tokens.

---

## Gap Analysis JSON Format

Input to `oscal_gap_map.py`:

```json
{
  "assessment_id": "string",
  "findings": [
    {
      "control_id": "SBS-AUTH-001",
      "status": "fail",
      "severity": "critical",
      "owner": "security-team",
      "evidence_ref": "collector://salesforce/dev/SBS-AUTH-001/snapshot-2026-03-02"
    }
  ]
}
```

If `control_id` starts with `SBS-`, the gap map does a direct lookup — `control_mapping.yaml` is not needed.

---

## Agent Frontmatter Schema

Every file in `agents/` has YAML frontmatter:

```yaml
---
name: agent-name
description: |
  What this agent does and when to invoke it.
model: gpt-5.3-chat-latest
tools:
  - sfdc_connect_collect
  - oscal_assess_assess
proactive_triggers:
  - "Weekly drift check"
---
```

**Model options:**
- `gpt-5.3-chat-latest` — orchestrator, collector, assessor, nist-reviewer, security-reviewer, sfdc-expert
- `gpt-4o-mini` — reporter (cost-efficient for templated narrative output)

---

## pyproject.toml Sections

```toml
[project.scripts]
# CLI entry points installed by pip install -e .
sfdc-connect = "skills.sfdc_connect.sfdc_connect:cli"
oscal-assess  = "skills.oscal_assess.oscal_assess:cli"
sscf-benchmark = "skills.sscf_benchmark.sscf_benchmark:cli"
nist-review   = "skills.nist_review.nist_review:cli"
agent-loop    = "harness.loop:cli"
report-gen    = "skills.report_gen.report_gen:cli"

[tool.setuptools.packages.find]
# Required for editable install to find skills.*
include = ["skills*", "harness*"]

[tool.uv]
# Dev deps (not installed by plain pip — must install explicitly in CI)
dev-dependencies = [
  "ruff>=0.6.0",
  "pytest>=8.0.0",
  "pytest-mock>=3.14.0",
  "diagrams>=0.23.4",
  "zizmor>=1.0.0",
  "pip-licenses>=5.0.0",
  "cyclonedx-bom>=4.0.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```
