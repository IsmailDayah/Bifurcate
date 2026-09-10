"""HKDF-SHA256 (RFC 5869) over stdlib only.

The cipher core must not depend on third-party crypto, so the key
hierarchy is built from `hmac` + `hashlib`. RSA is the only place
we reach for the `cryptography` package.
"""

from __future__ import annotations

import hashlib
import hmac

HASH_LEN = 32  # SHA-256 output size


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """RFC 5869 §2.2 — extract a uniform pseudorandom key from input keying material."""
    if not salt:
        salt = b"\x00" * HASH_LEN
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int = HASH_LEN) -> bytes:
    """RFC 5869 §2.3 — expand a pseudorandom key to `length` bytes."""
    if length > 255 * HASH_LEN:
        raise ValueError("HKDF: requested length too large")
    out = b""
    block = b""
    counter = 1
    while len(out) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:length]


def hkdf(ikm: bytes, info: bytes, length: int = HASH_LEN, salt: bytes = b"") -> bytes:
    """Full HKDF: extract-then-expand.

    Splits one 32-byte ``root_key`` into two independent
    subkeys, so encryption and authentication never share key material
    (*key separation*).
    """
    return hkdf_expand(hkdf_extract(salt, ikm), info, length)


# Domain-separation labels — these strings are part of the wire format.
INFO_CHAOS = b"BIFURCATE-CHAOS-v1"
INFO_MAC = b"BIFURCATE-MAC-v1"


def derive_subkeys(root_key: bytes) -> tuple[bytes, bytes]:
    """root_key -> (enc_seed, mac_key).

    Both passphrase mode and hybrid mode funnel into this function, which is
    what makes the two modes symmetric by construction: a hybrid recipient
    unwraps ``root_key`` with their RSA private key and derives the S-box and
    the MAC key with no passphrase at all.
    """
    if len(root_key) != 32:
        raise ValueError("root_key must be exactly 32 bytes")
    return hkdf(root_key, INFO_CHAOS), hkdf(root_key, INFO_MAC)
