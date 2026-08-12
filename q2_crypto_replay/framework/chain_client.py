"""
HMAC Transaction Chain & Replay Client (Q2 Framework)

What it does:
    Executes the multi-step transaction authorization workflow (POST challenge -> PUT signed payload)
    using the server-provided timestamp for HMAC-SHA512 generation, and dispatches a duplicate
    replay request within a target <150ms window.
"""

import time
import json
import logging
import requests
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

from q2_crypto_replay.framework.hmac_signer import compute_hmac_signature, canonicalize_json

logger = logging.getLogger("chain_client")

@dataclass
class TransactionChallenge:
    tx_id: str
    challenge_token: str
    server_timestamp_micros: int
    salt: str

@dataclass
class ReplayExecutionResult:
    tx_id: str
    initial_status: int
    replay_status: int
    replay_gap_micros: float
    initial_response: Dict[str, Any]
    replay_response: Dict[str, Any]

class CryptoChainClient:
    """Client driving gateway transaction initialization and replay verification."""

    def __init__(self, gateway_url: str = "http://localhost:8082") -> None:
        self.gateway_url = gateway_url

    def initiate_transaction(self) -> TransactionChallenge:
        """Step 1: POST /v1/transactions, extract ID from response header."""
        resp = requests.post(f"{self.gateway_url}/v1/transactions")
        resp.raise_for_status()

        tx_id = resp.headers.get("X-Transaction-Id")
        if not tx_id:
            raise ValueError("Gateway response missing required 'X-Transaction-Id' header.")

        body = resp.json()
        challenge = TransactionChallenge(
            tx_id=tx_id,
            challenge_token=body["challengeToken"],
            server_timestamp_micros=body["serverTimestampMicros"],
            salt=body["salt"]
        )

        print(f"[Q2] transaction_id={challenge.tx_id}")
        print(f"[Q2] challenge_received={challenge.challenge_token[:16]}...")
        print(f"[Q2] server_timestamp_micros={challenge.server_timestamp_micros}")

        return challenge

    def execute_signed_put_and_replay(
        self,
        challenge: TransactionChallenge,
        payload_dict: Dict[str, Any]
    ) -> ReplayExecutionResult:
        """
        Step 2 & 3: Sign payload using server_timestamp_micros, send PUT, then resend identical request within 150ms.
        """
        # Q2-A: Explicitly use the server-provided timestamp in cryptographic signing flow
        timestamp_micros = challenge.server_timestamp_micros

        print(f"[Q2] signing_timestamp_source=SERVER")
        print(f"[Q2] hmac_algorithm=HMAC-SHA512")

        mac = compute_hmac_signature(payload_dict, timestamp_micros, challenge.challenge_token, challenge.salt)
        raw_body = canonicalize_json(payload_dict)

        headers = {
            "Content-Type": "application/json",
            "X-Frugal-Mac": mac,
            "X-Frugal-Timestamp": str(timestamp_micros),
            "X-Frugal-Challenge": challenge.challenge_token
        }

        url = f"{self.gateway_url}/v1/transactions/{challenge.tx_id}"

        # Dispatch Step 2: Initial PUT
        start_ns = time.perf_counter_ns()
        resp1 = requests.put(url, data=raw_body, headers=headers)
        put1_completion_ns = time.perf_counter_ns()

        # Dispatch Step 3: Replay PUT (byte-identical)
        resp2 = requests.put(url, data=raw_body, headers=headers)
        put2_completion_ns = time.perf_counter_ns()

        replay_gap_micros = (put2_completion_ns - put1_completion_ns) / 1000.0

        logger.info(json.dumps({
            "event": "REPLAY_DISPATCHED",
            "tx_id": challenge.tx_id,
            "initial_status": resp1.status_code,
            "replay_status": resp2.status_code,
            "gap_micros": replay_gap_micros
        }))

        return ReplayExecutionResult(
            tx_id=challenge.tx_id,
            initial_status=resp1.status_code,
            replay_status=resp2.status_code,
            replay_gap_micros=replay_gap_micros,
            initial_response=resp1.json() if resp1.content else {},
            replay_response=resp2.json() if resp2.content else {}
        )
