"""Authentication — encrypt-then-MAC over the WHOLE container.

v1.1 FIX: the tag covers every byte of the container that precedes it —
magic ‖ version ‖ flags ‖ salt ‖ IV ‖ wrapped_len ‖ wrapped_key ‖ ciphertext.

Why it matters: an earlier draft MAC'd only (version ‖ salt ‖ IV ‖ wrapped ‖ ct),
leaving `flags` unauthenticated. An attacker could then flip the mode bit
(CBC→ECB) or the hybrid bit without detection — a downgrade attack. Covering
the full prefix means there is exactly one source of truth and nothing can be
tampered with silently.

The tag is verified BEFORE any decryption is attempted, which also rules out
padding-oracle style attacks.
"""

from __future__ import annotations

import hashlib
import hmac

TAG_BYTES = 32


class IntegrityError(Exception):
    """Raised when authentication fails: wrong key, or the data was altered.

    Bifurcate never returns garbage plaintext — a failure is always explicit.
    This is what makes the red INTEGRITY FAIL moment in the demo honest.
    """


def compute_tag(mac_key: bytes, authenticated_bytes: bytes) -> bytes:
    """HMAC-SHA256 over the container prefix."""
    return hmac.new(mac_key, authenticated_bytes, hashlib.sha256).digest()


def verify_tag(mac_key: bytes, authenticated_bytes: bytes, tag: bytes) -> None:
    """Constant-time verification. Raises :class:`IntegrityError` on mismatch."""
    expected = compute_tag(mac_key, authenticated_bytes)
    if not hmac.compare_digest(expected, tag):
        raise IntegrityError("INTEGRITY FAIL — HMAC mismatch (wrong key or tampered data)")
