# AGENTS.md — Master Agent Reference

This file is the canonical reference for all agents in this system. Each agent has a definition file in agents/. Read that file for full context, tools, and prompting patterns.

## Agent Roster

| Agent | File | Model | Primary Role |
|---|---|---|---|
| orchestrator | agents/orchestrator.md | claude-opus-4-6 | Routes tasks, assembles final output, manages agent loop |
| collector | agents/collector.md | claude-sonnet-4-6 | Extracts Salesforce org config via API and CLI |
| assessor | agents/assessor.md | claude-sonnet-4-6 | Maps findings to OSCAL/SBS/SSCF controls |
| reporter | agents/reporter.md | claude-haiku-4-5 | Generates DOCX/MD/JSON outputs for app owners |
| nist-reviewer | agents/nist-reviewer.md | claude-sonnet-4-6 | Validates all outputs against NIST AI RMF |
| security-reviewer | agents/security-reviewer.md | claude-sonnet-4-6 | AppSec + DevSecOps review of CI/CD, workflows, and skill CLIs |

## Skill Roster

| Skill | Directory | What It Does |
|---|---|---|
| sfdc-connect | skills/sfdc-connect/ | Authenticates and queries a Salesforce org via REST/Metadata API |
| oscal-assess | skills/oscal-assess/ | Runs OSCAL gap mapping against SBS control catalog |
| sscf-benchmark | skills/sscf-benchmark/ | Benchmarks findings against CSA SSCF control index |
| report-gen | skills/report-gen/ | Generates DOCX, Markdown, and JSON governance outputs |

## Context Modes

| Mode | File | When To Load |
|---|---|---|
| assess | contexts/assess.md | Running a live or historical assessment |
| review | contexts/review.md | Reviewing agent outputs, performing QA |
| research | contexts/research.md | Investigating a CVE, framework, or control definition |

## Model Assignment Rationale

- Orchestrator uses Opus: it makes routing decisions with incomplete information and assembles final multi-part outputs.
- Collector and Assessor use Sonnet: API interaction, structured data extraction, and control mapping are mid-complexity tasks.
- Reporter uses Haiku: templated output generation from structured data is low-complexity and high-volume.
- NIST Reviewer uses Sonnet: regulatory framework review requires depth but not Opus-level synthesis.
- Security Reviewer uses Sonnet: adversarial security analysis requires depth; no tool calls needed (text-only).

## Agent Loop Model

```
human message
  -> orchestrator receives
  -> orchestrator identifies task type
  -> orchestrator routes to specialist agents in sequence
  -> each agent calls skills (CLIs), parses output, returns structured result
  -> orchestrator assembles findings into output schema
  -> reporter formats for audience
  -> nist-reviewer validates
  -> orchestrator returns to human
```

## Proactive Heartbeat (Future)

The orchestrator can be scheduled to run proactively:
- Weekly: run sscf-benchmark against last known backlog, flag new drift.
- On CVE feed update: research.md context + nist-reviewer to assess impact.
- On org config change (webhook): collector + assessor triggered automatically.

## Escalation Rules

- Any finding with severity=critical and status=fail must surface to human before reporter finalizes.
- Any NIST AI RMF gap identified by nist-reviewer blocks output until human acknowledges.
- Any CRITICAL or HIGH finding from security-reviewer on a workflow or skill change blocks merge.
- If orchestrator cannot determine org target, it asks human before calling sfdc-connect.
