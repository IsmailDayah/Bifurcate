"""Frozen known-answer tests.

`test_engine.py` proves determinism *within one process*. This file proves it
against values frozen on 2026-07-21: if the keystream, S-box, key schedule or
Feistel core ever drifts — a refactor, a platform difference, an accidental
float — these fail loudly. This is the cross-machine guarantee the container
format depends on.
"""

from __future__ import annotations

import json
import pathlib

from bifurcate.chaos import ChaosEngine
from bifurcate.cipher import decrypt_block, encrypt_block
from bifurcate.kdf import derive_subkeys
from bifurcate.keyschedule import expand

VECTORS = json.loads(
    (pathlib.Path(__file__).parent / "test_vectors.json").read_text(encoding="utf-8")
)

ROOT = bytes.fromhex(VECTORS["root_key"])


def test_kdf_matches_frozen_vector():
    enc_seed, mac_key = derive_subkeys(ROOT)
    assert enc_seed.hex() == VECTORS["enc_seed"]
    assert mac_key.hex() == VECTORS["mac_key"]


def test_keystream_matches_frozen_vector():
    enc_seed, _ = derive_subkeys(ROOT)
    assert ChaosEngine(enc_seed).stream(64).hex() == VECTORS["keystream_64"]


def test_key_schedule_matches_frozen_vector():
    rk = expand(derive_subkeys(ROOT)[0])
    assert rk.sbox.hex() == VECTORS["sbox"]
    assert [k.hex() for k in rk.keys] == VECTORS["round_keys"]
    assert list(rk.rots) == VECTORS["rotations"]


def test_block_cipher_matches_frozen_vector():
    rk = expand(derive_subkeys(ROOT)[0])
    pt = bytes.fromhex(VECTORS["plaintext_block"])
    ct = bytes.fromhex(VECTORS["ciphertext_block"])
    assert encrypt_block(pt, rk) == ct
    assert decrypt_block(ct, rk) == pt
