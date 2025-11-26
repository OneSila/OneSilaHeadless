import hmac
import hashlib
from typing import Dict


def make_signature(secret: str, timestamp: int, raw_body: bytes) -> str:
    payload = str(timestamp).encode() + b"." + raw_body
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def check_signature(secret: str, timestamp: int, raw_body: bytes, signature: str) -> bool:
    expected = make_signature(secret, timestamp, raw_body)
    return hmac.compare_digest(expected, signature)


def build_headers(
    user_agent: str,
    event: str,
    action: str,
    version: str,
    delivery_id: str,
    secret: str,
    timestamp: int,
    raw_body: bytes,
) -> Dict[str, str]:
    signature = make_signature(secret, timestamp, raw_body)
    return {
        "User-Agent": user_agent,
        "X-OneSila-Event": event,
        "X-OneSila-Action": action,
        "X-OneSila-Version": version,
        "X-OneSila-Delivery": delivery_id,
        "X-OneSila-Signature": f"t={timestamp},v1={signature}",
    }
