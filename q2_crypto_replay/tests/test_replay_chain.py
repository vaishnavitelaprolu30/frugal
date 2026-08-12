"""
Q2 HMAC Transaction Replay Test Suite

Tests:
1. test_secure_mode_rejects_replay_with_409
2. test_tampered_body_rejects_with_401
3. test_stale_timestamp_rejected_422
4. test_vulnerable_mode_emits_high_risk_alert
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
    assert result.replay_gap_micros < 150000.0  # Under 150ms

def test_tampered_body_rejects_with_401():
    """Verifies single byte mutation in body invalidates HMAC signature."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {"action": "TRANSFER", "amount": 100.00, "recipient": "acc_101"}
    timestamp_micros = int(time.time() * 1e6)
    mac = compute_hmac_signature(payload, timestamp_micros, challenge.challenge_token, challenge.salt)

    # Tamper payload amount from 100.00 -> 9999.00 after signature calculation
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

def test_stale_timestamp_rejected_422():
    """Verifies timestamp skew > 5 seconds is rejected with HTTP 422."""
    client = CryptoChainClient(GATEWAY_URL)
    challenge = client.initiate_transaction()

    payload = {"action": "TRANSFER", "amount": 50.00}
    stale_timestamp_micros = int((time.time() - 10) * 1e6)  # 10s in the past
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

def test_vulnerable_mode_emits_high_risk_alert():
    """Verifies replay attack in VULNERABLE mode triggers security alert artifact."""
    reporter = VulnerabilityReporter(ARTIFACTS_DIR)

    # Simulate detection of replay vulnerability pass
    alert = reporter.emit_high_risk_alert(
        endpoint="/v1/transactions/:id",
        tx_id="tx_test_vuln_883",
        initial_status=200,
        replay_status=200,
        gap_micros=12400.0
    )

    alert_file = ARTIFACTS_DIR / "VULNERABILITY_ALERT.json"
    assert alert_file.exists()
    with open(alert_file, "r") as f:
        data = json.load(f)
    assert data["severity"] == "CRITICAL"
    assert "CWE-294" in data["cwe_reference"]
