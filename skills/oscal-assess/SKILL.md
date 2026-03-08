---
name: oscal-assess
description: Maps gap-analysis findings to the SBS control catalog and SSCF framework. Produces gap matrix (markdown) and remediation backlog (JSON). Wraps scripts/oscal_gap_map.py.
cli: skills/oscal-assess/oscal-assess
model_hint: sonnet
---

# oscal-assess

Runs OSCAL-aligned gap mapping against the Security Benchmark for Salesforce (SBS) catalog. Produces a scored gap matrix and a prioritized remediation backlog.

## Usage

```bash
skills/oscal-assess/oscal-assess --help
skills/oscal-assess/oscal-assess \
  --controls <sbs-controls-json> \
  --gap-analysis <gap-json> \
  --mapping <control-mapping-yaml> \
  --sscf-map <sbs-to-sscf-mapping-yaml> \
  --out-md <gap-matrix-output.md> \
  --out-json <backlog-output.json>
```

## Flags

```
--controls       Path to normalized SBS controls JSON.
                 Default: docs/oscal-salesforce-poc/generated/sbs_controls.json
--gap-analysis   Path to gap-analysis JSON. Required.
                 Must include: assessment_id, assessment_time_utc, findings[].
--mapping        Path to control mapping YAML.
                 Default: config/oscal-salesforce/control_mapping.yaml
--sscf-map       Path to SBS-to-SSCF mapping YAML.
                 Default: config/oscal-salesforce/sbs_to_sscf_mapping.yaml
--out-md         Output gap matrix markdown path. Required.
--out-json       Output backlog JSON path. Required.
```

## How Mapping Works

1. For each finding in the gap JSON:
   a. If control_id starts with SBS-: direct SBS match, confidence=high.
   b. Otherwise: look up in control_mapping.yaml for legacy->SBS mapping.
   c. Apply SSCF mappings from sbs_to_sscf_mapping.yaml (override first, then category default).
2. Unmapped findings are listed explicitly in the output.
3. Invalid entries (SBS ID not in catalog) are listed separately.

## Output: Backlog JSON

The backlog JSON conforms to the following top-level shape:
```json
{
  "assessment_id": "...",
  "generated_at_utc": "...",
  "catalog_version": "...",
  "framework": "CSA_SSCF",
  "summary": {
    "catalog_controls": N,
    "findings_total": N,
    "mapped_findings": N,
    "unmapped_findings": N,
    "invalid_mapping_entries": N,
    "status_counts": { "pass": N, "fail": N, "partial": N, "not_applicable": N },
    "mapping_confidence_counts": { "high": N, "medium": N, "low": N }
  },
  "mapped_items": [...],
  "unmapped_items": [...],
  "invalid_mapping_entries": [...]
}
```

## Refreshing SBS Catalog

Before mapping, ensure the SBS catalog is up to date:
```bash
python3 scripts/oscal_import_sbs.py \
  --source-config config/oscal-salesforce/sbs_source.yaml \
  --out docs/oscal-salesforce-poc/generated/sbs_controls.json
```

The catalog is pinned to SBS v0.4.1 in config/oscal-salesforce/sbs_source.yaml. Do not change the pin without a change control entry in CHANGELOG.md.

## Composing

```bash
# Full pipeline: import SBS, run gap map, benchmark SSCF
python3 scripts/oscal_import_sbs.py --source-config config/oscal-salesforce/sbs_source.yaml --out docs/oscal-salesforce-poc/generated/sbs_controls.json
skills/oscal-assess/oscal-assess --gap-analysis <gap.json> --out-md <matrix.md> --out-json <backlog.json>
skills/sscf-benchmark/sscf-benchmark --backlog <backlog.json> --out <sscf-report.json>
```

## One-Command Smoke Test

```bash
./scripts/oscal_smoke_test.sh
```
