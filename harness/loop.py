"""
harness/loop.py — Agentic orchestration loop for OSCAL/SSCF assessments.

Entry point:  agent-loop run [OPTIONS]

The orchestrator (claude-opus-4-6) is called in a tool_use loop:
  1. Load agent config (mission.md + orchestrator.md as system prompt)
  2. Prepend prior org assessment memory to the first user message
  3. Drive the Anthropic messages API until stop_reason == "end_turn"
  4. Dispatch each tool_use block via harness.tools.dispatch()
  5. Gate on critical/fail findings before writing final output
  6. Persist assessment metrics to Qdrant via Mem0
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv

from harness.agents import ORCHESTRATOR
from harness.memory import build_client, load_memories, save_assessment
from harness.tools import ALL_TOOLS, dispatch

_REPO = Path(__file__).resolve().parents[1]

# Load .env at import time so ANTHROPIC_API_KEY and SF_* vars are in os.environ
# before Click reads envvar= options or os.getenv() is called anywhere.
load_dotenv(_REPO / ".env")
_MAX_TURNS = 20  # hard stop to prevent runaway loops

# ---------------------------------------------------------------------------
# Critical/fail gate helpers
# ---------------------------------------------------------------------------


def _extract_critical_fails(gap_analysis_path: str | None) -> list[str]:
    """Return control IDs that are both status=fail and severity=critical."""
    if not gap_analysis_path:
        return []
    path = Path(gap_analysis_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [
            f["control_id"]
            for f in data.get("findings", [])
            if f.get("status") == "fail" and f.get("severity") == "critical"
        ]
    except Exception:  # noqa: BLE001
        return []


def _extract_score(sscf_report_path: str | None) -> float:
    """Extract overall_score from sscf_report.json, default 0.0 on failure."""
    if not sscf_report_path:
        return 0.0
    path = Path(sscf_report_path)
    if not path.exists():
        return 0.0
    try:
        data = json.loads(path.read_text())
        return float(data.get("overall_score", 0.0))
    except Exception:  # noqa: BLE001
        return 0.0


# ---------------------------------------------------------------------------
# Tool error handler — your contribution here
# ---------------------------------------------------------------------------


def _handle_tool_error(
    tool_name: str,
    tool_input: dict[str, Any],
    error: Exception,
) -> str:
    """Decide how to respond when a CLI tool dispatch fails.

    This function is called whenever dispatch() raises a RuntimeError.
    It returns a string that is fed back to the orchestrator as the tool_result
    content — the LLM will see this and decide how to proceed.

    Your task: implement the error handling strategy that best fits the
    security assessment context. Consider these trade-offs:

    Option A — Halt + surface (safest):
        raise the error immediately so the human sees it.
        Risk: one transient failure aborts the entire assessment.
        Best for: production runs, critical-path tools.

    Option B — Return structured error (recommended for resilience):
        return a JSON error payload; let the orchestrator decide next step.
        The LLM can narrow scope, skip optional stages, or ask the human.
        Best for: multi-stage pipelines where some stages are optional.

    Option C — Retry with narrowed scope (advanced):
        modify tool_input (e.g., scope="auth" instead of "all") and retry once.
        Useful when "all" scope times out but partial scope succeeds.
        Risk: hiding a real failure in a retry loop.

    IMPORTANT (security constraint): never silently swallow errors on
    sfdc_connect_collect or oscal_assess_assess — a hidden collector failure
    could cause a false-pass assessment (no findings because no data collected).

    TODO: implement your chosen strategy below (5–10 lines).
    Signature: (tool_name: str, tool_input: dict, error: Exception) -> str
    The return value is a JSON string fed to the orchestrator as the tool result.
    """
    # Critical pipeline stages: halt immediately.
    # A hidden collector or assessor failure produces zero findings → false-pass assessment.
    _CRITICAL_TOOLS = {"sfdc_connect_collect", "oscal_assess_assess"}
    if tool_name in _CRITICAL_TOOLS:
        raise RuntimeError(f"Critical tool '{tool_name}' failed — aborting to prevent false-pass assessment.\n{error}")
    # Downstream stages (gap_map, benchmark): return structured error payload.
    # The orchestrator can report partial results rather than aborting the whole run.
    return json.dumps({"status": "error", "tool": tool_name, "message": str(error)})


# ---------------------------------------------------------------------------
# Message loop
# ---------------------------------------------------------------------------


def _run_loop(
    task: str,
    env: str,
    org: str,
    dry_run: bool,
    approve_critical: bool,
    api_key: str | None,
) -> dict[str, Any]:
    """Core agentic loop. Returns result dict with score, status, output paths."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic") from exc

    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # --- Memory: load prior assessments for this org ---
    mem_client = None
    memory_context = ""
    try:
        mem_client = build_client()
        memory_context = load_memories(mem_client, org)
        click.echo(f"  [memory] {memory_context.splitlines()[0]}", err=True)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"  [memory] unavailable: {exc}", err=True)

    # --- Build initial user message ---
    user_content = task
    if memory_context:
        user_content = f"{memory_context}\n\n---\n\n{task}"

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]

    # Track key output file paths as the pipeline progresses
    state: dict[str, Any] = {
        "gap_analysis": None,
        "backlog": None,
        "sscf_report": None,
        "turns": 0,
    }

    # --- Agentic loop ---
    for turn in range(_MAX_TURNS):
        state["turns"] = turn + 1

        response = client.messages.create(
            model=ORCHESTRATOR.model,
            max_tokens=4096,
            # cache_control marks the system prompt for prompt caching.
            # Across the 20-turn ReAct loop the system prompt (mission.md +
            # orchestrator.md, ~3 KB) is re-sent every turn. Caching it cuts
            # token cost by ~90% on the system prompt portion after the first turn.
            system=[
                {
                    "type": "text",
                    "text": ORCHESTRATOR.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=ALL_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            # Extract final text summary
            final_text = " ".join(block.text for block in response.content if hasattr(block, "text"))
            state["summary"] = final_text
            break

        if response.stop_reason == "max_tokens":
            click.echo("WARNING: Response truncated (max_tokens reached).", err=True)
            state["summary"] = "[truncated]"
            break

        if response.stop_reason != "tool_use":
            click.echo(f"WARNING: Unexpected stop_reason: {response.stop_reason}", err=True)
            state["summary"] = f"[stop: {response.stop_reason}]"
            break

        # --- Process tool_use blocks ---
        tool_results: list[dict[str, Any]] = []

        for block in response.content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue

            click.echo(f"  [tool] {block.name}({json.dumps(block.input, separators=(',', ':'))})", err=True)

            try:
                result_str = dispatch(block.name, block.input)
            except Exception as exc:  # noqa: BLE001
                result_str = _handle_tool_error(block.name, block.input, exc)

            # Track output files for downstream steps and final gate
            try:
                result_data = json.loads(result_str)
                out_file = result_data.get("output_file")
                if out_file:
                    name = block.name
                    if name == "oscal_assess_assess":
                        state["gap_analysis"] = out_file
                    elif name == "oscal_gap_map":
                        state["backlog"] = out_file
                    elif name == "sscf_benchmark_benchmark":
                        state["sscf_report"] = out_file
            except (json.JSONDecodeError, AttributeError):
                pass

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                }
            )

        # Append assistant turn + tool results as next user turn
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    else:
        click.echo(f"WARNING: Reached max turns ({_MAX_TURNS}). Loop hard-stopped.", err=True)
        state["summary"] = f"[max_turns={_MAX_TURNS} exceeded]"

    # --- Critical/fail gate ---
    critical_fails = _extract_critical_fails(state.get("gap_analysis"))
    score = _extract_score(state.get("sscf_report"))

    if critical_fails and not dry_run and not approve_critical:
        click.echo(
            f"\nBLOCKED: {len(critical_fails)} critical/fail finding(s) require human review:\n"
            + "\n".join(f"  - {c}" for c in critical_fails)
            + "\n\nRe-run with --approve-critical to proceed past this gate.",
            err=True,
        )
        sys.exit(2)

    # --- Persist to memory ---
    if mem_client is not None:
        assessment_id = f"sfdc-assess-{org}-{env}-loop"
        save_assessment(mem_client, org, assessment_id, score, critical_fails)

    state["score"] = score
    state["critical_fails"] = critical_fails
    return state


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """agent-loop — agentic OSCAL/SSCF assessment orchestrator."""


@cli.command()
@click.option(
    "--env",
    default="dev",
    type=click.Choice(["dev", "test", "prod"]),
    show_default=True,
    help="Target environment label.",
)
@click.option(
    "--org",
    default="unknown-org",
    show_default=True,
    help="Org alias used for output directory naming and memory scoping.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Use dry-run mode for all CLIs (no real Salesforce connection, no real API spend on tools).",
)
@click.option(
    "--approve-critical",
    is_flag=True,
    help="Bypass the critical/fail gate and write output even if critical findings exist.",
)
@click.option("--task", default=None, help="Override the default assessment task prompt sent to the orchestrator.")
@click.option(
    "--api-key",
    default=None,
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var).",
)
def run(env: str, org: str, dry_run: bool, approve_critical: bool, task: str | None, api_key: str | None) -> None:
    """Run the agentic assessment loop against a Salesforce org.

    Orchestrates: sfdc-connect → oscal-assess → oscal_gap_map → sscf-benchmark
    via claude-opus-4-6 tool_use, with Mem0+Qdrant session memory.

    Example (dry-run, no real org or API credits):
        agent-loop run --dry-run --env dev --org weak-org-dry-run
    """
    dry_tag = " [DRY-RUN]" if dry_run else ""
    click.echo(f"\nagent-loop{dry_tag}: org={org} env={env}")

    if task is None:
        dry_note = " Use dry_run=true for all tool calls (no real Salesforce connection)." if dry_run else ""
        dry_gate_note = (
            (
                " This is a dry run — proceed through all pipeline stages including report generation "
                "without waiting for human review of findings."
            )
            if dry_run
            else ""
        )
        task = (
            f"Run a full OSCAL/SSCF security assessment for Salesforce org '{org}' "
            f"in environment '{env}'.{dry_note}{dry_gate_note}\n\n"
            f"IMPORTANT: Pass org='{org}' to every tool call so all outputs land in the same directory.\n\n"
            "Pipeline:\n"
            f"1. Call sfdc_connect_collect (org='{org}', scope='all') to gather org configuration.\n"
            f"2. Call oscal_assess_assess (org='{org}') to produce gap_analysis.json.\n"
            f"3. Call oscal_gap_map (org='{org}') with the gap_analysis output to produce backlog.json.\n"
            f"4. Call sscf_benchmark_benchmark (org='{org}') with the backlog to produce the SSCF scorecard.\n"
            f"5. Call report_gen_generate twice: once with audience='app-owner' (out ending in .md) "
            f"and once with audience='gis' (out ending in .md), both using the backlog and sscf_benchmark paths.\n\n"
            "Return a final summary with: overall_score, overall_status (red/amber/green), "
            "count of critical/fail findings, and the top 3 remediation priorities."
        )

    click.echo(f"  task: {task[:120]}{'...' if len(task) > 120 else ''}", err=True)

    state = _run_loop(
        task=task,
        env=env,
        org=org,
        dry_run=dry_run,
        approve_critical=approve_critical,
        api_key=api_key,
    )

    # --- Final output ---
    click.echo("\n" + "=" * 60)
    click.echo(f"Assessment complete ({state['turns']} turn(s))")
    click.echo(f"overall_score : {state.get('score', 0.0):.1%}")
    critical_fails = state.get("critical_fails", [])
    click.echo(f"critical_fails: {len(critical_fails)}")
    if critical_fails:
        for c in critical_fails:
            click.echo(f"  - {c}")
    click.echo("=" * 60)

    summary = state.get("summary", "")
    if summary:
        click.echo(f"\nOrchestrator summary:\n{summary}")

    # Write consolidated result JSON
    out_dir = _REPO / "docs" / "oscal-salesforce-poc" / "generated" / org
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "loop_result.json"
    result_path.write_text(
        json.dumps(
            {
                "org": org,
                "env": env,
                "dry_run": dry_run,
                "turns": state["turns"],
                "overall_score": state.get("score", 0.0),
                "critical_fails": critical_fails,
                "gap_analysis": state.get("gap_analysis"),
                "backlog": state.get("backlog"),
                "sscf_report": state.get("sscf_report"),
                "summary": state.get("summary", ""),
            },
            indent=2,
        )
    )
    click.echo(f"\nResult written → {result_path}")


if __name__ == "__main__":
    cli()
