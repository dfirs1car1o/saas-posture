#!/usr/bin/env python3
"""
generate_sbs_oscal_catalog.py — Convert sbs_controls.json to OSCAL 1.1.2 catalog.

Reads:  docs/oscal-salesforce-poc/generated/sbs_controls.json
Writes: config/oscal-salesforce/sbs_catalog.json

Each SBS control is mapped to its parent SSCF control via sbs_to_sscf_mapping.yaml.
The output OSCAL catalog links back to sscf_catalog.json for regulatory traceability.

Usage:
    python3 scripts/generate_sbs_oscal_catalog.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[1]

_SBS_SOURCE = _REPO / "docs/oscal-salesforce-poc/generated/sbs_controls.json"
_SSCF_MAP = _REPO / "config/oscal-salesforce/sbs_to_sscf_mapping.yaml"
_OUT = _REPO / "config/oscal-salesforce/sbs_catalog.json"

_OSCAL_VERSION = "1.1.2"
_CATALOG_UUID = "e5f6a7b8-c9d0-1234-efab-345678901234"
_ORG_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"

_RISK_TO_SEVERITY = {
    "Critical": "critical",
    "High": "high",
    "Medium": "moderate",
    "Low": "low",
}

_CATEGORY_TO_GROUP_ID = {
    "Access Controls": "acs",
    "Authentication": "auth",
    "Data Security": "data",
    "Deployments": "dep",
    "Foundations": "fnd",
    "Integrations": "int",
    "OAuth Security": "oauth",
    "Code Security": "code",
    "Customer Portals": "portal",
    "File Security": "file",
    "Security Configuration": "secconf",
}


def _slugify(text: str) -> str:
    """Convert text to OSCAL-safe NCName (lowercase, hyphens)."""
    return re.sub(r"[^a-z0-9-]", "-", text.lower()).strip("-")


def _control_id(raw_id: str) -> str:
    """SBS-ACS-001 → sbs-acs-001."""
    return raw_id.lower()


def _build_sscf_link(sscf_control_id: str) -> dict:
    """Build OSCAL link referencing the parent SSCF control in sscf_catalog.json."""
    oscal_id = sscf_control_id.lower().replace("_", "-")
    return {
        "href": f"../../sscf/sscf_catalog.json#{oscal_id}",
        "rel": "related",
        "text": f"Maps to {sscf_control_id} in SSCF catalog",
    }


def _build_control(ctrl: dict, sscf_map: dict) -> dict:
    raw_id = ctrl["control_id"]
    oscal_id = _control_id(raw_id)
    risk_level = ctrl.get("risk_level", "High")
    severity = _RISK_TO_SEVERITY.get(risk_level, "high")

    parts = [
        {
            "id": f"{oscal_id}_smt",
            "name": "statement",
            "prose": ctrl.get("statement", ""),
        }
    ]

    if ctrl.get("description"):
        parts.append(
            {
                "id": f"{oscal_id}_gdn",
                "name": "guidance",
                "prose": ctrl["description"],
            }
        )

    if ctrl.get("audit_procedure"):
        parts.append(
            {
                "id": f"{oscal_id}_obj",
                "name": "objective",
                "prose": ctrl["audit_procedure"],
            }
        )

    if ctrl.get("remediation"):
        parts.append(
            {
                "id": f"{oscal_id}_imp",
                "name": "implementation-guidance",
                "prose": ctrl["remediation"],
            }
        )

    if ctrl.get("default_value"):
        parts.append(
            {
                "id": f"{oscal_id}_def",
                "name": "default-value",
                "prose": ctrl["default_value"],
            }
        )

    props = [
        {"name": "label", "value": raw_id},
        {"name": "sort-id", "value": oscal_id},
        {"name": "severity", "value": severity},
        {"name": "category", "value": ctrl.get("category", "")},
    ]

    remediation_scope = ctrl.get("remediation_scope", {})
    if remediation_scope.get("scope"):
        props.append({"name": "remediation-scope", "value": remediation_scope["scope"]})
    if remediation_scope.get("entity_type"):
        props.append({"name": "remediation-entity-type", "value": remediation_scope["entity_type"]})

    # SSCF mapping link
    links = []
    sscf_id = sscf_map.get(raw_id)
    if sscf_id:
        links.append(_build_sscf_link(sscf_id))
        props.append({"name": "sscf-control", "value": sscf_id})

    control: dict = {
        "id": oscal_id,
        "title": ctrl["title"],
        "props": props,
        "parts": parts,
    }
    if links:
        control["links"] = links

    return control


def _build_groups(controls: list[dict], sscf_map: dict) -> list[dict]:
    """Group controls by category, preserving order of first appearance."""
    groups: dict[str, dict] = {}
    for ctrl in controls:
        cat = ctrl.get("category", "Other")
        if cat not in groups:
            group_id = _CATEGORY_TO_GROUP_ID.get(cat, _slugify(cat))
            groups[cat] = {
                "id": group_id,
                "class": "category",
                "title": cat,
                "remarks": ctrl.get("category_description", ""),
                "controls": [],
            }
        groups[cat]["controls"].append(_build_control(ctrl, sscf_map))
    return list(groups.values())


def _load_sscf_map(path: Path) -> dict[str, str]:
    """Return {sbs_control_id: sscf_control_id} from sbs_to_sscf_mapping.yaml.

    The mapping file uses category-level defaults plus per-control overrides.
    For catalog purposes we use control_overrides first, then category defaults.
    This returns a best-effort per-control SSCF ID.
    """
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text())
    overrides = data.get("control_overrides", {})

    result: dict[str, str] = {}
    for ctrl_id, mappings in overrides.items():
        if mappings:
            result[ctrl_id] = mappings[0]["sscf_control_id"]

    return result


def main(dry_run: bool = False) -> None:
    if not _SBS_SOURCE.exists():
        print(f"ERROR: SBS source not found: {_SBS_SOURCE}", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(_SBS_SOURCE.read_text())
    controls: list[dict] = raw.get("controls", [])
    source_info = raw.get("source", {})
    catalog_info = raw.get("catalog", {})

    sscf_map = _load_sscf_map(_SSCF_MAP)

    groups = _build_groups(controls, sscf_map)

    catalog = {
        "catalog": {
            "uuid": _CATALOG_UUID,
            "metadata": {
                "title": catalog_info.get("title", "Security Benchmark for Salesforce (SBS) — OSCAL Catalog"),
                "last-modified": "2026-03-07T00:00:00Z",
                "version": catalog_info.get("version", "0.4.0"),
                "oscal-version": _OSCAL_VERSION,
                "remarks": (
                    f"OSCAL 1.1.2 representation of the {source_info.get('benchmark_name', 'SBS')} "
                    f"{source_info.get('release_tag', '')}. "
                    "Controls link to parent SSCF controls in config/sscf/sscf_catalog.json. "
                    "Generated by scripts/generate_sbs_oscal_catalog.py."
                ),
                "roles": [
                    {"id": "creator", "title": "Catalog Author"},
                    {"id": "maintainer", "title": "Control Framework Maintainer"},
                ],
                "parties": [
                    {
                        "uuid": _ORG_UUID,
                        "type": "organization",
                        "name": "Security Team",
                    }
                ],
                "responsible-parties": [
                    {"role-id": "creator", "party-uuids": [_ORG_UUID]},
                    {"role-id": "maintainer", "party-uuids": [_ORG_UUID]},
                ],
            },
            "groups": groups,
            "back-matter": {
                "resources": [
                    {
                        "uuid": "f6a7b8c9-d0e1-2345-fab2-456789012345",
                        "title": "SBS Source",
                        "rlinks": [{"href": source_info.get("xml_url", "")}],
                    },
                    {
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "title": "SSCF Catalog",
                        "rlinks": [{"href": "../../sscf/sscf_catalog.json"}],
                    },
                ]
            },
        }
    }

    output = json.dumps(catalog, indent=2, ensure_ascii=False)

    if dry_run:
        total = sum(len(g["controls"]) for g in groups)
        print(f"DRY-RUN: would write {len(groups)} groups, {total} controls → {_OUT}")
        return

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(output)
    total = sum(len(g["controls"]) for g in groups)
    print(f"Wrote {len(groups)} groups, {total} controls → {_OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
