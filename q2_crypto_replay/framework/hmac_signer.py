"""
Canonical HMAC Signer (Q2 Framework)

What it does:
    Serializes JSON request payloads into a canonical, sorted key representation with zero
    whitespace, and generates HMAC-SHA512 signatures using a challenge-derived key.

Failure mode defended against:
    Defends against signature mismatch failures caused by field ordering variations or string
    formatting drift between client and gateway.

Design trade-off:
    Enforces strict key sorting and explicit microsecond string formatting, sacrificing JSON
    serialization flexibility for bit-for-bit cryptographic reproducibility across platforms.
"""

import hmac
import hashlib
import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple

logger = logging.getLogger("hmac_signer")

SHARED_SECRET = "super_secret_hmac_key_frugal_9921"

def canonicalize_json(body: Dict[str, Any]) -> str:
    """Serializes body dictionary with sorted keys and no whitespace."""
    return json.dumps(body, sort_keys=True, separators=(',', ':'))

def compute_hmac_signature(
    body_dict: Dict[str, Any],
    timestamp_micros: int,
    challenge_token: str,
    salt: str
) -> str:
    """Computes HMAC-SHA512 signature matching gateway verification logic."""
    canonical_body = canonicalize_json(body_dict)
    
    # Derive key via SHA256(SHARED_SECRET, challenge)
    derived_key = hmac.new(
        SHARED_SECRET.encode('utf-8'),
        challenge_token.encode('utf-8'),
        hashlib.sha256
    ).digest()

    # Construct payload to sign: canonical_body:timestamp_micros:salt
    payload = f"{canonical_body}:{timestamp_micros}:{salt}".encode('utf-8')

    mac = hmac.new(derived_key, payload, hashlib.sha512).hexdigest()
    
    logger.info(json.dumps({
        "event": "HMAC_COMPUTED",
        "mac_snippet": mac[:16] + "...",
        "timestamp_micros": timestamp_micros
    }))
    return mac
