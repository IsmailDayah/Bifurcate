"""Key-derived S-box via Fisher-Yates.

THE NOVELTY OF BIFURCATE lives here. Classical ciphers ship one fixed,
publicly known substitution table for every user on earth. Bifurcate grows the
table from the key, so two passphrases are effectively running two different
ciphers.

NO INVERSE TABLE IS NEEDED. In a Feistel network the round function F is never
inverted — the structure guarantees decryption regardless. That removes
an entire class of bug.
"""

from __future__ import annotations

from .chaos import ChaosEngine


def generate_sbox(engine: ChaosEngine) -> bytes:
    """Fisher-Yates shuffle of [0..255] driven by the chaotic stream.

    The shuffle is a permutation by construction, so the result is always a
    bijection — asserted in tests rather than assumed.
    """
    box = list(range(256))
    for i in range(255, 0, -1):
        j = engine.byte() % (i + 1)
        box[i], box[j] = box[j], box[i]
    return bytes(box)


def is_bijection(sbox: bytes) -> bool:
    """True iff every value 0..255 appears exactly once."""
    return len(sbox) == 256 and len(set(sbox)) == 256


def difference_ratio(a: bytes, b: bytes) -> float:
    """Fraction of positions where two S-boxes differ (key-sensitivity metric)."""
    if len(a) != len(b):
        raise ValueError("S-boxes must be the same length")
    return sum(1 for x, y in zip(a, b) if x != y) / len(a)
