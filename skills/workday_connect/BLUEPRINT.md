# Workday Connect — Collector Blueprint

**Skill:** `workday_connect`
**Phase:** C (Blueprint / dry-run only)
**Status:** Blueprint complete — implementation deferred to Phase E
**Schema:** `schemas/baseline_assessment_schema.json` v2, `"platform": "workday"`

---

## Purpose

`workday_connect` is the data collector for Workday HCM/Finance tenant security assessments. It reads security configuration via Workday Web Services (WWS) SOAP API and pre-configured Reports-as-a-Service (RaaS) endpoints. It outputs a v2-schema-compliant assessment JSON that feeds into `oscal-assess` → `oscal_gap_map.py` → `sscf-benchmark` → `report-gen`.

The collector is **read-only**. It never modifies tenant configuration.

---

## Tenant Setup Requirements

### 1. Integration System User (ISU)

Create a dedicated ISU for the security collector:

| Field | Value |
|---|---|
| User Name | `svc_security_assessor@tenant` |
| Account Type | Integration System User |
| Disallow UI Sessions | **Enabled** (required) |
| Session Timeout | 60 minutes |

> WD-IAM-002 check: `Disallow UI Sessions` must be `true`. If the ISU used by the collector itself does not have this set, the collector raises a configuration warning in its own output.

### 2. Integration System Security Group (ISSG)

Create an ISSG and assign the ISU:

| Field | Value |
|---|---|
| Security Group Name | `SG_Security_Assessor` |
| Group Type | Integration System Security Group |
| Members | `svc_security_assessor` |

### 3. Required Domain Security Policy Permissions

Grant **Get** (read-only) on the following domain security policies. All grants are view-only. No Put/Modify permissions are required or permitted.

| Domain Security Policy | Used By Controls |
|---|---|
| Security Configuration | WD-IAM-001, WD-IAM-005, WD-IAM-006, WD-CON-001–006 |
| Integration System Security | WD-IAM-002, WD-IAM-008 |
| Maintain: Authentication Policies | WD-IAM-003, WD-CON-006 |
| Identity Provider | WD-IAM-004 |
| Workday Account | WD-IAM-007 |
| System Auditing | WD-LOG-001–005 |
| Security Logging | WD-LOG-001, WD-LOG-002 |
| Tenant Setup – Security | WD-CKM-001, WD-CKM-002 |
| Integration System User | WD-CKM-003 |
| Maintain: Business Process Security Policies | WD-IAM-006 |
| Manage: Business Process Definitions | WD-TDR-002 |
| Sensitive | WD-DSP-001, WD-DSP-004 |
| Worker Data: Workers | WD-DSP-001 |
| Security Groups | WD-IAM-005 |
| Maintain: Security Policies (Pending) | WD-GOV-001 |
| Set Up: Security | WD-GOV-002 |

### 4. RaaS Report Pre-Configuration (Optional)

Several controls are collected via pre-built Custom Reports configured as RaaS endpoints. If these reports are not pre-configured, the collector degrades gracefully (see Graceful Degradation section).

| Report Name (suggested) | Used By |
|---|---|
| `RPT_Inactive_Workday_Accounts` | WD-IAM-007 |
| `RPT_Failed_Signon_Events` | WD-LOG-003 |
| `RPT_Security_Config_Changes` | WD-GOV-002 |

---

## Authentication — OAuth 2.0 Client Credentials (Universal)

**No password credentials are used.** All calls — REST, SOAP, and RaaS — authenticate exclusively via OAuth 2.0 Client Credentials (machine-to-machine). Tokens expire in 3600 seconds and are scoped to the ISU's registered functional areas. This eliminates long-lived password credential exposure and enables token revocation without ISU password rotation.

```
Token URL:  https://{tenant}.workday.com/ccx/oauth2/{tenant}/token
Grant type: client_credentials
Scope:      Workday REST API (functional areas matching ISU ISSG permissions)
TLS:        1.2+ required. Enforced by Workday. All endpoints HTTPS-only.
```

### Transport by endpoint type

| Transport | Auth mechanism | Used for |
|---|---|---|
| **REST API v1** | OAuth 2.0 Bearer (`Authorization: Bearer {token}`) | Worker data, REST-native endpoints |
| **SOAP WWS** | OAuth 2.0 Bearer in HTTP header (`Authorization: Bearer {token}`) | Security config endpoints (auth policies, password rules, lockout, SAML) |
| **RaaS** | OAuth 2.0 Bearer (`Authorization: Bearer {token}`) | Pre-configured custom reports |

> Workday SOAP API accepts `Authorization: Bearer` as an alternative to WS-Security XML. This means `zeep` is not required — use `requests` with a Bearer header for all calls, including SOAP. Raw SOAP XML is simpler and avoids WS-Security token construction entirely.

### Why not WS-Security BasicAuth?

WS-Security UsernameToken (BasicAuth) embeds credentials in every SOAP envelope. This means:
- Long-lived ISU password transmitted on every request
- Credentials must be stored in `.env` or secrets manager but rotated manually
- No token revocation — password change required to revoke access
- SOAP envelope credential exposure in logs if envelope logging is enabled

OAuth 2.0 Client Credentials eliminates all of these: one client secret generates short-lived tokens; secret rotation does not require re-deployment; tokens can be revoked instantly without changing credentials.

### Environment variables

```
WD_TENANT              — Workday tenant ID (e.g., acme_dpt1)
WD_USERNAME            — ISU username for context (logging only; not used in auth)
WD_CLIENT_ID           — OAuth 2.0 API client ID (from Workday API Client registration)
WD_CLIENT_SECRET       — OAuth 2.0 client secret (never logged, never written to disk)
WD_TOKEN_URL           — OAuth token endpoint (default: https://{tenant}.workday.com/ccx/oauth2/{tenant}/token)
WD_API_VERSION         — WWS SOAP version, e.g. v40.0 (default: v40.0)
WD_BASE_URL            — optional override; defaults to https://{tenant}.workday.com
```

---

## Collection Method Taxonomy

Each control in `workday_catalog.json` declares its `collection-method` prop:

| Method | Auth | Transport | Collector behavior |
|---|---|---|---|
| `rest` | OAuth 2.0 Bearer | HTTPS JSON | GET `{base_url}/ccx/api/{rest-endpoint}`; parse JSON response |
| `soap` | OAuth 2.0 Bearer | HTTPS XML | POST raw SOAP envelope with `Authorization: Bearer {token}` header; no WS-Security XML |
| `raas` | OAuth 2.0 Bearer | HTTPS JSON | GET `{base_url}/ccx/service/customreport2/{tenant}/{report}?format=json` |
| `manual` | N/A | N/A | Return `not_applicable` with `collection_method_note` |

---

## Per-Control Collection Reference

### IAM Controls

| Control | Method | Service / Endpoint | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-IAM-001 | raas | — | `Security_Group_Domain_Access_Audit` | Domain assignments per group; flag sensitive-domain access |
| WD-IAM-002 | soap+oauth | Security_Configuration | Get_Workday_Account | `Disallow_UI_Sessions` per ISU |
| WD-IAM-003 | soap+oauth | Security_Configuration | Get_Authentication_Policies | `Multi_Factor_Authentication_Required` per policy |
| WD-IAM-004 | soap+oauth | Security_Configuration | Get_SAML_Setup | SSO active; `Require_Signed_Assertions` |
| WD-IAM-005 | raas | — | `Privileged_Role_Assignments_Audit` | Privileged group members; last recertification date |
| WD-IAM-006 | raas | — | `Business_Process_Security_Policy_Audit` | SOD check: initiator vs. approver group overlap |
| WD-IAM-007 | **rest** | `/staffing/v6/workers` | — | Active workers; filter `lastLogin` > 90d |
| WD-IAM-008 | soap+oauth | Security_Configuration | Get_API_Clients | OAuth client scope list; flag over-permissive |

### Configuration Hardening Controls

All CON controls use SOAP with OAuth 2.0 Bearer. Workday security config endpoints (password rules, lockout, session timeout, auth policies) have no REST API equivalent.

| Control | Service | Operation | Key Fields |
|---|---|---|---|
| WD-CON-001 | Security_Configuration | Get_Password_Rules | `Minimum_Password_Length`, complexity flags |
| WD-CON-002 | Security_Configuration | Get_Password_Rules | `Password_Expiration_Days`, `Password_History_Count` |
| WD-CON-003 | Security_Configuration | Get_Workday_Account (sample) | `Session_Timeout_Minutes` per account type |
| WD-CON-004 | Security_Configuration | Get_Password_Rules | `Lockout_Threshold`, `Lockout_Duration_Minutes` |
| WD-CON-005 | Security_Configuration | Get_IP_Range_Settings | `Allowed_IP_Ranges` list; empty = no restriction |
| WD-CON-006 | Security_Configuration | Get_Authentication_Policies | Policy count; verify all-user coverage |

### Logging and Monitoring Controls

| Control | Method | Service / Endpoint | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-LOG-001 | soap+oauth | Security_Configuration | Get_Workday_Account | `User_Activity_Logging_Enabled` tenant-wide flag |
| WD-LOG-002 | soap+oauth | Security_Configuration | Get_SignOn_Events | Last 30d sign-on audit; verify accessibility |
| WD-LOG-003 | raas | — | `RPT_Failed_Signon_Events` | Failed events by user in last 30d |
| WD-LOG-004 | soap+oauth | Security_Configuration | Get_Audit_Logs | Admin action log availability check |
| WD-LOG-005 | soap+oauth | Security_Configuration | Get_Audit_Retention_Settings | `Audit_Log_Retention_Days`; pass if ≥ 365 |

### Cryptography and Key Management Controls

| Control | Method | Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-CKM-001 | soap+oauth | Security_Configuration | Get_Tenant_Setup_Security | `Require_TLS_For_API`; TLS version enforced |
| WD-CKM-002 | manual | — | — | BYOK requires manual tenant admin confirmation |
| WD-CKM-003 | soap+oauth | Security_Configuration | Get_Integration_System_Users | ISU `Password_Last_Changed_Date`; flag if > 90d |

### Data Security and Privacy Controls

| Control | Method | Service / Endpoint | Operation | Key Fields |
|---|---|---|---|---|
| WD-DSP-001 | soap+oauth | Security_Configuration | Get_Security_Groups | Sensitive domain members (Compensation, SSN, Benefits) |
| WD-DSP-002 | soap+oauth | Security_Configuration | Get_Workday_Account | `Allow_Data_Export`, export permission flags |
| WD-DSP-003 | soap+oauth | Security_Configuration | Get_API_Clients | Integration scope breadth; flag `All_Workday_Data` |
| WD-DSP-004 | soap+oauth | Security_Configuration | Get_Security_Groups | PII domain access; group membership count |

### Threat Detection and Response Controls

| Control | Method | Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-TDR-001 | soap+oauth | Security_Configuration | Get_Authentication_Policies | `Failed_Login_Alert_Threshold`, alert routing |
| WD-TDR-002 | soap+oauth | Security_Configuration | Get_Business_Process_Definitions | Approval step count; flag single-approver chains |

### Governance and Compliance Controls

| Control | Method | Service / Endpoint | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-GOV-001 | soap+oauth | Security_Configuration | Get_Security_Policies | `Pending_Security_Policies`; pass if empty |
| WD-GOV-002 | raas | — | `RPT_Security_Config_Changes` | Changes in last 90d; flag entries with no approver |

---

## Graceful Degradation

### RaaS Not Pre-Configured

When a required RaaS report returns 404 or is inaccessible:

```json
{
  "control_id": "WD-IAM-007",
  "status": "not_applicable",
  "severity": "moderate",
  "evidence_source": "RaaS GET RPT_Inactive_Workday_Accounts",
  "observed_value": null,
  "remediation": "Pre-configure the RaaS report RPT_Inactive_Workday_Accounts and rerun the collector.",
  "platform_data": {
    "collection_method": "raas",
    "collection_method_note": "RaaS report not pre-configured. Control requires manual review.",
    "raas_available": false
  },
  "sscf_mappings": [...]
}
```

### Manual Controls

Controls with `collection_method: manual` always return `not_applicable` with an explanatory note. They are included in the output for completeness but excluded from automated pass/fail scoring:

```json
{
  "control_id": "WD-CKM-002",
  "status": "not_applicable",
  "evidence_source": "manual questionnaire required",
  "platform_data": {
    "collection_method": "manual",
    "collection_method_note": "BYOK configuration requires confirmation from Workday tenant administrator via manual questionnaire."
  }
}
```

### SOAP API Permission Denied

When the ISU lacks domain permission for a SOAP call, log the denial and return partial:

```json
{
  "control_id": "WD-DSP-001",
  "status": "partial",
  "evidence_source": "Get_Security_Groups — SOAP (permission denied)",
  "platform_data": {
    "collection_method": "soap",
    "soap_error": "PERMISSION_DENIED: Sensitive domain not granted to ISSG SG_Security_Assessor"
  }
}
```

---

## Dry-Run Mode

`--dry-run` prints the collection plan without making any API calls:

```
$ python3 skills/workday_connect/workday_connect.py --dry-run

DRY-RUN: Workday Connect Collection Plan
Tenant:  acme_dpt1
Auth:    SOAP WS-Security BasicAuth
Controls in scope: 30 (27 soap/raas, 1 manual, 2 raas-dependent)

  WD-IAM-001  soap   Get_Security_Groups                   ✓ in scope
  WD-IAM-002  soap   Get_Integration_System_Users          ✓ in scope
  WD-IAM-003  soap   Get_Authentication_Policies           ✓ in scope
  WD-IAM-004  soap   Get_Authentication_Policies           ✓ in scope
  WD-IAM-005  soap   Get_Security_Groups                   ✓ in scope
  WD-IAM-006  soap   Get_Business_Process_Security_Policies ✓ in scope
  WD-IAM-007  raas   RPT_Inactive_Workday_Accounts         * raas-dependent
  WD-IAM-008  soap   Get_API_Client_Scopes                 ✓ in scope
  ...
  WD-CKM-002  manual (questionnaire)                        - not_applicable
  ...

Would write: docs/oscal-salesforce-poc/generated/workday_raw.json
```

---

## Output Format

The collector writes a `baseline_assessment_schema.json` v2 compliant file:

```json
{
  "schema_version": "2.0",
  "assessment_id": "wd-assess-20260307-001",
  "platform": "workday",
  "oscal_catalog_ref": "config/workday/workday_catalog.json",
  "assessment_time_utc": "2026-03-07T12:00:00Z",
  "environment": "prod",
  "assessor": "workday-connect v0.1.0",
  "assessment_owner": "Jane Smith",
  "data_source": "workday-connect SOAP WWS v40.0 + RaaS",
  "ai_generated_findings_notice": "Findings produced by automated collector workday-connect. Requires human review before use in audit evidence.",
  "assessment_scope": {
    "controls_in_scope": 30,
    "controls_excluded": 1,
    "exclusion_reasons": ["WD-CKM-002 requires manual BYOK confirmation"]
  },
  "findings": [...]
}
```

Output file: `docs/oscal-salesforce-poc/generated/workday_raw.json`

---

## Pipeline Integration

```
workday_connect → oscal-assess → oscal_gap_map.py → sscf-benchmark → nist-review → report-gen
     ↓
workday_raw.json
```

The gap map step reads `workday_to_sscf_mapping.yaml` to enrich each finding with SSCF domain scores and CCM regulatory references. No changes to downstream pipeline are required — platform field is set to `"workday"` and the schema is v2 compliant.

---

## Implementation Notes (Phase E)

When implementing `workday_connect.py`:

1. **Auth first:** implement `get_oauth_token(client_id, client_secret, token_url) -> str` as the single entry point for all auth. Cache the token and refresh when it expires (check `expires_in`). Never log the token or secret.
2. **No `zeep`.** Use `requests` for all transports:
   - REST: `requests.get(url, headers={"Authorization": f"Bearer {token}"})`
   - SOAP: `requests.post(url, data=soap_xml_str, headers={"Authorization": f"Bearer {token}", "Content-Type": "text/xml"})` — no WS-Security XML in the envelope
   - RaaS: same as REST GET with Bearer header
3. **OSCAL-catalog-driven loop:** parse `workday_catalog.json` to enumerate controls. Read `collection-method`, `rest-endpoint`, `soap-service`, `soap-operation`, `raas-report` props. Do not hardcode control IDs.
4. **Dispatch by collection-method:** `rest` → REST handler; `soap` → SOAP handler with raw XML template; `raas` → RaaS handler; `manual` → immediate `not_applicable`.
5. Validate output against `schemas/baseline_assessment_schema.json` before writing.
6. Honor `--dry-run` flag by short-circuiting before any network call.
7. Never log `WD_CLIENT_SECRET`.

Key pip dependencies:
```
requests      # all HTTP (REST + SOAP + RaaS)
pyyaml        # mapping file parsing
jsonschema    # output validation
python-dotenv # env loading
lxml          # SOAP XML response parsing
```

### OAuth 2.0 token acquisition (pseudocode)

```python
import requests, time

_token_cache: dict = {}

def get_oauth_token(client_id: str, client_secret: str, token_url: str) -> str:
    now = time.time()
    if _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["access_token"]
    resp = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["access_token"]
```

### Mock server for development (no paid tenant needed)

See "Workday Dev Environment" section below — use WireMock or `pytest-responses` to stub SOAP/REST/RaaS endpoints without a live tenant.

---

## Workday Dev Environment (No Paid Tenant Required)

Workday **does not offer a free developer org** equivalent to Salesforce Developer Edition. Options for building and testing `workday_connect` without a paid tenant:

### Option 1: WireMock stub server (recommended for Phase E)

Run a local WireMock container that mimics Workday SOAP/REST/RaaS responses:

```bash
docker run -d --name workday-mock \
  -p 8080:8080 \
  -v ./tests/workday_mocks:/home/wiremock/mappings \
  wiremock/wiremock:latest
```

Create stub files in `tests/workday_mocks/` that return realistic Workday XML/JSON responses. The OAuth token endpoint, SOAP operations, and RaaS endpoints each get a stub mapping. The collector code is identical for real and mock — just set `WD_BASE_URL=http://localhost:8080`.

### Option 2: pytest-responses (unit tests only)

Use `responses` library to intercept HTTP calls at the test level. Good for per-function unit tests; not sufficient for full end-to-end dry-run.

### Option 3: Workday Learning / Community tenant

Workday provides a free **Workday Learning** tenant at `wd5.myworkday.com` for training. API access is severely restricted — useful for exploring the UI but not for SOAP/REST testing.

### Option 4: Implementation partner sandbox

If your organization uses a Workday implementation partner (Deloitte, Accenture, Alight), they typically have sandbox tenants with full API access. Request a time-boxed ISU/ISSG setup for integration testing.

### Recommended test approach for Phase E

1. Build against WireMock stubs (all 30 controls covered by stub XML/JSON files)
2. Add `pytest` tests that assert correct `status`, `observed_value`, `sscf_mappings` for each control
3. When a real Workday tenant becomes available: run `--dry-run` first, then live

Stub files go in: `tests/workday_mocks/` (create dir; add to `.gitignore` if stubs contain realistic-looking data)
