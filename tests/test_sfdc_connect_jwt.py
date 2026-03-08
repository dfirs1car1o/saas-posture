"""
Unit tests for JWT Bearer Auth in sfdc-connect.
No live Salesforce org required.
"""

from __future__ import annotations

import pytest


def test_resolve_auth_method(monkeypatch):
    """CLI flag takes precedence over env var, which takes precedence over default 'soap'."""
    from skills.sfdc_connect.sfdc_connect import AUTH_METHOD_JWT, AUTH_METHOD_SOAP, _resolve_auth_method

    # CLI flag wins regardless of env
    monkeypatch.delenv("SF_AUTH_METHOD", raising=False)
    assert _resolve_auth_method("jwt") == AUTH_METHOD_JWT

    # Env var used when no CLI flag
    monkeypatch.setenv("SF_AUTH_METHOD", "jwt")
    assert _resolve_auth_method(None) == AUTH_METHOD_JWT

    # Default is soap when neither CLI flag nor env var is set
    monkeypatch.delenv("SF_AUTH_METHOD", raising=False)
    assert _resolve_auth_method(None) == AUTH_METHOD_SOAP


def test_check_env_jwt_missing_vars(monkeypatch):
    """_check_env exits 1 when required JWT env vars are absent."""
    from skills.sfdc_connect.sfdc_connect import AUTH_METHOD_JWT, _check_env

    monkeypatch.delenv("SF_USERNAME", raising=False)
    monkeypatch.delenv("SF_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SF_PRIVATE_KEY_PATH", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        _check_env(AUTH_METHOD_JWT)
    assert exc_info.value.code == 1


def test_auth_dry_run_jwt(monkeypatch):
    """auth --dry-run --auth-method jwt fails when only SOAP vars are set."""
    from click.testing import CliRunner

    from skills.sfdc_connect.sfdc_connect import cli

    # SOAP vars present, JWT-specific vars absent
    monkeypatch.setenv("SF_USERNAME", "test@example.com")
    monkeypatch.setenv("SF_PASSWORD", "password")
    monkeypatch.setenv("SF_SECURITY_TOKEN", "token")
    monkeypatch.delenv("SF_AUTH_METHOD", raising=False)
    monkeypatch.delenv("SF_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SF_PRIVATE_KEY_PATH", raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "--dry-run", "--auth-method", "jwt"])
    assert result.exit_code != 0
