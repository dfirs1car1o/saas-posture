# OpenSearch Dashboards Guide

> **Optional — not required to run assessments.**
> The core pipeline writes JSON, Markdown, and DOCX artifacts that stand on their own.
> Dashboards are for teams who want trending, cross-org comparison, and continuous monitoring.

---

## The Three Dashboards

Three pre-built dashboards are imported automatically when the Docker stack starts.
Access them at **http://localhost:5601** → Dashboards (left sidebar).

| Dashboard | ID | Purpose |
|---|---|---|
| **SSCF Security Posture Overview** | `sscf-main-dashboard` | Combined view across all platforms and orgs |
| **Salesforce Security Posture** | `sfdc-dashboard` | Salesforce-only findings, score, and failing controls |
| **Workday Security Posture** | `workday-dashboard` | Workday-only findings, score, and failing controls |

---

## When to Use Each Dashboard

### SSCF Security Posture Overview
Use this when you want a **cross-platform governance view** — comparing Salesforce vs Workday health side-by-side, or presenting to a security committee with multiple platform owners in the room.

**Best for:**
- Monthly security reviews with leadership
- Comparing risk posture across all connected SaaS platforms
- Tracking POA&M aging across both platforms

**Layout (top to bottom):**
| Row | Panels | What it shows |
|---|---|---|
| Row 1 (scores) | Salesforce score tile + Workday score tile + Platform pie | Current average score per platform (color-coded RED/AMBER/GREEN) and finding distribution |
| Row 2 (top failures) | Top failing controls bar + Critical/High table | Top 10 failing controls by full name, grouped by severity + drill-down table with description, domain |
| Row 3 (trend) | Findings by severity bar + Score trend line | Severity breakdown across all findings + score progression over time |
| Row 4 (posture) | Domain bar + Open POA&M count + POA&M detail | Risk by SSCF domain + open/in-progress remediation items |
| Row 5 (details) | Failing controls document table | Full document view: control ID, title, domain, severity, status, owner, due date, remediation |

---

### Salesforce Security Posture
Use this for **platform-specific Salesforce review** — when the app owner or SFDC admin team is in the room, or when preparing a Salesforce-only audit response.

**Best for:**
- SBS (Salesforce Security Benchmark) quarterly reviews
- Presenting SFDC-specific findings to a Salesforce admin team
- Tracking SBS control remediation progress

**Layout:** Same structure as the overview, but the document table is pre-filtered to `platform:salesforce`. Score tiles show both SFDC and Workday for context.

---

### Workday Security Posture
Use this for **platform-specific Workday review** — WSCC compliance discussions, Workday HCM/Finance security reviews, or when presenting to a Workday team.

**Best for:**
- WSCC (Workday Security Control Catalog) reviews
- Presenting findings to a Workday integration/configuration team
- Tracking WD-* control remediation velocity

**Layout:** Mirror of the Salesforce dashboard, document table pre-filtered to `platform:workday`.

---

## Starting the Stack

```bash
# Start OpenSearch + Dashboards + auto-import dashboards
docker compose up -d

# Wait ~60 seconds for dashboards to become ready
curl -s http://localhost:5601/api/status | python3 -m json.tool | grep state

# Open dashboards
open http://localhost:5601
```

The `dashboard-init` service imports all 19 saved objects (2 index patterns, 10 visualizations, 3 saved searches, 3 dashboards) automatically on first start.

---

## Getting Data Into the Dashboards

After every assessment run, export the results:

```bash
# Auto-discover artifacts by org + date
python scripts/export_to_opensearch.py --auto --org <org-alias> --date <YYYY-MM-DD>

# Or use the interactive runner (handles export automatically if you opt in)
python scripts/run_assessment.py
```

The export writes two index types:

| Index | One doc per | Key fields |
|---|---|---|
| `sscf-runs-YYYY-MM` | Assessment run | org, platform, overall_score, nist_verdict, domain scores |
| `sscf-findings-YYYY-MM` | Finding | control_id, sbs_title, domain, severity, status, owner, due_date, poam_status, remediation |

### Workday dry-run → OpenSearch (full example)

```bash
# Step 1: Run the Workday dry-run assessment
python3 scripts/workday_dry_run_demo.py --org acme-workday --env dev

# Step 2: Export to OpenSearch
python scripts/export_to_opensearch.py --auto --org acme-workday --date $(date +%Y-%m-%d)

# Step 3: Open the Workday dashboard
open "http://localhost:5601/app/dashboards#/view/workday-dashboard"
```

### Salesforce dry-run → OpenSearch (full example)

```bash
# Step 1: Run the Salesforce dry-run (via interactive runner)
python scripts/run_assessment.py
# choose: salesforce → dry-run → <org-alias> → dev → yes (OpenSearch)

# Or manually:
ORG=acme-sfdc
DATE=$(date +%Y-%m-%d)
mkdir -p docs/oscal-salesforce-poc/generated/$ORG/$DATE

python -m skills.oscal_assess.oscal_assess assess \
  --dry-run --platform salesforce --env dev \
  --out docs/oscal-salesforce-poc/generated/$ORG/$DATE/gap_analysis.json

python scripts/oscal_gap_map.py \
  --controls docs/oscal-salesforce-poc/generated/sbs_controls.json \
  --gap-analysis docs/oscal-salesforce-poc/generated/$ORG/$DATE/gap_analysis.json \
  --mapping config/oscal-salesforce/control_mapping.yaml \
  --out-md docs/oscal-salesforce-poc/generated/$ORG/$DATE/gap_matrix.md \
  --out-json docs/oscal-salesforce-poc/generated/$ORG/$DATE/backlog.json

python scripts/export_to_opensearch.py --auto --org $ORG --date $DATE

open "http://localhost:5601/app/dashboards#/view/sfdc-dashboard"
```

---

## Time Range

Dashboards default to **last 1 year** so historical assessment data is always visible.

If you run an assessment today and see "No results", check:
- The time picker in the top-right corner — confirm it covers the assessment date
- That `export_to_opensearch.py` ran successfully after the assessment
- That the index exists: `curl http://localhost:9200/_cat/indices?v | grep sscf`

---

## Navigating the Dashboards

### Score tiles
The **Salesforce Score** and **Workday Score** tiles in the top-left use color ranges:
- **Red (0–50%)** — high risk; multiple critical/high failures
- **Amber (50–75%)** — moderate risk; partial controls, remediation in progress
- **Green (75–100%)** — low risk; most controls passing

### Top failing controls bar chart
Shows the **top 10 failing or partial controls** labeled by their full control name, grouped by severity color. Use this to quickly identify the highest-priority remediation items.

Click any bar to filter the entire dashboard to that control.

### Critical/High failing table
Shows the top critical and high findings with:
- Severity | Control ID | Control Description | Domain

Use this for priority-setting in remediation sprints.

### Failing controls document table (bottom row)
Shows **one row per finding** (real document values, not aggregations) with:
- control_id · full title · domain · severity · status · poam_status · owner · due_date · remediation

Sortable by any column. Use the search bar at top to filter by org, platform, or control.

### POA&M items
- **Open POA&M Items** (metric tile) — count of findings with `poam_status:Open`
- **Open POA&M Detail** (table) — control ID, severity, and status for all open/in-progress items

---

## Direct Links

Once the stack is running:

| Dashboard | URL |
|---|---|
| Combined overview | http://localhost:5601/app/dashboards#/view/sscf-main-dashboard |
| Salesforce | http://localhost:5601/app/dashboards#/view/sfdc-dashboard |
| Workday | http://localhost:5601/app/dashboards#/view/workday-dashboard |
| All dashboards | http://localhost:5601/app/dashboards |
| Discover (raw docs) | http://localhost:5601/app/data-explorer/discover |

---

## Saved Objects

All 19 saved objects are stored in `config/opensearch/dashboards.ndjson` and imported on every stack start by the `dashboard-init` service:

| Type | Count | IDs |
|---|---|---|
| index-pattern | 2 | `sscf-runs-*`, `sscf-findings-*` |
| visualization | 11 | score tiles, bars, pie, trend, tables |
| search (document table) | 3 | all platforms, salesforce-only, workday-only |
| dashboard | 3 | overview, salesforce, workday |

To re-import manually (e.g. after resetting OpenSearch):
```bash
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "osd-xsrf: true" \
  --form file=@config/opensearch/dashboards.ndjson
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Dashboard shows "No results" | Check time picker — set to last 1 year or include assessment date |
| Score tiles show "No data" | Run `export_to_opensearch.py` after assessment; check `sscf-runs-*` index exists |
| `dashboard-init` service failed | Re-run manually: `docker compose restart dashboard-init` |
| Dashboards not loading | Wait 60s after `docker compose up -d` for full startup |
| `opensearch-py not installed` | `pip install opensearch-py` or `pip install -e ".[monitoring]"` |
| Port 9200/5601 conflict | Stop conflicting service or change ports in `docker-compose.yml` |
| Apple Silicon (M-series) OOM | Reduce `OPENSEARCH_JAVA_OPTS` to `-Xms256m -Xmx256m` in compose |
| Wrong platform on findings | Check `backlog.json` has `platform` field; re-export with `--org` flag |
