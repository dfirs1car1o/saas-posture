# Secure Coding Standard (Azure + Multi-Agent)

This standard is mandatory for all code in this repository.

## 1) Secrets and Credentials
- Never commit secrets, tokens, API keys, or connection strings.
- Use managed identity + Key Vault for runtime secrets.
- Use GitHub OIDC for Azure authentication in CI/CD.
- Rotate credentials on schedule and after incidents.

## 2) Input/Output Safety
- Validate and constrain all external input (API body, tool output, case artifacts).
- Enforce schema checks for action payloads.
- Reject unknown fields by default.
- Apply output filtering/redaction for sensitive findings.

## 3) Prompt and Tool Safety
- Separate system policies from user content.
- Treat tool output as untrusted.
- Require explicit allowlists for outbound tools/integrations.
- Add approval gates for high-impact actions (containment, blocking, deletion).

## 4) Least Privilege
- Service identities get minimum required permissions only.
- No broad contributor/owner access for app identities.
- Segregate dev/prod identities and resources.

## 5) Observability and Audit
- Correlation ID required across request -> workflow -> tool call.
- Log security-relevant events (auth failures, policy denials, action approvals).
- Never log raw secrets or sensitive evidence contents.

## 6) Dependency and Code Hygiene
- Pin dependency ranges and review updates.
- Run static checks on every PR.
- Fail CI on security check failures.
- Maintain changelog entries for all behavior-affecting changes.

## 7) Well-Architected Alignment
- Security: least privilege, secret management, defense in depth.
- Reliability: retry strategy, fallback model routing, failure isolation.
- Performance: bounded timeouts and async queue workflows.
- Cost Optimization: model routing policy and budget-aware controls.
- Operational Excellence: runbooks, alerts, and rollback drills.

## 8) PR Minimum Requirements
- [ ] Threat/risk note included.
- [ ] Rollback/backout steps included.
- [ ] RV (release validation) commands included.
- [ ] `CHANGELOG.md` updated.
- [ ] Inline reviewer checks pass (`pr-inline-review` + `security-checks`).
- [ ] CODEOWNER review completed.
