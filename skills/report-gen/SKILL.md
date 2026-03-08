---
name: report-gen
description: Generates governance-ready DOCX, Markdown, and JSON outputs from an OSCAL backlog. Formats for two audiences: application owners (plain language) and Security Team governance (technical).
cli: skills/report-gen/report-gen
model_hint: haiku
---

# report-gen

Takes an assessed OSCAL backlog and generates formatted governance outputs. Uses the reference.docx template for Word output. Supports two output audiences with different formatting profiles.

## Usage

```bash
skills/report-gen/report-gen --help
skills/report-gen/report-gen \
  --backlog <backlog-json> \
  --audience <app-owner|gis> \
  --out <output-path>
```

## Flags

```
--backlog         Path to OSCAL backlog JSON (from oscal-assess). Required.
--audience        Output audience. Required. One of:
                    app-owner    Executive summary + critical/high findings table
                    gis          Full control matrix + SSCF heatmap + NIST section
--out             Output file path. For .docx output, use .docx extension.
                  For markdown, use .md extension. Required.
--template        DOCX reference template.
                  Default: docs/saas-baseline/deliverables/reference.docx
--sscf-benchmark  Optional: path to sscf-benchmark JSON for heatmap section.
--nist-review     Optional: path to nist-reviewer output JSON for NIST section.
--title           Report title override. Default: "Salesforce OSCAL Assessment Report"
--org-alias       Org alias to include in report header. Default: from backlog.
```

## Audience Profiles

### app-owner

Sections included:
1. Executive Summary (plain language: what is the overall risk posture).
2. Critical and High Findings Table (control, severity, owner, due date, action).
3. What Happens Next (remediation process, who to contact, exception process link).
4. Appendix: Full Control Matrix (all 45 controls, status only).

Language rules:
- No SSCF control IDs in the executive summary.
- No "gap matrix" or "OSCAL" jargon in section titles.
- Due dates formatted as human dates (March 15, 2026), not ISO strings.

### gis

Sections included:
1. Assessment Metadata (ID, timestamp, org, environment, catalog version).
2. Summary Metrics (total/pass/partial/fail/not_applicable, mapping confidence distribution).
3. Full Control Matrix (legacy ID, SBS ID, title, confidence, SSCF IDs, status, severity, owner, due date).
4. Unmapped Findings (if any).
5. SSCF Domain Heatmap (from sscf-benchmark output if provided).
6. NIST AI RMF Compliance Note (from nist-reviewer output if provided, else [PENDING NIST REVIEW]).

## File Naming Convention

```
docs/oscal-salesforce-poc/deliverables/SFDC_OSCAL_<YYYY-MM-DD>.docx
docs/oscal-salesforce-poc/deliverables/SFDC_OSCAL_<YYYY-MM-DD>.md
docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix_latest.md
```

Always produce the .md counterpart alongside any .docx. The .md is committed; the .docx is committed alongside it.

## Generating Both Outputs In Sequence

```bash
DATE=$(date +%Y-%m-%d)
skills/report-gen/report-gen --backlog backlog.json --audience app-owner --out docs/oscal-salesforce-poc/deliverables/SFDC_OSCAL_${DATE}.md
skills/report-gen/report-gen --backlog backlog.json --audience app-owner --out docs/oscal-salesforce-poc/deliverables/SFDC_OSCAL_${DATE}.docx --template docs/saas-baseline/deliverables/reference.docx
skills/report-gen/report-gen --backlog backlog.json --audience gis --sscf-benchmark sscf_benchmark.json --out docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix_latest.md
```
