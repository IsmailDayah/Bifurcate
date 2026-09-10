"""Modes of operation and padding.

CBC is the default. ECB exists ONLY as a labelled counter-example: encrypting
a simple logo in ECB leaves the outline visible, which is the
famous "ECB penguin" argument for why mode matters. It is never the default and
the UI marks it INSECURE.
"""

from __future__ import annotations

from .cipher import BLOCK_BYTES, decrypt_block, encrypt_block
from .keyschedule import RoundKeys

MODE_CBC = 0
MODE_ECB = 1


# -- PKCS#7 -----------------------------------------------------------------
def pad(data: bytes, block_size: int = BLOCK_BYTES) -> bytes:
    """PKCS#7. ALWAYS pads — an exact multiple gains a whole extra block, so
    unpadding is never ambiguous."""
    n = block_size - (len(data) % block_size)
    return data + bytes([n]) * n


def unpad(data: bytes, block_size: int = BLOCK_BYTES) -> bytes:
    if not data or len(data) % block_size:
        raise ValueError("invalid padded length")
    n = data[-1]
    if n < 1 or n > block_size or data[-n:] != bytes([n]) * n:
        raise ValueError("invalid PKCS#7 padding")
    return data[:-n]


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def _blocks(data: bytes):
    for i in range(0, len(data), BLOCK_BYTES):
        yield data[i : i + BLOCK_BYTES]


# -- CBC --------------------------------------------------------------------
def cbc_encrypt(plaintext: bytes, rk: RoundKeys, iv: bytes) -> bytes:
    """C_i = E(P_i XOR C_{i-1}), with C_0 = IV."""
    if len(iv) != BLOCK_BYTES:
        raise ValueError("IV must be 16 bytes")
    prev = iv
    out = bytearray()
    for block in _blocks(pad(plaintext)):
        prev = encrypt_block(_xor(block, prev), rk)
        out += prev
    return bytes(out)


def cbc_decrypt(ciphertext: bytes, rk: RoundKeys, iv: bytes) -> bytes:
    if len(iv) != BLOCK_BYTES:
        raise ValueError("IV must be 16 bytes")
    if not ciphertext or len(ciphertext) % BLOCK_BYTES:
        raise ValueError("ciphertext length must be a multiple of the block size")
    prev = iv
    out = bytearray()
    for block in _blocks(ciphertext):
        out += _xor(decrypt_block(block, rk), prev)
        prev = block
    return unpad(bytes(out))


# -- ECB (demo counter-example only) ----------------------------------------
def ecb_encrypt(plaintext: bytes, rk: RoundKeys, iv: bytes | None = None) -> bytes:
    """INSECURE — identical plaintext blocks produce identical ciphertext."""
    return b"".join(encrypt_block(b, rk) for b in _blocks(pad(plaintext)))


def ecb_decrypt(ciphertext: bytes, rk: RoundKeys, iv: bytes | None = None) -> bytes:
    if not ciphertext or len(ciphertext) % BLOCK_BYTES:
        raise ValueError("ciphertext length must be a multiple of the block size")
    return unpad(b"".join(decrypt_block(b, rk) for b in _blocks(ciphertext)))


ENCRYPTORS = {MODE_CBC: cbc_encrypt, MODE_ECB: ecb_encrypt}
DECRYPTORS = {MODE_CBC: cbc_decrypt, MODE_ECB: ecb_decrypt}
MODE_NAMES = {MODE_CBC: "CBC", MODE_ECB: "ECB"}
