"""Security analysis — avalanche, entropy, chi-square and timing.

Every figure quoted in the docs is produced by this module. Nothing is
asserted that was not measured.
"""

from __future__ import annotations

import math
import os
import random
import time
from collections import Counter

from .cipher import BLOCK_BYTES, encrypt_block
from .kdf import derive_subkeys
from .keyschedule import ROUNDS, RoundKeys, expand
from .round import F


# -- bit helpers ------------------------------------------------------------
def bit_diff(a: bytes, b: bytes) -> int:
    """Number of differing bits between two equal-length byte strings."""
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def flip_bit(data: bytes, index: int) -> bytes:
    out = bytearray(data)
    out[index // 8] ^= 1 << (index % 8)
    return bytes(out)


# -- entropy & distribution -------------------------------------------------
def shannon_entropy(data: bytes) -> float:
    """Shannon entropy in bits/byte. Ciphertext should approach 8.0."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def histogram(data: bytes) -> list[int]:
    """Byte-value frequency, length 256 — drives the flattening visual."""
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    return counts


def chi_square_uniform(data: bytes) -> tuple[float, int]:
    """Chi-square statistic against a uniform byte distribution (df = 255).

    A flat histogram gives a statistic near df. Large values indicate structure.
    """
    if not data:
        return 0.0, 255
    expected = len(data) / 256
    counts = histogram(data)
    stat = sum((c - expected) ** 2 / expected for c in counts)
    return stat, 255


def chi_square_p(stat: float, df: int) -> float:
    """Right-tail p-value for a chi-square statistic (Wilson-Hilferty).

    The cube-root transform of chi2/df is close to normal; at df = 255 the
    approximation is accurate to ~1e-3, ample for a uniformity verdict
    (a uniform ciphertext wants p > 0.05). Stdlib only — no scipy dependency.
    """
    if stat <= 0:
        return 1.0
    t = (stat / df) ** (1.0 / 3.0)
    mu = 1.0 - 2.0 / (9.0 * df)
    sigma = math.sqrt(2.0 / (9.0 * df))
    z = (t - mu) / sigma
    return 0.5 * math.erfc(z / math.sqrt(2.0))


# -- avalanche --------------------------------------------------------------
def plaintext_avalanche(rk: RoundKeys, trials: int = 500, seed: int = 0) -> float:
    """Mean % of ciphertext bits that flip when ONE plaintext bit flips."""
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        block = bytes(rng.randrange(256) for _ in range(BLOCK_BYTES))
        idx = rng.randrange(BLOCK_BYTES * 8)
        total += bit_diff(encrypt_block(block, rk), encrypt_block(flip_bit(block, idx), rk))
    return total / (trials * BLOCK_BYTES * 8) * 100


def key_avalanche(rk_a: RoundKeys, rk_b: RoundKeys, trials: int = 500, seed: int = 0) -> float:
    """Mean % of ciphertext bits that differ between two near-identical keys."""
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        block = bytes(rng.randrange(256) for _ in range(BLOCK_BYTES))
        total += bit_diff(encrypt_block(block, rk_a), encrypt_block(block, rk_b))
    return total / (trials * BLOCK_BYTES * 8) * 100


def avalanche_grid(rk: RoundKeys, block: bytes, bit_index: int) -> list[int]:
    """Per-bit diff (0/1) for a single flip — drives the heatmap."""
    a = encrypt_block(block, rk)
    b = encrypt_block(flip_bit(block, bit_index), rk)
    return [
        (a[i // 8] ^ b[i // 8]) >> (i % 8) & 1 for i in range(BLOCK_BYTES * 8)
    ]


def _feistel_n_rounds(block: bytes, rk: RoundKeys, n: int) -> bytes:
    """Encrypt with only the first n rounds — used for the rounds-vs-avalanche curve."""
    left, right = block[:8], block[8:]
    for i in range(n):
        f = F(right, rk.keys[i], rk.rots[i], rk.sbox)
        left, right = right, bytes(x ^ y for x, y in zip(left, f))
    return right + left


def rounds_vs_avalanche(rk: RoundKeys, trials: int = 200, seed: int = 0) -> list[float]:
    """Avalanche % after 1..ROUNDS rounds.

    The headline figure: it turns "we chose 12 rounds" from
    an assertion into evidence.
    """
    rng = random.Random(seed)
    out = []
    for n in range(1, ROUNDS + 1):
        total = 0
        for _ in range(trials):
            block = bytes(rng.randrange(256) for _ in range(BLOCK_BYTES))
            idx = rng.randrange(BLOCK_BYTES * 8)
            total += bit_diff(
                _feistel_n_rounds(block, rk, n),
                _feistel_n_rounds(flip_bit(block, idx), rk, n),
            )
        out.append(total / (trials * BLOCK_BYTES * 8) * 100)
    return out


# -- performance ------------------------------------------------------------
def throughput_mbps(rk: RoundKeys, n_blocks: int = 4000) -> float:
    """Raw block-encryption throughput in MB/s."""
    data = [os.urandom(BLOCK_BYTES) for _ in range(n_blocks)]
    start = time.perf_counter()
    for b in data:
        encrypt_block(b, rk)
    elapsed = time.perf_counter() - start
    return (n_blocks * BLOCK_BYTES) / elapsed / 1_000_000 if elapsed else float("inf")


def rsa_vs_symmetric(trials: int = 20) -> dict:
    """Timing comparison — RSA versus the symmetric core.

    Times the operation each party actually pays for. RSA *encryption* with
    the public key is cheap (small exponent 65537); it is the *private-key
    decryption* that is expensive — so the honest comparison is unwrap vs
    symmetric bulk throughput. RSA is also capped at 190 bytes per operation
    at 2048 bits, so "sending data over RSA" means paying wrap+unwrap for
    every 190-byte chunk. Both facts together are why hybrid encryption
    exists, and both are measured here rather than asserted.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
    from cryptography.hazmat.primitives.ciphers import modes as aes_modes

    from .hybrid import (
        generate_keypair,
        max_plaintext_bytes,
        new_root_key,
        unwrap_key,
        wrap_key,
    )

    priv, pub = generate_keypair()
    key = new_root_key()
    wrapped = wrap_key(pub, key)

    start = time.perf_counter()
    for _ in range(trials):
        wrap_key(pub, key)
    wrap_ms = (time.perf_counter() - start) / trials * 1000

    start = time.perf_counter()
    for _ in range(trials):
        unwrap_key(priv, wrapped)
    unwrap_ms = (time.perf_counter() - start) / trials * 1000

    # Bulk throughput of the two symmetric options.
    bifurcate_mbps = throughput_mbps(expand(derive_subkeys(key)[0]), 2000)

    data = os.urandom(4_000_000)
    enc = Cipher(algorithms.AES(os.urandom(32)), aes_modes.CBC(os.urandom(16))).encryptor()
    start = time.perf_counter()
    enc.update(data)
    enc.finalize()
    aes_mbps = len(data) / (time.perf_counter() - start) / 1_000_000

    # Effective RSA "bulk" rate: every 190-byte chunk costs a wrap + an unwrap.
    chunk = max_plaintext_bytes()
    rsa_mbps = chunk / ((wrap_ms + unwrap_ms) / 1000) / 1_000_000

    return {
        "rsa_wrap_ms": wrap_ms,
        "rsa_unwrap_ms": unwrap_ms,
        "rsa_max_payload_bytes": chunk,
        "rsa_mbps": rsa_mbps,
        "bifurcate_mbps": bifurcate_mbps,
        "aes_mbps": aes_mbps,
        "slowdown_vs_aes": aes_mbps / rsa_mbps if rsa_mbps else float("inf"),
    }


def keyspace_bits() -> int:
    """256-bit key -> 2^256 keyspace."""
    return 256


def summary(passphrase_a: str = "correct horse battery staple",
            passphrase_b: str = "correct horse battery stapla") -> dict:
    """One call that produces every headline number."""
    from .container import root_key_from_passphrase

    salt = b"\x00" * 16
    rk_a = expand(derive_subkeys(root_key_from_passphrase(passphrase_a, salt))[0])
    rk_b = expand(derive_subkeys(root_key_from_passphrase(passphrase_b, salt))[0])
    sample = b"".join(encrypt_block(os.urandom(16), rk_a) for _ in range(2000))
    stat, df = chi_square_uniform(sample)
    return {
        "plaintext_avalanche_pct": plaintext_avalanche(rk_a),
        "key_avalanche_pct": key_avalanche(rk_a, rk_b),
        "ciphertext_entropy": shannon_entropy(sample),
        "chi_square": stat,
        "chi_square_df": df,
        "chi_square_p": chi_square_p(stat, df),
        "keyspace_bits": keyspace_bits(),
        "throughput_mbps": throughput_mbps(rk_a, 2000),
        "rounds_curve": rounds_vs_avalanche(rk_a, trials=100),
    }
