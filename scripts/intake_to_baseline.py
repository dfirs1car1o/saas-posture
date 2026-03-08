#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def parse_event_types(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_outcomes(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_profile(data: dict[str, Any]) -> dict[str, Any]:
    generated = datetime.now(UTC).strftime("%Y-%m-%d")
    events = parse_event_types(data.get("event_types", ""))
    outcomes = parse_outcomes(data.get("top_3_outcomes", ""))

    policies = [
        {
            "id": "SF-TSP-001",
            "name": "Block impossible travel login event",
            "severity": "critical",
            "condition": "Login event indicates impossible travel",
            "action": "block",
            "notify": ["security_operations", "salesforce_platform_owner"],
            "sscf_control_id": "SSCF-TDR-001",
        },
        {
            "id": "SF-TSP-002",
            "name": "Block suspicious report export behavior",
            "severity": "critical",
            "condition": "Export volume exceeds baseline threshold or sensitive object scope",
            "action": "block",
            "notify": ["security_operations", "data_security_owner"],
            "sscf_control_id": "SSCF-DSP-002",
        },
        {
            "id": "SF-TSP-003",
            "name": "Challenge high-risk API session anomalies",
            "severity": "high",
            "condition": "API event context deviates from approved integration behavior",
            "action": "notify",
            "notify": ["security_operations", "integration_owner"],
            "sscf_control_id": "SSCF-CKM-001",
        },
    ]

    return {
        "version": 1,
        "profile_id": "SF-BASELINE-EM-TSP-V1-GENERATED",
        "title": "Salesforce Event Monitoring and Transaction Security Baseline v1 (Generated)",
        "platform": "salesforce",
        "owner_team": data.get("security_owner") or "security_engineering",
        "approver_team": "information_security",
        "effective_date": generated,
        "intake_source": {
            "generated_at_utc": data.get("generated_at_utc"),
            "program_name": data.get("program_name"),
            "business_owner": data.get("business_owner"),
            "go_live_date": data.get("go_live_date"),
        },
        "scope": {
            "environments": [x.strip() for x in data.get("in_scope_envs", "").split(",") if x.strip()],
            "clouds": [x.strip() for x in data.get("salesforce_clouds", "").split(",") if x.strip()],
            "include_integrations": "api" in data.get("guest_users_integrations", "").lower(),
            "include_experience_cloud_users": "communit" in data.get("guest_users_integrations", "").lower()
            or "experience" in data.get("salesforce_clouds", "").lower(),
        },
        "mapping": {
            "framework": "CSA_SSCF",
            "controls": ["SSCF-LOG-001", "SSCF-LOG-002", "SSCF-TDR-001", "SSCF-IAM-001"],
        },
        "business_outcomes": outcomes,
        "event_monitoring": {
            "required": True,
            "retention_target": data.get("retention_target"),
            "export_to_siem_required": True,
            "siem_destination": data.get("siem_destination"),
            "required_event_types": events,
            "severity_thresholds": data.get("severity_thresholds"),
        },
        "transaction_security_policies": {
            "required": True,
            "risk_scenarios_from_intake": data.get("tsp_risk_scenarios", ""),
            "approved_actions": data.get("tsp_actions"),
            "approval_owner": data.get("tsp_approval_owner"),
            "exception_owner": data.get("tsp_exception_owner"),
            "policies": policies,
        },
        "identity_and_access": {
            "mfa_requirements": data.get("mfa_requirements"),
            "session_settings": data.get("session_settings"),
            "ip_network_controls": data.get("ip_network_controls"),
            "privileged_governance": data.get("privileged_governance"),
        },
        "integration_and_data": {
            "connected_apps_policy": data.get("connected_apps_policy"),
            "data_export_controls": data.get("data_export_controls"),
            "encryption_masking": data.get("encryption_masking"),
            "data_residency": data.get("data_residency"),
        },
        "operations": {
            "assessment_owner": data.get("assessment_owner"),
            "remediation_sla": data.get("remediation_sla"),
            "escalation_path": data.get("escalation_path"),
            "evidence_format": data.get("evidence_format"),
        },
    }


def build_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Generated Salesforce Baseline Configuration",
        "",
        f"- Profile ID: `{profile['profile_id']}`",
        f"- Effective date: `{profile['effective_date']}`",
        f"- Program: `{profile['intake_source'].get('program_name', '')}`",
        "",
        "## Scope",
        f"- Environments: {', '.join(profile['scope']['environments']) or 'n/a'}",
        f"- Clouds: {', '.join(profile['scope']['clouds']) or 'n/a'}",
        "",
        "## Event Monitoring",
        f"- Retention target: {profile['event_monitoring'].get('retention_target', '')}",
        f"- SIEM: {profile['event_monitoring'].get('siem_destination', '')}",
        f"- Event types: {', '.join(profile['event_monitoring'].get('required_event_types', []))}",
        "",
        "## Transaction Security Policies",
    ]
    for p in profile["transaction_security_policies"]["policies"]:
        lines.append(f"- `{p['id']}` {p['name']} ({p['severity']}, action={p['action']})")
    lines += [
        "",
        "## SSCF Controls",
        f"- {', '.join(profile['mapping']['controls'])}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert intake response JSON into baseline config outputs.")
    parser.add_argument("input_json", help="Path to intake JSON produced by intake_questionnaire.py")
    parser.add_argument(
        "--out-dir",
        default="config/saas_baseline_profiles/generated",
        help="Output directory for generated baseline profile YAML.",
    )
    parser.add_argument(
        "--docs-out-dir",
        default="docs/saas-baseline/generated",
        help="Output directory for generated markdown summary.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_path = Path(args.input_json).resolve()
    data = json.loads(input_path.read_text())

    profile = build_profile(data)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = (root / args.out_dir).resolve()
    docs_out_dir = (root / args.docs_out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_out_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = out_dir / f"salesforce-baseline-generated-{timestamp}.yaml"
    md_path = docs_out_dir / f"salesforce-baseline-generated-{timestamp}.md"

    if yaml is not None:
        yaml_path.write_text(yaml.safe_dump(profile, sort_keys=False))
    else:
        # JSON is valid YAML 1.2; fallback keeps script usable without PyYAML.
        yaml_path.write_text(json.dumps(profile, indent=2))
    md_path.write_text(build_markdown(profile))

    print("Generated baseline artifacts:")
    print(f"- {yaml_path}")
    print(f"- {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
