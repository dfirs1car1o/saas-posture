"""
harness/tools.py — Anthropic tool schema definitions + subprocess dispatchers.

Each tool schema follows the Anthropic tool format (input_schema = JSON Schema).
dispatch(name, input_dict) runs the corresponding CLI as a subprocess and returns
its result as a JSON string. All output files are written to:
    docs/oscal-salesforce-poc/generated/<org>/<date>/

Raises RuntimeError on non-zero subprocess exit (stderr included in message).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
_PYTHON = sys.executable

# ---------------------------------------------------------------------------
# Tool schema definitions (Anthropic format)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "sfdc_connect_collect",
        "description": (
            "Collect security-relevant configuration from a Salesforce org (read-only). "
            "Use scope='all' for a full assessment. Returns path to collector output JSON."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "Org alias or instance URL (overrides SF_INSTANCE_URL)"},
                "scope": {
                    "type": "string",
                    "enum": [
                        "all",
                        "auth",
                        "access",
                        "event-monitoring",
                        "transaction-security",
                        "integrations",
                        "oauth",
                        "secconf",
                    ],
                    "description": "Which configuration scope(s) to collect",
                },
                "env": {
                    "type": "string",
                    "enum": ["dev", "test", "prod"],
                    "description": "Environment label for evidence tagging",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Print what would be collected without calling Salesforce API",
                },
            },
            "required": ["scope"],
        },
    },
    {
        "name": "oscal_assess_assess",
        "description": (
            "Run deterministic SBS OSCAL gap assessment. "
            "Takes sfdc-connect collector output and produces gap_analysis.json. "
            "Use dry_run=true to emit realistic weak-org stub findings without a live org."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "Org alias for output dir naming"},
                "collector_output": {
                    "type": "string",
                    "description": "Path to sfdc-connect collect output JSON (omit if dry_run=true)",
                },
                "env": {
                    "type": "string",
                    "enum": ["dev", "test", "prod"],
                    "description": "Environment label",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Emit realistic stub findings (weak-org scenario) without a real org",
                },
                "out": {"type": "string", "description": "Override output file path"},
            },
            "required": [],
        },
    },
    {
        "name": "oscal_gap_map",
        "description": (
            "Map gap-analysis findings to SSCF controls and produce a prioritised remediation backlog. "
            "Reads gap_analysis.json, writes matrix.md and backlog.json."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "Org alias for output dir naming"},
                "gap_analysis": {
                    "type": "string",
                    "description": "Path to gap_analysis.json produced by oscal_assess_assess",
                },
                "out_md": {"type": "string", "description": "Override output path for matrix markdown"},
                "out_json": {"type": "string", "description": "Override output path for backlog JSON"},
            },
            "required": ["gap_analysis"],
        },
    },
    {
        "name": "report_gen_generate",
        "description": (
            "Generate governance output (DOCX or Markdown) from assessment backlog. "
            "Use audience='app-owner' for a plain-language report; 'gis' for a technical CorpIS review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "backlog": {"type": "string", "description": "Path to backlog.json from oscal_gap_map"},
                "audience": {
                    "type": "string",
                    "enum": ["app-owner", "gis"],
                    "description": "Report audience",
                },
                "out": {"type": "string", "description": "Output file path (.md or .docx)"},
                "sscf_benchmark": {
                    "type": "string",
                    "description": "Optional path to sscf_report.json for domain heatmap",
                },
                "nist_review": {
                    "type": "string",
                    "description": "Optional path to nist_review.json for NIST AI RMF section",
                },
                "org_alias": {"type": "string", "description": "Org alias for report header"},
                "dry_run": {"type": "boolean", "description": "Print plan without writing files"},
            },
            "required": ["backlog", "audience", "out"],
        },
    },
    {
        "name": "sscf_benchmark_benchmark",
        "description": (
            "Benchmark the remediation backlog against the SSCF control index to produce "
            "a domain-level compliance scorecard (overall_score, overall_status, per-domain breakdown)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "Org alias for output dir naming"},
                "backlog": {
                    "type": "string",
                    "description": "Path to backlog.json produced by oscal_gap_map",
                },
                "out": {"type": "string", "description": "Override output path for SSCF report JSON"},
            },
            "required": ["backlog"],
        },
    },
]

ALL_TOOLS = TOOL_SCHEMAS


# ---------------------------------------------------------------------------
# Output directory helper
# ---------------------------------------------------------------------------


def _out_dir(org: str) -> Path:
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    out = _REPO / "docs" / "oscal-salesforce-poc" / "generated" / org / date
    out.mkdir(parents=True, exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------


def _run(args: list[str]) -> str:
    """Run subprocess, return stdout. Raise RuntimeError on non-zero exit."""
    result = subprocess.run(args, capture_output=True, text=True, cwd=_REPO)  # noqa: S603
    if result.returncode != 0:
        raise RuntimeError(f"Tool '{args[0]}' failed (exit {result.returncode}):\n{result.stderr.strip()}")
    return result.stdout


# ---------------------------------------------------------------------------
# Per-tool dispatchers
# ---------------------------------------------------------------------------


def _dispatch_sfdc_connect(inp: dict[str, Any], out_dir: Path) -> str:
    out_path = inp.get("out") or str(out_dir / "sfdc_raw.json")
    args = [
        _PYTHON,
        "-m",
        "skills.sfdc_connect.sfdc_connect",
        "collect",
        "--scope",
        inp.get("scope", "all"),
        "--env",
        inp.get("env", "dev"),
    ]
    if inp.get("org"):
        args += ["--org", inp["org"]]
    if inp.get("dry_run"):
        # dry-run prints a message but writes nothing — return synthetic result
        args.append("--dry-run")
        _run(args)
        return json.dumps(
            {
                "status": "ok",
                "dry_run": True,
                "output_file": out_path,
                "note": "dry-run: org config not collected; pass dry_run=true to oscal_assess_assess",
            }
        )
    args += ["--out", out_path]
    _run(args)
    return json.dumps({"status": "ok", "output_file": out_path})


def _dispatch_oscal_assess(inp: dict[str, Any], out_dir: Path) -> str:
    out_path = inp.get("out") or str(out_dir / "gap_analysis.json")
    args = [
        _PYTHON,
        "-m",
        "skills.oscal_assess.oscal_assess",
        "assess",
        "--env",
        inp.get("env", "dev"),
        "--out",
        out_path,
    ]
    if inp.get("collector_output"):
        args += ["--collector-output", inp["collector_output"]]
    if inp.get("dry_run"):
        args.append("--dry-run")
    _run(args)
    return json.dumps({"status": "ok", "output_file": out_path})


def _dispatch_gap_map(inp: dict[str, Any], out_dir: Path) -> str:
    out_md = inp.get("out_md") or str(out_dir / "matrix.md")
    out_json = inp.get("out_json") or str(out_dir / "backlog.json")
    controls_path = _REPO / "docs/oscal-salesforce-poc/generated/sbs_controls.json"
    mapping_path = _REPO / "config/oscal-salesforce/control_mapping.yaml"
    sscf_map_path = _REPO / "config/oscal-salesforce/sbs_to_sscf_mapping.yaml"
    args = [
        _PYTHON,
        "scripts/oscal_gap_map.py",
        "--controls",
        str(controls_path),
        "--gap-analysis",
        inp["gap_analysis"],
        "--mapping",
        str(mapping_path),
        "--sscf-map",
        str(sscf_map_path),
        "--out-md",
        out_md,
        "--out-json",
        out_json,
    ]
    _run(args)
    return json.dumps({"status": "ok", "output_file": out_json})


def _dispatch_report_gen(inp: dict[str, Any], out_dir: Path) -> str:
    out_path = inp.get("out") or str(out_dir / "report.md")
    audience = inp.get("audience", "gis")
    args = [
        _PYTHON,
        "-m",
        "skills.report_gen.report_gen",
        "generate",
        "--backlog",
        inp["backlog"],
        "--audience",
        audience,
        "--out",
        out_path,
    ]
    if inp.get("sscf_benchmark"):
        args += ["--sscf-benchmark", inp["sscf_benchmark"]]
    if inp.get("nist_review"):
        args += ["--nist-review", inp["nist_review"]]
    if inp.get("org_alias"):
        args += ["--org-alias", inp["org_alias"]]
    if inp.get("dry_run"):
        args.append("--dry-run")
    _run(args)
    return json.dumps({"status": "ok", "output_file": out_path})


def _dispatch_sscf_benchmark(inp: dict[str, Any], out_dir: Path) -> str:
    out_path = inp.get("out") or str(out_dir / "sscf_report.json")
    sscf_index = _REPO / "config/sscf_control_index.yaml"
    args = [
        _PYTHON,
        "-m",
        "skills.sscf_benchmark.sscf_benchmark",
        "benchmark",
        "--backlog",
        inp["backlog"],
        "--sscf-index",
        str(sscf_index),
        "--out",
        out_path,
    ]
    _run(args)
    return json.dumps({"status": "ok", "output_file": out_path})


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

_DISPATCHERS = {
    "sfdc_connect_collect": _dispatch_sfdc_connect,
    "oscal_assess_assess": _dispatch_oscal_assess,
    "oscal_gap_map": _dispatch_gap_map,
    "sscf_benchmark_benchmark": _dispatch_sscf_benchmark,
    "report_gen_generate": _dispatch_report_gen,
}


def dispatch(name: str, input_dict: dict[str, Any]) -> str:
    """Dispatch a named tool call; return JSON result string."""
    handler = _DISPATCHERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {list(_DISPATCHERS)}")
    org = input_dict.get("org", "unknown-org")
    out_dir = _out_dir(org)
    return handler(input_dict, out_dir)
