"""The .bfc container format and the end-to-end API.

Layout (every field authenticated by the trailing tag):

    offset  field
    0       magic        "BFC1"          4
    4       version      0x01            1
    5       flags        mode | hybrid   1
    6       salt                        16
    22      iv                          16
    38      wrapped_len  uint16 BE       2
    40      wrapped_key  (0 or 256)     var
    ..      ciphertext                  var
    end-32  hmac_tag                    32

Self-describing files are the determinism proof: you can encrypt on one
machine and decrypt on another with no out-of-band parameters.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from .kdf import derive_subkeys
from .keyschedule import expand
from .mac import TAG_BYTES, IntegrityError, compute_tag, verify_tag
from .modes import DECRYPTORS, ENCRYPTORS, MODE_CBC, MODE_ECB, MODE_NAMES

MAGIC = b"BFC1"
VERSION = 1
SALT_BYTES = 16
IV_BYTES = 16
HEADER_LEN = 40  # magic..wrapped_len inclusive

FLAG_ECB = 0b0000_0001
FLAG_HYBRID = 0b0000_0010

PBKDF2_ITERATIONS = 200_000


class FormatError(Exception):
    """Raised when a file is not a valid .bfc container."""


# -- key material -----------------------------------------------------------
def root_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256, 200k iterations.

    Stretches a low-entropy human passphrase to a full 256-bit key and makes
    dictionary attacks expensive. The chaos engine is NEVER seeded from a raw
    passphrase.
    """
    return hashlib.pbkdf2_hmac(
        "sha256", passphrase.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32
    )


@dataclass(frozen=True)
class Container:
    """A parsed .bfc file."""

    version: int
    flags: int
    salt: bytes
    iv: bytes
    wrapped_key: bytes
    ciphertext: bytes
    tag: bytes

    @property
    def mode(self) -> int:
        return MODE_ECB if self.flags & FLAG_ECB else MODE_CBC

    @property
    def mode_name(self) -> str:
        return MODE_NAMES[self.mode]

    @property
    def is_hybrid(self) -> bool:
        return bool(self.flags & FLAG_HYBRID)


def _pack(flags, salt, iv, wrapped_key, ciphertext) -> bytes:
    """Serialise everything except the tag (this is exactly the MAC input)."""
    return (
        MAGIC
        + bytes([VERSION, flags])
        + salt
        + iv
        + len(wrapped_key).to_bytes(2, "big")
        + wrapped_key
        + ciphertext
    )


# -- encrypt ----------------------------------------------------------------
def encrypt(
    plaintext: bytes,
    *,
    passphrase: str | None = None,
    public_key=None,
    mode: int = MODE_CBC,
) -> bytes:
    """Encrypt `plaintext` into a complete .bfc container.

    Exactly one of `passphrase` or `public_key` must be given.
    """
    if (passphrase is None) == (public_key is None):
        raise ValueError("provide exactly one of passphrase or public_key")

    salt = os.urandom(SALT_BYTES)
    iv = os.urandom(IV_BYTES)
    flags = 0
    if mode == MODE_ECB:
        flags |= FLAG_ECB

    if public_key is not None:
        from .hybrid import new_root_key, wrap_key

        root_key = new_root_key()
        wrapped = wrap_key(public_key, root_key)
        flags |= FLAG_HYBRID
    else:
        root_key = root_key_from_passphrase(passphrase, salt)
        wrapped = b""

    enc_seed, mac_key = derive_subkeys(root_key)
    rk = expand(enc_seed)
    ciphertext = ENCRYPTORS[mode](plaintext, rk, iv)

    body = _pack(flags, salt, iv, wrapped, ciphertext)
    return body + compute_tag(mac_key, body)


# -- parse / decrypt --------------------------------------------------------
def parse(blob: bytes) -> Container:
    """Parse a .bfc file without verifying or decrypting it."""
    if len(blob) < HEADER_LEN + TAG_BYTES:
        raise FormatError("file too short to be a .bfc container")
    if blob[:4] != MAGIC:
        raise FormatError("bad magic — not a .bfc container")
    version = blob[4]
    if version != VERSION:
        raise FormatError(f"unsupported container version {version}")
    flags = blob[5]
    salt = blob[6:22]
    iv = blob[22:38]
    wrapped_len = int.from_bytes(blob[38:40], "big")
    start = HEADER_LEN
    wrapped_key = blob[start : start + wrapped_len]
    if len(wrapped_key) != wrapped_len:
        raise FormatError("truncated wrapped key")
    ciphertext = blob[start + wrapped_len : -TAG_BYTES]
    tag = blob[-TAG_BYTES:]
    return Container(version, flags, salt, iv, wrapped_key, ciphertext, tag)


def decrypt(
    blob: bytes,
    *,
    passphrase: str | None = None,
    private_key=None,
) -> bytes:
    """Verify then decrypt a .bfc container.

    The tag is checked BEFORE decryption. On failure this raises
    :class:`IntegrityError` — it never returns garbage.
    """
    c = parse(blob)

    if c.is_hybrid:
        if private_key is None:
            raise ValueError("this container is hybrid — an RSA private key is required")
        from .hybrid import unwrap_key

        try:
            root_key = unwrap_key(private_key, c.wrapped_key)
        except Exception as exc:  # wrong private key
            raise IntegrityError("RSA unwrap failed — wrong private key") from exc
    else:
        if passphrase is None:
            raise ValueError("this container needs a passphrase")
        root_key = root_key_from_passphrase(passphrase, c.salt)

    enc_seed, mac_key = derive_subkeys(root_key)

    # Authenticate the entire prefix before touching the ciphertext.
    verify_tag(mac_key, blob[:-TAG_BYTES], c.tag)

    rk = expand(enc_seed)
    return DECRYPTORS[c.mode](c.ciphertext, rk, c.iv)
