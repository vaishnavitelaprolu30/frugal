"""
Security Vulnerability Alert Generator (Q2 Framework)

What it does:
    Analyzes API transaction replay test execution results and emits structured security alerts
    (JSON lines + artifact file) when replay bypasses authentication/nonce checks.

Failure mode defended against:
    Prevents high-risk security flaws (CWE-294 Replay Attacks) from passing unnoticed in CI/CD pipeline runs.

Design trade-off:
    Emits structured security alert artifacts to filesystem in addition to log output, ensuring static artifact
    scanners can ingest vulnerabilities without parsing stdout stream logs.
"""

import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any

logger = logging.getLogger("vuln_reporter")

@dataclass
class VulnerabilityAlert:
    severity: str
    cwe_reference: str
    vulnerability_type: str
    endpoint: str
    transaction_id: str
    initial_status_code: int
    replay_status_code: int
    replay_gap_micros: float
    remediation_guidance: str
    timestamp_iso: str

class VulnerabilityReporter:
    """Security alert generator for CWE-294 Replay vulnerability detection."""

    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.alert_file = self.artifacts_dir / "VULNERABILITY_ALERT.json"

    def emit_high_risk_alert(
        self,
        endpoint: str,
        tx_id: str,
        initial_status: int,
        replay_status: int,
        gap_micros: float
    ) -> VulnerabilityAlert:
        alert = VulnerabilityAlert(
            severity="CRITICAL",
            cwe_reference="CWE-294: Authentication Bypass by Capture-replay",
            vulnerability_type="UNGUARDED_TRANSACTION_REPLAY",
            endpoint=endpoint,
            transaction_id=tx_id,
            initial_status_code=initial_status,
            replay_status_code=replay_status,
            replay_gap_micros=gap_micros,
            remediation_guidance=(
                "Enforce atomic nonce tracking (in Redis/In-Memory Map) per (MAC + Timestamp) tuple "
                "and reject duplicate submissions within clock skew window with HTTP 409 Conflict."
            ),
            timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

        alert_data = asdict(alert)

        # Write to structured JSON log
        logger.critical(json.dumps({
            "event": "HIGH_RISK_VULNERABILITY_DETECTED",
            "alert": alert_data
        }))

        # Write alert artifact file
        with open(self.alert_file, "w") as f:
            json.dump(alert_data, f, indent=2)

        return alert
