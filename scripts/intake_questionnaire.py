#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class PromptItem:
    key: str
    question: str
    multiline: bool = False


PROMPTS: list[PromptItem] = [
    PromptItem("program_name", "Program name:"),
    PromptItem("business_owner", "Business owner:"),
    PromptItem("security_owner", "Security owner:"),
    PromptItem("in_scope_envs", "In-scope orgs/environments (prod/sandbox):"),
    PromptItem("regulatory_drivers", "Regulatory/compliance drivers (SOX, GDPR, PCI, etc.):"),
    PromptItem("primary_use_case", "Primary business use case:"),
    PromptItem("top_3_outcomes", "Top 3 measurable outcomes (comma-separated):"),
    PromptItem("go_live_date", "Timeline and target go-live date:"),
    PromptItem("platform_scope", "Include only Salesforce or also ServiceNow/Workday:"),
    PromptItem("salesforce_clouds", "Salesforce clouds in scope:"),
    PromptItem("guest_users_integrations", "Include Guest users / Communities / API integrations (details):"),
    PromptItem("event_types", "Required event types to monitor:"),
    PromptItem("retention_target", "Log retention target:"),
    PromptItem("siem_destination", "SIEM destination:"),
    PromptItem("severity_thresholds", "Alert severity taxonomy and thresholds:"),
    PromptItem("tsp_risk_scenarios", "Transaction Security risk scenarios to enforce:", multiline=True),
    PromptItem("tsp_actions", "Allowed policy actions (Block/challenge/notify/allow with audit):"),
    PromptItem("tsp_approval_owner", "Production policy approval owner:"),
    PromptItem("tsp_exception_owner", "Exception/waiver process owner:"),
    PromptItem("mfa_requirements", "MFA policy requirements:"),
    PromptItem("session_settings", "Session timeout/lock settings:"),
    PromptItem("ip_network_controls", "IP restrictions/network controls:"),
    PromptItem("privileged_governance", "Privileged role governance expectations:"),
    PromptItem("connected_apps_policy", "Connected apps policy:"),
    PromptItem("data_export_controls", "Data export controls required:"),
    PromptItem("encryption_masking", "Encryption/masking requirements:"),
    PromptItem("data_residency", "Data residency constraints:"),
    PromptItem("assessment_owner", "Monthly baseline assessment owner:"),
    PromptItem("remediation_sla", "Remediation SLA by severity:"),
    PromptItem("escalation_path", "Escalation path for overdue findings:"),
    PromptItem("evidence_format", "Required evidence format for audit:"),
    PromptItem("sscf_required", "CSA SSCF required (yes/no):"),
    PromptItem("additional_frameworks", "Additional frameworks required:"),
    PromptItem("control_id_policy", "Control ID policy (provisional vs strict enterprise IDs):"),
    PromptItem("output_format", "Preferred output format (docx/markdown/yaml/json):"),
    PromptItem("deliverable_bundle", "Need executive summary + technical baseline + implementation backlog (yes/no):"),
    PromptItem("ops_runbook", "Need security operations/admin runbook (yes/no):"),
]


def ask_question(item: PromptItem) -> str:
    print(item.question)
    if not item.multiline:
        return input("> ").strip()

    print("(Enter multiple lines. Submit an empty line to finish.)")
    lines: list[str] = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def to_markdown(data: dict) -> str:
    lines = [
        "# SaaS Baseline Intake Response",
        "",
        f"- Generated: {data['generated_at_utc']}",
        "",
        "## 1) Business Context",
        f"- Program name: {data['program_name']}",
        f"- Business owner: {data['business_owner']}",
        f"- Security owner: {data['security_owner']}",
        f"- In-scope orgs/environments: {data['in_scope_envs']}",
        f"- Regulatory/compliance drivers: {data['regulatory_drivers']}",
        "",
        "## 2) Use Case and Outcomes",
        f"- Primary business use case: {data['primary_use_case']}",
        f"- Top 3 measurable outcomes: {data['top_3_outcomes']}",
        f"- Timeline and target go-live date: {data['go_live_date']}",
        "",
        "## 3) Scope of Baseline",
        f"- Scope: {data['platform_scope']}",
        f"- Salesforce clouds: {data['salesforce_clouds']}",
        f"- Guest/Communities/API integrations: {data['guest_users_integrations']}",
        "",
        "## 4) Event Monitoring Requirements",
        f"- Required event types: {data['event_types']}",
        f"- Log retention target: {data['retention_target']}",
        f"- SIEM destination: {data['siem_destination']}",
        f"- Severity thresholds: {data['severity_thresholds']}",
        "",
        "## 5) Transaction Security Policy Requirements",
        f"- Risk scenarios:\n{data['tsp_risk_scenarios']}",
        f"- Allowed actions: {data['tsp_actions']}",
        f"- Production approval owner: {data['tsp_approval_owner']}",
        f"- Exception owner: {data['tsp_exception_owner']}",
        "",
        "## 6) Identity and Access Baseline",
        f"- MFA: {data['mfa_requirements']}",
        f"- Session settings: {data['session_settings']}",
        f"- IP/network controls: {data['ip_network_controls']}",
        f"- Privileged governance: {data['privileged_governance']}",
        "",
        "## 7) Integration and Data Handling",
        f"- Connected apps policy: {data['connected_apps_policy']}",
        f"- Data export controls: {data['data_export_controls']}",
        f"- Encryption/masking: {data['encryption_masking']}",
        f"- Data residency constraints: {data['data_residency']}",
        "",
        "## 8) Operating Model",
        f"- Assessment owner: {data['assessment_owner']}",
        f"- Remediation SLA: {data['remediation_sla']}",
        f"- Escalation path: {data['escalation_path']}",
        f"- Evidence format: {data['evidence_format']}",
        "",
        "## 9) Standards Mapping",
        f"- SSCF required: {data['sscf_required']}",
        f"- Additional frameworks: {data['additional_frameworks']}",
        f"- Control ID policy: {data['control_id_policy']}",
        "",
        "## 10) Deliverable Format",
        f"- Output format: {data['output_format']}",
        f"- Full deliverable bundle: {data['deliverable_bundle']}",
        f"- Security operations/admin runbook: {data['ops_runbook']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive SaaS baseline intake questionnaire.")
    parser.add_argument(
        "--out-dir",
        default="docs/saas-baseline/intake-responses",
        help="Directory to write output files.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("SaaS Baseline Intake Questionnaire")
    print("Answer the prompts below. Press Enter to submit each answer.\n")

    result: dict = {}
    for item in PROMPTS:
        result[item.key] = ask_question(item)
        print()

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    result["generated_at_utc"] = datetime.now(UTC).isoformat()

    json_path = out_dir / f"intake-{timestamp}.json"
    md_path = out_dir / f"intake-{timestamp}.md"

    json_path.write_text(json.dumps(result, indent=2))
    md_path.write_text(to_markdown(result))

    print("Saved intake responses:")
    print(f"- {json_path}")
    print(f"- {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
