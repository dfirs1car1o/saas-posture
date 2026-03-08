# Wiki Update: OSCAL POC for Salesforce

## Summary
Created an `OSCAL POC for Salesforce` track under the SaaS Risk Program to operationalize baseline management in three phases:
1. Build from existing gap-analysis data.
2. Connect sandbox/dev org for automated checks.
3. Promote to production orgs after tuning and approval.

## New Assets
- `docs/oscal-salesforce-poc/README.md`
- `config/oscal-salesforce/sbs_source.yaml`
- `config/oscal-salesforce/control_mapping.yaml`
- `config/oscal-salesforce/sbs_to_sscf_mapping.yaml`
- `scripts/oscal_import_sbs.py`
- `scripts/oscal_gap_map.py`

## Operating Intent
- Use version-pinned SBS XML as upstream benchmark source.
- Map SBS controls to CSA SSCF control IDs for governance traceability.
- Preserve Acme Corp ownership model (BSS + Security Team) and exception governance.
- Keep technical and operational baseline outputs in sync from one mapped control set.

## Next Steps
1. Import SBS controls (pinned release).
2. Run mapping against completed Salesforce gap analysis.
3. Review unmapped controls and finalize control mapping.
4. Implement sandbox collectors with evidence references per control.
