"""The round function F.

F maps 8 bytes -> 8 bytes and is applied to the right half each round:

    1. XOR round key      -> key mixing
    2. S-box substitution -> CONFUSION   (Shannon, 1949)
    3. bit rotation       -> DIFFUSION   (crosses byte boundaries)
    4. byte permutation   -> DIFFUSION   (moves bytes between lanes)

F IS NEVER INVERTED. The Feistel structure guarantees decryption
regardless of what F does, which is why an un-invertible chaotic S-box is safe
to use here.
"""

from __future__ import annotations

HALF_BITS = 64
HALF_BYTES = 8
MASK64 = (1 << HALF_BITS) - 1

# v1.1 fix — a single 8-cycle derangement: 0->5->3->7->4->1->2->6->0.
# No byte stays in place (derangement) AND one cycle links all eight lanes,
# so repeated rounds propagate every byte to every position. Asserted in tests.
PERM: tuple[int, ...] = (5, 2, 6, 7, 1, 3, 0, 4)


def rotate_left_bits(block: bytes, n: int) -> bytes:
    """Rotate an 8-byte block left by n bits (treated as one 64-bit word)."""
    n %= HALF_BITS
    if n == 0:
        return block
    v = int.from_bytes(block, "big")
    v = ((v << n) | (v >> (HALF_BITS - n))) & MASK64
    return v.to_bytes(HALF_BYTES, "big")


def byte_permute(block: bytes, perm: tuple[int, ...] = PERM) -> bytes:
    """Move the byte at position i to position perm[i]."""
    out = bytearray(HALF_BYTES)
    for i, dest in enumerate(perm):
        out[dest] = block[i]
    return bytes(out)


def is_derangement(perm: tuple[int, ...]) -> bool:
    """True iff no element maps to its own index."""
    return all(i != dest for i, dest in enumerate(perm))


def cycle_lengths(perm: tuple[int, ...]) -> list[int]:
    """Cycle decomposition lengths — used to assert PERM is a single 8-cycle."""
    seen = [False] * len(perm)
    lengths = []
    for start in range(len(perm)):
        if seen[start]:
            continue
        length = 0
        node = start
        while not seen[node]:
            seen[node] = True
            node = perm[node]
            length += 1
        lengths.append(length)
    return lengths


def F(half: bytes, round_key: bytes, rot: int, sbox: bytes) -> bytes:
    """The round function."""
    t = bytes(a ^ b for a, b in zip(half, round_key))   # 1. key mixing
    t = bytes(sbox[b] for b in t)                        # 2. confusion
    t = rotate_left_bits(t, rot)                         # 3. diffusion
    return byte_permute(t)                               # 4. diffusion
