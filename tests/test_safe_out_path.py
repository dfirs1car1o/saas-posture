"""
Tests for harness.tools._safe_out_path() path-traversal guard.

Covers:
  1. Valid paths inside _ARTIFACT_ROOT → accepted
  2. Valid paths inside _APEX_ROOT → accepted
  3. Path traversal via ``../../outside.json`` → ValueError
  4. Absolute path outside repo → ValueError
  5. None input falls back to default → accepted
  6. Dated run subdirectory → accepted
"""

from __future__ import annotations

import pytest

from harness.tools import _APEX_ROOT, _ARTIFACT_ROOT, _safe_out_path

# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_valid_artifact_root_path() -> None:
    valid = str(_ARTIFACT_ROOT / "my-org" / "2026-03-11" / "backlog.json")
    result = _safe_out_path(valid, _ARTIFACT_ROOT / "fallback.json")
    assert result == valid


def test_valid_apex_root_path() -> None:
    valid = str(_APEX_ROOT / "my-org" / "fix_mfa.apex")
    result = _safe_out_path(valid, _APEX_ROOT / "fallback.apex")
    assert result == valid


def test_none_uses_default() -> None:
    default = _ARTIFACT_ROOT / "my-org" / "2026-03-11" / "gap_analysis.json"
    result = _safe_out_path(None, default)
    assert result == str(default.resolve())


def test_dated_subdirectory() -> None:
    path = str(_ARTIFACT_ROOT / "cyber-coach-dev" / "2026-03-11" / "loop_result.json")
    result = _safe_out_path(path, _ARTIFACT_ROOT / "fallback.json")
    assert "2026-03-11" in result


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


def test_path_traversal_rejected() -> None:
    traversal = str(_ARTIFACT_ROOT / "my-org" / ".." / ".." / ".." / "etc" / "passwd")
    with pytest.raises(ValueError, match="outside the allowed artifact root"):
        _safe_out_path(traversal, _ARTIFACT_ROOT / "fallback.json")


def test_absolute_path_outside_repo_rejected() -> None:
    with pytest.raises(ValueError, match="outside the allowed artifact root"):
        _safe_out_path("/tmp/evil.json", _ARTIFACT_ROOT / "fallback.json")


def test_relative_escape_rejected() -> None:
    # Attempt to write to repo root (outside generated/)
    import os

    repo_root_file = os.path.join(str(_ARTIFACT_ROOT), "..", "..", "..", "README.md")
    with pytest.raises(ValueError, match="outside the allowed artifact root"):
        _safe_out_path(repo_root_file, _ARTIFACT_ROOT / "fallback.json")
