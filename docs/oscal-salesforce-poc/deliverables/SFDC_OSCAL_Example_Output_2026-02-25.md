# Salesforce OSCAL Example Output for Business Review

Date: 2026-02-25  
Program: SaaS Risk Program - Salesforce OSCAL POC

## Purpose
This document shows the type of governance output that can be produced from a legitimate Salesforce gap-analysis file mapped through the OSCAL pipeline.

## Input and Processing Scope
- Input gap file: `docs/oscal-salesforce-poc/examples/gap-analysis-salesforce-collector-mock.json`
- Control catalog: `docs/oscal-salesforce-poc/generated/sbs_controls.json` (45 SBS controls)
- Mappings applied:
  - `config/oscal-salesforce/control_mapping.yaml`
  - `config/oscal-salesforce/sbs_to_sscf_mapping.yaml`
- Pipeline script: `scripts/oscal_gap_map.py`

## End-to-End Outcome Summary
- Total controls in scope: 45
- Findings evaluated: 45
- Mapped findings: 45
- Unmapped findings: 0
- Invalid mapping entries: 0

### Status Breakdown
- Pass: 24
- Partial: 12
- Fail: 9
- Not applicable: 0

### Severity Distribution
- Critical: 9
- High: 19
- Medium: 14
- Low: 3

### Mapping Quality
- Mapping confidence: 100% high confidence (45/45)
- SSCF traceability: included per finding in `sscf_control_ids`

## Example Priority Gaps (from generated output)
### Failed controls
- SBS-ACS-001 - Enforce a Documented Permission Set Model (high)
- SBS-ACS-008 - Restrict Broad Privileges for Non-Human Identities (high)
- SBS-DATA-001 - Detect regulated data in long text fields (high)
- SBS-DEP-006 - Configure Salesforce CLI token expiration policies (high)
- SBS-SECCONF-001 - Establish a Salesforce Health Check baseline (high)

### Partial controls (critical examples)
- SBS-ACS-003 - Documented justification for Approve Uninstalled Connected Apps permission
- SBS-ACS-006 - Documented justification for Use Any API Client permission
- SBS-DEP-005 - Secret scanning for Salesforce repositories
- SBS-OAUTH-002 - Connected App access control via profile/permission set
- SBS-CPORTAL-001 - Prevent parameter-based record access in portal Apex

## Deliverables Produced by This Run
- Gap matrix (human-readable): `docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix_latest.md`
- Backlog (machine-readable): `docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog_latest.json`

## What This Enables for the Business Unit
- A control-level compliance heatmap (pass/partial/fail) from one ingest.
- Prioritized remediation backlog with ownership and target dates.
- Direct mapping from Salesforce controls to CSA SSCF controls for governance reporting.
- Repeatable evidence package generation for recurring review cycles.

## Recommended Next Step for Production-Grade Reporting
Run this exact pipeline with the business unit's real Salesforce gap file and publish the generated matrix/backlog as the monthly governance pack baseline.
