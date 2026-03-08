---
name: sfdc-connect
description: Authenticates to a Salesforce org and extracts configuration data via REST and Metadata API for security assessment. Read-only. Never writes to the org.
cli: skills/sfdc-connect/sfdc-connect
model_hint: sonnet
---

# sfdc-connect

Connects to any Salesforce org and extracts security-relevant configuration data for OSCAL/SBS/SSCF assessment.

## Usage

```bash
skills/sfdc-connect/sfdc-connect --help
skills/sfdc-connect/sfdc-connect --org <alias-or-instance-url> --scope <scope> --out <output-json-path>
```

## Flags

```
--org            Org alias (from SFDX auth) or instance URL. Required.
--scope          What to collect. Required. One of:
                   auth               Identity settings, SSO, MFA policy
                   access             Profiles, permission sets, connected apps
                   event-monitoring   EventMonitoringInfo, storage utilization
                   transaction-security TransactionSecurityPolicy metadata
                   integrations       Named credentials, remote site settings
                   deployments        DeployRequest history, change sets
                   data               Field-level security, sharing rules (metadata only)
                   oauth              OAuth policies, connected app scopes
                   files              ContentDistribution settings
                   secconf            Health check baseline score
                   all                All of the above in sequence
--out            Output JSON file path. Required.
--env            Environment label: dev|test|prod. Default: dev.
--timeout        API timeout in seconds. Default: 60.
--dry-run        Print what would be collected without calling API.
```

## Output Shape

Each scope produces a JSON object conforming to the collector finding shape:
```json
{
  "org": "<alias>",
  "env": "<dev|test|prod>",
  "collected_at_utc": "<ISO timestamp>",
  "scope": "<scope-name>",
  "findings": [
    {
      "control_id": "<SBS-XXX-NNN>",
      "status": "<pass|fail|partial|not_applicable>",
      "severity": "<critical|high|medium|low>",
      "evidence_source": "sfdc-connect://...",
      "observed_value": "<what was found>",
      "expected_value": "<what the baseline requires>"
    }
  ]
}
```

## Authentication

sfdc-connect reads credentials from environment variables (`.env` file or shell). It never accepts credentials as CLI flags and never writes them to any file.

Required env vars:
```bash
SF_USERNAME=your.name@yourorg.com
SF_PASSWORD=YourPassword
SF_SECURITY_TOKEN=YourToken   # appended to password for IP-unrestricted login
SF_DOMAIN=login               # use "test" for sandbox orgs
```

Copy `.env.example` to `.env` and fill in values before first run.

## If You Are Unsure

Call --help first. This CLI loads its own reference documentation and will tell you exactly what flags are available and what each scope collects. Do not guess flag names.

## Composing With Other Skills

```bash
# Collect auth scope, pipe summary to assessor
skills/sfdc-connect/sfdc-connect --org myorg --scope auth --out /tmp/auth.json
skills/oscal-assess/oscal-assess --gap-analysis /tmp/auth.json ...
```

## What This Skill Will Not Do

- It will not perform any write operation on the org.
- It will not store org credentials in any file.
- It will not collect record-level data (Contacts, Accounts, Opportunities).
- It will not run if the org alias is not already authenticated via SFDX.
