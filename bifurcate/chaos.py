"""The chaotic engine — deterministic integer logistic map.

WHY INTEGER ARITHMETIC (the single most important implementation decision):
    x_{n+1} = r*x_n*(1 - x_n) in floating point is NOT guaranteed bit-identical
    across platforms, Python builds, or FPU modes. One differing bit in the
    keystream means decryption fails on another machine and cannot be
    debugged under pressure. Python integers are arbitrary-precision, so the
    fixed-point formulation below is exactly reproducible everywhere.

WHY THE SHA-256 SPONGE:
    Raw states are never emitted. Chaos supplies key-dependent *structure*;
    SHA-256 supplies *statistical quality*. The literature (Alvarez & Li, 2006)
    shows naive chaos ciphers are frequently broken precisely because they rely
    on the map's statistics. This split is a deliberate defence, not a hedge.
"""

from __future__ import annotations

import hashlib

SCALE = 1 << 32          # fixed-point scale S; state X represents x = X / S
R_SHIFT = 20             # r is stored as a 2^20 fixed-point integer
R_FIXED = round(3.99 * (1 << R_SHIFT))   # r = 3.99, deep in the chaotic regime
ITERS_PER_SQUEEZE = 8    # map iterations between successive sponge squeezes


def step(x: int) -> int:
    """One iteration of the fixed-point logistic map.

    x_next = (R * X * (S - X)) // (S * 2^R_SHIFT)
    Stays within [0, S) for all X in [0, S).
    """
    return (R_FIXED * x * (SCALE - x)) // (SCALE << R_SHIFT)


class ChaosEngine:
    """Key-seeded chaotic byte source.

    Parameters
    ----------
    enc_seed:
        32-byte subkey from :func:`bifurcate.kdf.derive_subkeys`. Never a raw
        passphrase — the key hierarchy stretches passphrases through PBKDF2 first.
    """

    def __init__(self, enc_seed: bytes) -> None:
        if len(enc_seed) != 32:
            raise ValueError("enc_seed must be exactly 32 bytes")
        self._seed = enc_seed
        # Seed the state from the subkey, forced into the valid open interval.
        self._x = int.from_bytes(enc_seed[:4], "big") % (SCALE - 2) + 1
        self._ctr = 0
        self._buf = bytearray()
        self._reinject = 0

    # -- degeneracy guard -------------------------------------------------
    def _guard(self, prev: int) -> None:
        """Escape fixed points and detected 1-cycles.

        X = 0 is an absorbing state of the logistic map, and a discretised map
        can also land on X_next == X. Either would collapse the keystream, so
        we re-inject key material instead of stalling.
        """
        if self._x == 0 or self._x == prev:
            self._reinject += 1
            digest = hashlib.sha256(
                b"BIFURCATE-REINJECT" + self._reinject.to_bytes(8, "big") + self._seed
            ).digest()
            self._x = (self._x ^ int.from_bytes(digest[:4], "big")) % (SCALE - 2) + 1

    def _iterate(self, n: int) -> None:
        for _ in range(n):
            prev = self._x
            self._x = step(self._x)
            self._guard(prev)

    # -- public API -------------------------------------------------------
    def _squeeze(self) -> bytes:
        """Advance the map, then whiten the state into 32 output bytes."""
        self._iterate(ITERS_PER_SQUEEZE)
        block = hashlib.sha256(
            self._x.to_bytes(4, "big") + self._ctr.to_bytes(8, "big") + self._seed
        ).digest()
        self._ctr += 1
        return block

    def stream(self, n_bytes: int) -> bytes:
        """Return the next `n_bytes` of keystream."""
        if n_bytes < 0:
            raise ValueError("n_bytes must be non-negative")
        while len(self._buf) < n_bytes:
            self._buf.extend(self._squeeze())
        out = bytes(self._buf[:n_bytes])
        del self._buf[:n_bytes]
        return out

    def byte(self) -> int:
        """Return a single keystream byte (used by the Fisher-Yates shuffle)."""
        return self.stream(1)[0]


def orbit(x0: float, r: float, n: int, skip: int = 0) -> list[float]:
    """Float logistic orbit — VISUALISATION ONLY (bifurcation diagram).

    Deliberately separate from the cipher path: floats are fine for drawing a
    picture, and must never touch key material.
    """
    x = x0
    out = []
    for i in range(n + skip):
        x = r * x * (1.0 - x)
        if i >= skip:
            out.append(x)
    return out
