"""RSA-OAEP hybrid envelope.

We do NOT reimplement RSA. The goal is to *evaluate* asymmetric
cryptography, so we use a correct, standard implementation (RFC 8017 OAEP via
`cryptography`) and measure it honestly against the symmetric core.

The session key IS the `root_key`: the recipient unwraps it with their
private key, then derives `enc_seed` and `mac_key` exactly as in passphrase
mode. Both modes are therefore symmetric by construction.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

RSA_BITS = 2048
WRAPPED_LEN = RSA_BITS // 8  # 256 bytes for RSA-2048
ROOT_KEY_BYTES = 32

_OAEP = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)


def generate_keypair(bits: int = RSA_BITS):
    """Generate an RSA keypair (public exponent 65537 — the standard choice)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return private_key, private_key.public_key()


def serialize_private(private_key, password: bytes | None = None) -> bytes:
    enc = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc,
    )


def serialize_public(public_key) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_private(pem: bytes, password: bytes | None = None):
    return serialization.load_pem_private_key(pem, password=password)


def load_public(pem: bytes):
    return serialization.load_pem_public_key(pem)


def new_root_key() -> bytes:
    """A fresh 32-byte session key — random per message."""
    return os.urandom(ROOT_KEY_BYTES)


def wrap_key(public_key, root_key: bytes) -> bytes:
    """RSA-OAEP-SHA256 encrypt the session key."""
    if len(root_key) != ROOT_KEY_BYTES:
        raise ValueError("root_key must be 32 bytes")
    return public_key.encrypt(root_key, _OAEP)


def unwrap_key(private_key, wrapped: bytes) -> bytes:
    """RSA-OAEP-SHA256 decrypt the session key. Wrong key raises."""
    return private_key.decrypt(wrapped, _OAEP)


def max_plaintext_bytes(bits: int = RSA_BITS) -> int:
    """RSA-OAEP capacity: k - 2*hLen - 2 (RFC 8017).

    2048-bit RSA carries only 190 bytes — which is precisely why hybrid
    encryption exists.
    """
    return bits // 8 - 2 * 32 - 2


def fingerprint(public_key) -> str:
    """Short SHA-256 fingerprint of a public key, for the Keys page."""
    import hashlib

    digest = hashlib.sha256(serialize_public(public_key)).hexdigest()
    return ":".join(digest[i : i + 4] for i in range(0, 16, 4)).upper()
