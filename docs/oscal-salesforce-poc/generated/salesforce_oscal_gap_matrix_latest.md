# Salesforce OSCAL Gap Matrix (POC)

- Assessment ID: `ACME-SF-COLLECTOR-MOCK-2026-02-24`
- Generated UTC: `2026-02-25T15:19:18.118825+00:00`
- SBS controls in catalog: `45`
- Mapped findings: `45`
- Unmapped findings: `0`

## Status Summary (Mapped Findings)
- pass: `24`
- fail: `9`
- partial: `12`
- not_applicable: `0`

## Control Mapping Table
| Legacy Control ID | SBS Control ID | SBS Title | Mapping Confidence | SSCF Controls | Status | Severity | Owner | Due Date |
|---|---|---|---|---|---|---|---|---|
| SBS-ACS-001 | SBS-ACS-001 | Enforce a Documented Permission Set Model | high | SSCF-IAM-002 | fail | high | Salesforce Platform Owner | 2026-03-15 |
| SBS-ACS-002 | SBS-ACS-002 | Documented Justification for All `API-Enabled` Authorizations | high | SSCF-IAM-002 | pass | high | SaaS Security Team |  |
| SBS-ACS-003 | SBS-ACS-003 | Documented Justification for `Approve Uninstalled Connected Apps` Permission | high | SSCF-IAM-002 | partial | critical | Security Operations Monitoring Team | 2026-03-17 |
| SBS-ACS-004 | SBS-ACS-004 | Documented Justification for All Super Admin–Equivalent Users | high | SSCF-IAM-002 | pass | high | GRC and Audit |  |
| SBS-ACS-005 | SBS-ACS-005 | Only Use Custom Profiles for Active Users | high | SSCF-IAM-002 | pass | high | Salesforce Platform Owner |  |
| SBS-ACS-006 | SBS-ACS-006 | Documented Justification for `Use Any API Client` Permission | high | SSCF-IAM-002 | partial | critical | SaaS Security Team | 2026-03-20 |
| SBS-ACS-007 | SBS-ACS-007 | Maintain Inventory of Non-Human Identities | high | SSCF-IAM-002 | pass | high | Security Operations Monitoring Team |  |
| SBS-ACS-008 | SBS-ACS-008 | Restrict Broad Privileges for Non-Human Identities | high | SSCF-IAM-002 | fail | high | GRC and Audit | 2026-03-22 |
| SBS-ACS-009 | SBS-ACS-009 | Implement Compensating Controls for Privileged Non-Human Identities | high | SSCF-IAM-002 | pass | medium | Salesforce Platform Owner |  |
| SBS-ACS-010 | SBS-ACS-010 | Enforce Periodic Access Review and Recertification | high | SSCF-IAM-002 | pass | medium | SaaS Security Team |  |
| SBS-ACS-011 | SBS-ACS-011 | Enforce Governance of Access and Authorization Changes | high | SSCF-IAM-002 | partial | high | Security Operations Monitoring Team | 2026-03-25 |
| SBS-ACS-012 | SBS-ACS-012 | Classify Users for Login Hours Restrictions | high | SSCF-IAM-002 | pass | medium | GRC and Audit |  |
| SBS-AUTH-001 | SBS-AUTH-001 | Enable Organization-Wide SSO Enforcement Setting | high | SSCF-IAM-003 | pass | critical | Salesforce Platform Owner |  |
| SBS-AUTH-002 | SBS-AUTH-002 | Govern and Document All Users Permitted to Bypass Single Sign-On | high | SSCF-IAM-001 | fail | medium | SaaS Security Team | 2026-03-28 |
| SBS-AUTH-003 | SBS-AUTH-003 | Prohibit Broad or Unrestricted Profile Login IP Ranges | high | SSCF-IAM-001 | partial | medium | Security Operations Monitoring Team | 2026-03-29 |
| SBS-AUTH-004 | SBS-AUTH-004 | Enforce Strong Multi-Factor Authentication for External Users with Substantial Access to Sensitive Data | high | SSCF-IAM-001 | fail | medium | GRC and Audit | 2026-03-30 |
| SBS-CODE-001 | SBS-CODE-001 | Mandatory Peer Review for Salesforce Code Changes | high | SSCF-CON-001 | pass | medium | Salesforce Platform Owner |  |
| SBS-CODE-002 | SBS-CODE-002 | Pre-Merge Static Code Analysis for Apex and LWC | high | SSCF-CON-001 | partial | medium | SaaS Security Team | 2026-04-01 |
| SBS-CODE-003 | SBS-CODE-003 | Implement Persistent Apex Application Logging | high | SSCF-CON-001 | pass | high | Security Operations Monitoring Team |  |
| SBS-CODE-004 | SBS-CODE-004 | Prevent Sensitive Data in Application Logs | high | SSCF-CON-001 | pass | critical | GRC and Audit |  |
| SBS-CPORTAL-001 | SBS-CPORTAL-001 | Prevent Parameter-Based Record Access in Portal Apex | high | SSCF-DSP-001 | partial | critical | Salesforce Platform Owner | 2026-04-04 |
| SBS-CPORTAL-002 | SBS-CPORTAL-002 | Restrict Guest User Record Access | high | SSCF-DSP-001 | pass | critical | SaaS Security Team |  |
| SBS-DATA-001 | SBS-DATA-001 | Implement Mechanisms to Detect Regulated Data in Long Text Area Fields | high | SSCF-DSP-001 | fail | high | Security Operations Monitoring Team | 2026-04-06 |
| SBS-DATA-002 | SBS-DATA-002 | Maintain an Inventory of Long Text Area Fields Containing Regulated Data | high | SSCF-DSP-001 | pass | medium | GRC and Audit |  |
| SBS-DATA-003 | SBS-DATA-003 | Maintain Tested Backup and Recovery for Salesforce Data and Metadata | high | SSCF-DSP-001 | pass | high | Salesforce Platform Owner |  |
| SBS-DATA-004 | SBS-DATA-004 | Require Field History Tracking for Sensitive Fields | high | SSCF-DSP-001 | partial | high | SaaS Security Team | 2026-04-09 |
| SBS-DEP-001 | SBS-DEP-001 | Require a Designated Deployment Identity for Metadata Changes | high | SSCF-CON-002 | pass | high | Security Operations Monitoring Team |  |
| SBS-DEP-002 | SBS-DEP-002 | Establish and Maintain a List of High-Risk Metadata Types Prohibited from Direct Production Editing | high | SSCF-CON-002 | pass | high | GRC and Audit |  |
| SBS-DEP-003 | SBS-DEP-003 | Monitor and Alert on Unauthorized Modifications to High-Risk Metadata | high | SSCF-LOG-002, SSCF-CON-002 | fail | high | Salesforce Platform Owner | 2026-03-15 |
| SBS-DEP-005 | SBS-DEP-005 | Implement Secret Scanning for Salesforce Source Repositories | high | SSCF-CON-002 | partial | critical | SaaS Security Team | 2026-03-16 |
| SBS-DEP-006 | SBS-DEP-006 | Configure Salesforce CLI Connected App with Token Expiration Policies | high | SSCF-CON-002 | fail | high | Security Operations Monitoring Team | 2026-03-17 |
| SBS-FILE-001 | SBS-FILE-001 | Require Expiry Dates on Public Content Links | high | SSCF-DSP-002 | pass | low | GRC and Audit |  |
| SBS-FILE-002 | SBS-FILE-002 | Require Passwords on Public Content Links for Sensitive Content | high | SSCF-DSP-002 | partial | medium | Salesforce Platform Owner | 2026-03-19 |
| SBS-FILE-003 | SBS-FILE-003 | Periodic Review and Cleanup of Public Content Links | high | SSCF-DSP-002 | pass | low | SaaS Security Team |  |
| SBS-FDNS-001 | SBS-FDNS-001 | Centralized Security System of Record | high | SSCF-GOV-001 | pass | low | Security Operations Monitoring Team |  |
| SBS-INT-001 | SBS-INT-001 | Enforce Governance of Browser Extensions Accessing Salesforce | high | SSCF-DSP-002 | partial | medium | GRC and Audit | 2026-03-22 |
| SBS-INT-002 | SBS-INT-002 | Inventory and Justification of Remote Site Settings | high | SSCF-DSP-002 | pass | medium | Salesforce Platform Owner |  |
| SBS-INT-003 | SBS-INT-003 | Inventory and Justification of Named Credentials | high | SSCF-CKM-001 | fail | medium | SaaS Security Team | 2026-03-24 |
| SBS-INT-004 | SBS-INT-004 | Retain API Total Usage Event Logs for 30 Days | high | SSCF-LOG-003 | pass | high | Security Operations Monitoring Team |  |
| SBS-OAUTH-001 | SBS-OAUTH-001 | Require Formal Installation of Connected Apps | high | SSCF-CKM-001 | pass | critical | GRC and Audit |  |
| SBS-OAUTH-002 | SBS-OAUTH-002 | Require Profile or Permission Set Access Control for Connected Apps | high | SSCF-CKM-001 | partial | critical | Salesforce Platform Owner | 2026-03-27 |
| SBS-OAUTH-003 | SBS-OAUTH-003 | Add Criticality Classification of OAuth-Enabled Connected Apps | high | SSCF-CKM-001 | pass | high | SaaS Security Team |  |
| SBS-OAUTH-004 | SBS-OAUTH-004 | Due Diligence Documentation for High-Risk Connected App Vendors | high | SSCF-CKM-001 | pass | medium | Security Operations Monitoring Team |  |
| SBS-SECCONF-001 | SBS-SECCONF-001 | Establish a Salesforce Health Check Baseline | high | SSCF-CON-001 | fail | high | GRC and Audit | 2026-03-30 |
| SBS-SECCONF-002 | SBS-SECCONF-002 | Review and Remediate Salesforce Health Check Deviations | high | SSCF-CON-001 | partial | high | Salesforce Platform Owner | 2026-03-31 |

## Unmapped Findings
- None

## Invalid Mapping Entries
- None
