"""Round-key schedule.

Draws 12 x (8-byte round key + 1 rotation byte) = 108 bytes from the sponge.

THE ROTATION FLOOR (v1.1 fix): rot is 1..7, never 0. A zero rotation would
leave that round's diffusion resting on the fixed byte permutation alone, so
every round is guaranteed to mix across byte boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

from .chaos import ChaosEngine
from .sbox import generate_sbox

ROUNDS = 12
HALF_BYTES = 8  # 64-bit half-block


@dataclass(frozen=True)
class RoundKeys:
    """Everything the Feistel network needs, derived from one enc_seed."""

    sbox: bytes
    keys: tuple[bytes, ...]
    rots: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.keys) != ROUNDS or len(self.rots) != ROUNDS:
            raise ValueError(f"expected {ROUNDS} round keys and rotations")


def expand(enc_seed: bytes) -> RoundKeys:
    """enc_seed -> (S-box, 12 round keys, 12 rotation amounts).

    Order matters and is part of the wire format: the S-box is drawn first,
    then each round's key and rotation in sequence.
    """
    engine = ChaosEngine(enc_seed)
    sbox = generate_sbox(engine)
    keys: list[bytes] = []
    rots: list[int] = []
    for _ in range(ROUNDS):
        keys.append(engine.stream(HALF_BYTES))
        rots.append(1 + engine.byte() % 7)  # 1..7 — never zero
    return RoundKeys(sbox=sbox, keys=tuple(keys), rots=tuple(rots))
