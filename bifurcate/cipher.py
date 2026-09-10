"""The Feistel network — block-level encrypt/decrypt.

    Encrypt:  for i = 0..11:   L, R = R, L XOR F(R, K_i)   ; output R || L
    Decrypt:  identical, with the round keys consumed in reverse order.

Encryption and decryption are THE SAME FUNCTION. Only the key order flips.
That is the elegance of Feistel:
whatever F does — however non-invertible, however chaotic — the structure
still inverts.
"""

from __future__ import annotations

from .keyschedule import HALF_BYTES, ROUNDS, RoundKeys, expand
from .round import F

BLOCK_BYTES = 16  # 128-bit block


def _feistel(block: bytes, rk: RoundKeys, *, reverse: bool) -> bytes:
    if len(block) != BLOCK_BYTES:
        raise ValueError(f"block must be exactly {BLOCK_BYTES} bytes")
    left, right = block[:HALF_BYTES], block[HALF_BYTES:]
    order = range(ROUNDS - 1, -1, -1) if reverse else range(ROUNDS)
    for i in order:
        f = F(right, rk.keys[i], rk.rots[i], rk.sbox)
        left, right = right, bytes(a ^ b for a, b in zip(left, f))
    return right + left  # final swap omitted -> concatenate reversed


def encrypt_block(block: bytes, rk: RoundKeys) -> bytes:
    """Encrypt one 128-bit block."""
    return _feistel(block, rk, reverse=False)


def decrypt_block(block: bytes, rk: RoundKeys) -> bytes:
    """Decrypt one 128-bit block."""
    return _feistel(block, rk, reverse=True)


class Bifurcate:
    """Convenience wrapper binding a key schedule to the block operations."""

    def __init__(self, enc_seed: bytes) -> None:
        self.rk = expand(enc_seed)

    def encrypt_block(self, block: bytes) -> bytes:
        return encrypt_block(block, self.rk)

    def decrypt_block(self, block: bytes) -> bytes:
        return decrypt_block(block, self.rk)
