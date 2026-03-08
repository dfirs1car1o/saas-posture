---
name: sscf-benchmark
description: Benchmarks an OSCAL backlog JSON against the CSA SSCF control index. Produces a domain-level heatmap showing which SSCF domains are passing, partially covered, or failing.
cli: skills/sscf-benchmark/sscf-benchmark
model_hint: sonnet
---

# sscf-benchmark

Consumes an OSCAL backlog JSON (produced by oscal-assess) and scores it against the full CSA SSCF control index. Produces a domain heatmap for governance reporting.

## Usage

```bash
skills/sscf-benchmark/sscf-benchmark --help
skills/sscf-benchmark/sscf-benchmark \
  --backlog <backlog-json> \
  --sscf-index <sscf-control-index-yaml> \
  --out <sscf-benchmark-output-json>
```

## Flags

```
--backlog        Path to oscal-assess backlog JSON. Required.
--sscf-index     Path to SSCF control index YAML.
                 Default: config/sscf_control_index.yaml
--out            Output benchmark JSON path. Required.
--format         Output format: json|markdown. Default: json.
--threshold      Minimum pass percentage to consider a domain covered.
                 Default: 80.
```

## Scoring Method

For each SSCF control in the index:
1. Find all backlog items that map to this control ID.
2. Score: pass=1.0, partial=0.5, fail=0.0, not_applicable=excluded.
3. Domain score = average of all control scores in that domain.
4. Flag domain as:
   - covered: score >= threshold (default 80%).
   - partial: 50% <= score < threshold.
   - gap: score < 50%.

## Output Shape

```json
{
  "assessment_id": "...",
  "generated_at_utc": "...",
  "sscf_index_version": "...",
  "threshold_pct": 80,
  "domains": {
    "identity_access_management": {
      "controls_evaluated": 3,
      "score_pct": 75.0,
      "status": "partial",
      "control_detail": [
        { "sscf_control_id": "SSCF-IAM-001", "score": 1.0, "status": "covered" }
      ]
    }
  },
  "summary": {
    "domains_covered": N,
    "domains_partial": N,
    "domains_gap": N,
    "domains_not_evaluated": N
  }
}
```

## SSCF Domains In Scope

From config/sscf_control_index.yaml:
- identity_access_management (SSCF-IAM-001, IAM-002, IAM-003)
- logging_monitoring (SSCF-LOG-001, LOG-002, LOG-003)
- threat_detection_response (SSCF-TDR-001, TDR-002)
- cryptography_key_management (SSCF-CKM-001)
- data_security_privacy (SSCF-DSP-001, DSP-002)
- configuration_hardening (SSCF-CON-001, CON-002)
- governance_risk_compliance (SSCF-GOV-001)

## Composing

The heatmap output feeds directly into report-gen for the Security Team governance report section:
```bash
skills/sscf-benchmark/sscf-benchmark --backlog backlog.json --out sscf_benchmark.json
skills/report-gen/report-gen --backlog backlog.json --sscf-benchmark sscf_benchmark.json --audience gis --out gap_matrix.md
```
