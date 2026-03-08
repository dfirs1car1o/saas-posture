"""
tests/test_workday_connect.py — Unit tests for workday_connect.

Uses `responses` library to intercept HTTP calls — no live Workday tenant required.
All tests run in CI with no network access.
"""

from __future__ import annotations

import re

import pytest
import responses as resp_lib

from skills.workday_connect.workday_connect import (
    _assess_soap_result,
    clear_token_cache,
    collect_manual,
    collect_raas,
    collect_rest,
    collect_soap,
    get_oauth_token,
    load_catalog,
    print_dry_run_plan,
    run_collect,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

TOKEN_URL = "https://acme.workday.com/ccx/oauth2/acme/token"
BASE_URL = "https://acme.workday.com"
TENANT = "acme"
API_VERSION = "v40.0"
FAKE_TOKEN = "fake-access-token-abc123"

# Minimal SOAP XML responses for each control group
_PW_RULES_XML = """\
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:wd="urn:com.workday/bsvc">
  <env:Body>
    <wd:Get_Password_Rules_Response>
      <wd:Response_Data>
        <wd:Password_Rules>
          <wd:Minimum_Password_Length>14</wd:Minimum_Password_Length>
          <wd:Password_Expiration_Days>60</wd:Password_Expiration_Days>
          <wd:Password_History_Count>24</wd:Password_History_Count>
          <wd:Lockout_Threshold>3</wd:Lockout_Threshold>
          <wd:Lockout_Duration_Minutes>30</wd:Lockout_Duration_Minutes>
        </wd:Password_Rules>
      </wd:Response_Data>
    </wd:Get_Password_Rules_Response>
  </env:Body>
</env:Envelope>"""

_PW_RULES_FAIL_XML = """\
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:wd="urn:com.workday/bsvc">
  <env:Body>
    <wd:Get_Password_Rules_Response>
      <wd:Response_Data>
        <wd:Password_Rules>
          <wd:Minimum_Password_Length>6</wd:Minimum_Password_Length>
          <wd:Password_Expiration_Days>180</wd:Password_Expiration_Days>
          <wd:Password_History_Count>3</wd:Password_History_Count>
          <wd:Lockout_Threshold>10</wd:Lockout_Threshold>
          <wd:Lockout_Duration_Minutes>5</wd:Lockout_Duration_Minutes>
        </wd:Password_Rules>
      </wd:Response_Data>
    </wd:Get_Password_Rules_Response>
  </env:Body>
</env:Envelope>"""

_MFA_XML = """\
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:wd="urn:com.workday/bsvc">
  <env:Body>
    <wd:Get_Authentication_Policies_Response>
      <wd:Response_Data>
        <wd:Authentication_Policy>
          <wd:Authentication_Policy_Name>Default Policy</wd:Authentication_Policy_Name>
          <wd:Multi_Factor_Authentication_Required>true</wd:Multi_Factor_Authentication_Required>
        </wd:Authentication_Policy>
      </wd:Response_Data>
    </wd:Get_Authentication_Policies_Response>
  </env:Body>
</env:Envelope>"""

_TLS_XML = """\
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:wd="urn:com.workday/bsvc">
  <env:Body>
    <wd:Get_Tenant_Setup_Security_Response>
      <wd:Response_Data>
        <wd:Tenant_Setup_Security>
          <wd:Require_TLS_For_API>true</wd:Require_TLS_For_API>
        </wd:Tenant_Setup_Security>
      </wd:Response_Data>
    </wd:Get_Tenant_Setup_Security_Response>
  </env:Body>
</env:Envelope>"""

_RETENTION_XML = """\
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:wd="urn:com.workday/bsvc">
  <env:Body>
    <wd:Get_Audit_Retention_Settings_Response>
      <wd:Response_Data>
        <wd:Audit_Log_Retention_Days>730</wd:Audit_Log_Retention_Days>
      </wd:Response_Data>
    </wd:Get_Audit_Retention_Settings_Response>
  </env:Body>
</env:Envelope>"""


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear OAuth token cache and SOAP cache before each test."""
    clear_token_cache()
    # Clear SOAP cache
    from skills.workday_connect import workday_connect

    workday_connect._soap_cache.clear()
    yield


def _token_stub():
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"access_token": FAKE_TOKEN, "expires_in": 3600},
        status=200,
    )


def _make_ctrl(ctrl_id: str, method: str = "soap", operation: str = "Get_Password_Rules") -> dict:
    return {
        "id": ctrl_id,
        "title": f"Test control {ctrl_id}",
        "group_id": "con",
        "severity": "high",
        "collection_method": method,
        "soap_service": "Security_Configuration",
        "soap_operation": operation,
        "raas_report": "Test_Report",
        "rest_endpoint": "/staffing/v6/workers",
        "sscf_control": "SSCF-IAM-001",
    }


# ---------------------------------------------------------------------------
# OAuth token tests
# ---------------------------------------------------------------------------


@resp_lib.activate
def test_get_oauth_token_success():
    _token_stub()
    token = get_oauth_token("client-id", "client-secret", TOKEN_URL)
    assert token == FAKE_TOKEN
    assert len(resp_lib.calls) == 1


@resp_lib.activate
def test_get_oauth_token_cached():
    """Second call should use cache — only one HTTP request fired."""
    _token_stub()
    t1 = get_oauth_token("client-id", "client-secret", TOKEN_URL)
    t2 = get_oauth_token("client-id", "client-secret", TOKEN_URL)
    assert t1 == t2 == FAKE_TOKEN
    assert len(resp_lib.calls) == 1  # cached — no second request


@resp_lib.activate
def test_get_oauth_token_failure():
    resp_lib.add(resp_lib.POST, TOKEN_URL, status=401, json={"error": "unauthorized"})
    with pytest.raises(RuntimeError, match="OAuth token acquisition failed"):
        get_oauth_token("bad-id", "bad-secret", TOKEN_URL)


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------


def test_load_catalog_returns_30_controls():
    controls = load_catalog()
    assert len(controls) == 30, f"Expected 30 controls, got {len(controls)}"


def test_load_catalog_all_have_required_fields():
    controls = load_catalog()
    for ctrl in controls:
        assert "id" in ctrl
        assert "collection_method" in ctrl
        assert ctrl["collection_method"] in ("soap", "soap+oauth", "raas", "rest", "manual")


# ---------------------------------------------------------------------------
# SOAP assessment tests
# ---------------------------------------------------------------------------


def test_assess_soap_password_length_pass():
    result = _assess_soap_result("WD-CON-001", _PW_RULES_XML)
    assert result["status"] == "pass"
    assert "14" in result["observed_value"]


def test_assess_soap_password_length_fail():
    result = _assess_soap_result("WD-CON-001", _PW_RULES_FAIL_XML)
    assert result["status"] == "fail"
    assert "6" in result["observed_value"]


def test_assess_soap_password_expiry_pass():
    result = _assess_soap_result("WD-CON-002", _PW_RULES_XML)
    assert result["status"] == "pass"


def test_assess_soap_lockout_pass():
    result = _assess_soap_result("WD-CON-004", _PW_RULES_XML)
    assert result["status"] == "pass"


def test_assess_soap_lockout_fail():
    result = _assess_soap_result("WD-CON-004", _PW_RULES_FAIL_XML)
    assert result["status"] == "fail"


def test_assess_soap_mfa_required():
    result = _assess_soap_result("WD-IAM-003", _MFA_XML)
    assert result["status"] == "pass"


def test_assess_soap_tls_required():
    result = _assess_soap_result("WD-CKM-001", _TLS_XML)
    assert result["status"] == "pass"


def test_assess_soap_audit_retention_pass():
    result = _assess_soap_result("WD-LOG-005", _RETENTION_XML)
    assert result["status"] == "pass"
    assert "730" in result["observed_value"]


# ---------------------------------------------------------------------------
# collect_soap tests
# ---------------------------------------------------------------------------


@resp_lib.activate
def test_collect_soap_permission_denied():
    soap_url = f"{BASE_URL}/ccx/service/{TENANT}/Security_Configuration/{API_VERSION}"
    resp_lib.add(resp_lib.POST, soap_url, status=403, body="Forbidden")
    ctrl = _make_ctrl("WD-CON-001")
    result = collect_soap(ctrl, BASE_URL, TENANT, FAKE_TOKEN, API_VERSION)
    assert result["status"] == "partial"
    assert result["platform_data"]["soap_error"] == "PERMISSION_DENIED: domain not granted to ISSG"


@resp_lib.activate
def test_collect_soap_success_pass():
    soap_url = f"{BASE_URL}/ccx/service/{TENANT}/Security_Configuration/{API_VERSION}"
    resp_lib.add(resp_lib.POST, soap_url, status=200, body=_PW_RULES_XML, content_type="text/xml")
    ctrl = _make_ctrl("WD-CON-001")
    result = collect_soap(ctrl, BASE_URL, TENANT, FAKE_TOKEN, API_VERSION)
    assert result["status"] == "pass"
    assert result["platform_data"]["collection_method"] == "soap"


# ---------------------------------------------------------------------------
# collect_raas tests
# ---------------------------------------------------------------------------


@resp_lib.activate
def test_collect_raas_not_configured():
    raas_url = f"{BASE_URL}/ccx/service/customreport2/{TENANT}/Test_Report?format=json"
    resp_lib.add(resp_lib.GET, raas_url, status=404)
    ctrl = _make_ctrl("WD-IAM-001", method="raas")
    result = collect_raas(ctrl, BASE_URL, TENANT, FAKE_TOKEN)
    assert result["status"] == "not_applicable"
    assert result["platform_data"]["raas_available"] is False


@resp_lib.activate
def test_collect_raas_success():
    raas_url = f"{BASE_URL}/ccx/service/customreport2/{TENANT}/Test_Report?format=json"
    resp_lib.add(resp_lib.GET, raas_url, status=200, json={"Report_Entry": [{"id": "grp1"}, {"id": "grp2"}]})
    ctrl = _make_ctrl("WD-IAM-001", method="raas")
    result = collect_raas(ctrl, BASE_URL, TENANT, FAKE_TOKEN)
    assert result["status"] == "partial"
    assert result["platform_data"]["record_count"] == 2


# ---------------------------------------------------------------------------
# collect_rest tests
# ---------------------------------------------------------------------------


@resp_lib.activate
def test_collect_rest_workers():
    rest_url = f"{BASE_URL}/ccx/api/staffing/v6/workers"
    resp_lib.add(resp_lib.GET, rest_url, status=200, json={"data": [{"id": "w1"}, {"id": "w2"}]})
    ctrl = _make_ctrl("WD-IAM-007", method="rest")
    ctrl["rest_endpoint"] = "/staffing/v6/workers"
    result = collect_rest(ctrl, BASE_URL, FAKE_TOKEN)
    assert result["status"] == "partial"
    assert result["platform_data"]["worker_count"] == 2


# ---------------------------------------------------------------------------
# collect_manual test
# ---------------------------------------------------------------------------


def test_collect_manual_not_applicable():
    ctrl = _make_ctrl("WD-CKM-002", method="manual")
    ctrl["title"] = "BYOK Key Management"
    result = collect_manual(ctrl)
    assert result["status"] == "not_applicable"
    assert "BYOK" in result["platform_data"]["collection_method_note"]


# ---------------------------------------------------------------------------
# dry-run test
# ---------------------------------------------------------------------------


def test_dry_run_prints_plan(capsys):
    print_dry_run_plan("acme_dpt1", "acme-dry-run")
    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out
    assert "acme_dpt1" in captured.out
    assert "WD-IAM-001" in captured.out
    assert "WD-CKM-002" in captured.out


# ---------------------------------------------------------------------------
# Full run_collect integration test (mocked HTTP)
# ---------------------------------------------------------------------------


@resp_lib.activate
def test_run_collect_writes_output(tmp_path):
    # Stub SOAP endpoints for both services used by the catalog
    for service in ("Security_Configuration", "Human_Resources"):
        soap_url = f"{BASE_URL}/ccx/service/{TENANT}/{service}/{API_VERSION}"
        resp_lib.add(resp_lib.POST, soap_url, status=200, body=_PW_RULES_XML, content_type="text/xml")

    # Stub REST endpoint
    rest_url = f"{BASE_URL}/ccx/api/staffing/v6/workers"
    resp_lib.add(resp_lib.GET, rest_url, status=200, json={"data": []})

    # Stub all RaaS endpoints as 404 (not pre-configured) using regex pattern
    resp_lib.add(resp_lib.GET, re.compile(r".*/customreport2/.*"), status=404)

    out_path = tmp_path / "workday_raw.json"
    output = run_collect(BASE_URL, TENANT, FAKE_TOKEN, API_VERSION, "test-org", "dev", "Test Owner", out_path)

    assert out_path.exists()
    assert output["schema_version"] == "2.0"
    assert output["platform"] == "workday"
    assert len(output["findings"]) == 30
    # Manual controls are not_applicable
    ckm2 = next(f for f in output["findings"] if f["control_id"] == "WD-CKM-002")
    assert ckm2["status"] == "not_applicable"
