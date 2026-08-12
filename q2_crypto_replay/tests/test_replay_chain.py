"""
Q2 HMAC Transaction Replay Test Suite

Tests:
1. test_secure_mode_rejects_replay_with_409 (@pytest.mark.secure)
2. test_tampered_body_rejects_with_401 (@pytest.mark.secure)
3. test_stale_timestamp_rejected_422 (@pytest.mark.secure)
4. test_vulnerable_mode_emits_high_risk_alert (@pytest.mark.vulnerable)
"""

import os
import json
import time
import pytest
import requests
from pathlib import Path

from q2_crypto_replay.framework.chain_client import CryptoChainClient
from q2_crypto_replay.framework.hmac_signer import compute_hmac_signature, canonicalize_json
from q2_crypto_replay.framework.vuln_reporter import VulnerabilityReporter

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

GATEWAY_URL = "http://localhost:8082"

@pytest.fixture(autouse=True)
def ensure_gateway_secure_default():
    """Ensure gateway is set to SECURE mode by default before each test."""
    requests.post(f"{GATEWAY_URL}/v1/config/mode", json={"mode": "SECURE"})
    yield
    requests.post(f"{GATEWAY_URL}/v1/config/mode", json={"mode": "SECURE"})

@pytest.fixture
def vulnerable_gateway():
    """Switch gateway to VULNERABLE mode for vulnerable security tests."""
    resp = requests.post(f"{GATEWAY_URL}/v1/config/mode", json={"mode": "VULNERABLE"})
    assert resp.status_code == 200
    yield
    requests.post(f"{GATEWAY_URL}/v1/config/mode", json={"mode": "SECURE"})

@pytest.mark.secure
def test_secure_mode_rejects_replay_with_409():
    """Verifies SECURE mode gateway returns 409 Conflict on replay."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {
        "action": "TRANSFER",
        "amount": 500.00,
        "currency": "USD",
        "recipient": "acc_884920"
    }

    result = client.execute_signed_put_and_replay(challenge, payload)

    # In SECURE mode, initial request succeeds (200), replay is rejected (409)
    assert result.initial_status == 200
    assert result.replay_status == 409
    assert result.replay_response.get("error") == "REPLAY_DETECTED"

@pytest.mark.secure
def test_tampered_body_rejects_with_401():
    """Verifies single byte mutation in body invalidates HMAC signature using server timestamp."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {"action": "TRANSFER", "amount": 100.00, "recipient": "acc_101"}
    timestamp_micros = challenge.server_timestamp_micros
    mac = compute_hmac_signature(payload, timestamp_micros, challenge.challenge_token, challenge.salt)

    tampered_payload = {"action": "TRANSFER", "amount": 9999.00, "recipient": "acc_101"}
    raw_tampered_body = canonicalize_json(tampered_payload)

    headers = {
        "Content-Type": "application/json",
        "X-Frugal-Mac": mac,
        "X-Frugal-Timestamp": str(timestamp_micros),
        "X-Frugal-Challenge": challenge.challenge_token
    }

    resp = requests.put(f"{GATEWAY_URL}/v1/transactions/{challenge.tx_id}", data=raw_tampered_body, headers=headers)
    assert resp.status_code == 401
    assert resp.json().get("error") == "INVALID_HMAC_SIGNATURE"

@pytest.mark.secure
def test_stale_timestamp_rejected_422():
    """Verifies timestamp skew > 5 seconds is rejected with HTTP 422."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {"action": "TRANSFER", "amount": 50.00}
    stale_timestamp_micros = int((time.time() - 10) * 1e6)
    mac = compute_hmac_signature(payload, stale_timestamp_micros, challenge.challenge_token, challenge.salt)

    headers = {
        "Content-Type": "application/json",
        "X-Frugal-Mac": mac,
        "X-Frugal-Timestamp": str(stale_timestamp_micros),
        "X-Frugal-Challenge": challenge.challenge_token
    }

    resp = requests.put(f"{GATEWAY_URL}/v1/transactions/{challenge.tx_id}", data=canonicalize_json(payload), headers=headers)
    assert resp.status_code == 422
    assert resp.json().get("error") == "STALE_TIMESTAMP_SKEW_EXCEEDED"

@pytest.mark.vulnerable
def test_vulnerable_mode_emits_high_risk_alert(vulnerable_gateway):
    """P0-6: Runs real POST -> signed PUT -> replay chain against VULNERABLE gateway, observing duplicate 2xx and emitting alert."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {
        "action": "TRANSFER",
        "amount": 500.00,
        "currency": "USD",
        "recipient": "acc_884920"
    }

    # Execute transaction replay against gateway in VULNERABLE mode
    result = client.execute_signed_put_and_replay(challenge, payload)

    # Assert gateway returned duplicated 2xx success (vulnerability observed!)
    assert result.initial_status == 200, f"Expected initial status 200, got {result.initial_status}"
    assert result.replay_status == 200, f"Expected replay status 200 in VULNERABLE mode, got {result.replay_status}"

    # Emit security alert artifact BY observing this real duplicated 2xx success
    reporter = VulnerabilityReporter(ARTIFACTS_DIR)
    alert = reporter.emit_high_risk_alert(
        endpoint="/v1/transactions/:id",
        tx_id=challenge.tx_id,
        initial_status=result.initial_status,
        replay_status=result.replay_status,
        gap_micros=result.replay_gap_micros
    )

    alert_file = ARTIFACTS_DIR / "VULNERABILITY_ALERT.json"
    assert alert_file.exists()
    with open(alert_file, "r") as f:
        data = json.load(f)

    assert data["severity"] == "CRITICAL"
    assert "CWE-294" in data["cwe_reference"]
    assert data["initial_status_code"] == 200
    assert data["replay_status_code"] == 200
