"""Envelope tests — modes, MAC, hybrid, container."""

from __future__ import annotations

import os

import pytest

from bifurcate import container, hybrid
from bifurcate.analysis import shannon_entropy
from bifurcate.container import FLAG_ECB, FLAG_HYBRID, FormatError, parse
from bifurcate.kdf import derive_subkeys
from bifurcate.keyschedule import expand
from bifurcate.mac import IntegrityError
from bifurcate.modes import (
    MODE_CBC,
    MODE_ECB,
    cbc_decrypt,
    cbc_encrypt,
    ecb_decrypt,
    ecb_encrypt,
    pad,
    unpad,
)

PW = "correct horse battery staple"


def _rk(pw: str = PW):
    return expand(derive_subkeys(container.root_key_from_passphrase(pw, b"\x00" * 16))[0])


# --------------------------------------------------------------------------
# Padding
# --------------------------------------------------------------------------
@pytest.mark.parametrize("n", list(range(0, 40)))
def test_pkcs7_roundtrip(n):
    data = os.urandom(n)
    padded = pad(data)
    assert len(padded) % 16 == 0
    assert len(padded) > len(data)  # always pads, even exact multiples
    assert unpad(padded) == data


def test_pkcs7_rejects_bad_padding():
    with pytest.raises(ValueError):
        unpad(b"\x00" * 15 + b"\x05")
    with pytest.raises(ValueError):
        unpad(b"")


# --------------------------------------------------------------------------
# Test 2 — round trip for every length 0..1000 (CBC + padding edges)
# --------------------------------------------------------------------------
def test_cbc_roundtrip_all_lengths():
    rk = _rk()
    iv = os.urandom(16)
    for n in range(0, 1001):
        data = os.urandom(n)
        assert cbc_decrypt(cbc_encrypt(data, rk, iv), rk, iv) == data


def test_ecb_roundtrip_all_lengths():
    rk = _rk()
    for n in range(0, 300):
        data = os.urandom(n)
        assert ecb_decrypt(ecb_encrypt(data, rk), rk) == data


def test_ecb_leaks_repetition_but_cbc_does_not():
    """The 'ECB penguin' argument, as an assertion."""
    rk = _rk()
    plain = b"A" * 64  # four identical blocks
    ecb = ecb_encrypt(plain, rk)
    blocks = {ecb[i : i + 16] for i in range(0, 64, 16)}
    assert len(blocks) == 1, "ECB should repeat identical blocks"
    cbc = cbc_encrypt(plain, rk, os.urandom(16))
    blocks = {cbc[i : i + 16] for i in range(0, 64, 16)}
    assert len(blocks) == 4, "CBC must not repeat"


# --------------------------------------------------------------------------
# Test 10 — IV uniqueness: identical plaintext -> distinct ciphertext
# --------------------------------------------------------------------------
def test_identical_plaintexts_encrypt_differently():
    msg = b"the same message every time"
    seen = {container.encrypt(msg, passphrase=PW) for _ in range(200)}
    assert len(seen) == 200


# --------------------------------------------------------------------------
# Container round trips
# --------------------------------------------------------------------------
def test_container_roundtrip_passphrase():
    for n in (0, 1, 15, 16, 17, 1000):
        msg = os.urandom(n)
        blob = container.encrypt(msg, passphrase=PW)
        assert container.decrypt(blob, passphrase=PW) == msg


def test_container_roundtrip_ecb_flagged():
    msg = b"ecb demo"
    blob = container.encrypt(msg, passphrase=PW, mode=MODE_ECB)
    c = parse(blob)
    assert c.flags & FLAG_ECB and c.mode == MODE_ECB and c.mode_name == "ECB"
    assert container.decrypt(blob, passphrase=PW) == msg


def test_container_fields_are_wellformed():
    blob = container.encrypt(b"x" * 100, passphrase=PW)
    c = parse(blob)
    assert c.version == 1
    assert len(c.salt) == 16 and len(c.iv) == 16 and len(c.tag) == 32
    assert not c.is_hybrid and c.wrapped_key == b""
    assert len(c.ciphertext) % 16 == 0


def test_parse_rejects_garbage():
    with pytest.raises(FormatError):
        parse(b"not a container at all")
    with pytest.raises(FormatError):
        parse(b"XXXX" + b"\x00" * 100)


# --------------------------------------------------------------------------
# Test 7/8 — authentication: wrong key and tampering
# --------------------------------------------------------------------------
def test_wrong_passphrase_raises_never_returns_garbage():
    blob = container.encrypt(b"secret", passphrase=PW)
    with pytest.raises(IntegrityError):
        container.decrypt(blob, passphrase=PW + "x")


def test_every_single_bit_flip_in_a_byte_is_detected():
    """Flip each of the 8 bits of one ciphertext byte — all must be caught."""
    blob = container.encrypt(b"authenticate me" * 4, passphrase=PW)
    pos = len(blob) - 40  # inside the ciphertext
    for bit in range(8):
        bad = bytearray(blob)
        bad[pos] ^= 1 << bit
        with pytest.raises(IntegrityError):
            container.decrypt(bytes(bad), passphrase=PW)


def test_header_tampering_is_detected():
    """v1.1 full-container MAC: flipping the mode/hybrid FLAGS must be caught.

    This is the downgrade attack the earlier draft was vulnerable to.
    """
    blob = container.encrypt(b"downgrade me", passphrase=PW)
    bad = bytearray(blob)
    bad[5] ^= FLAG_ECB  # flip CBC -> ECB in the flags byte
    with pytest.raises(IntegrityError):
        container.decrypt(bytes(bad), passphrase=PW)


def test_salt_and_iv_tampering_is_detected():
    blob = container.encrypt(b"msg", passphrase=PW)
    for offset in (6, 22):  # salt, iv
        bad = bytearray(blob)
        bad[offset] ^= 0xFF
        with pytest.raises(IntegrityError):
            container.decrypt(bytes(bad), passphrase=PW)


def test_truncation_is_detected():
    blob = container.encrypt(b"a" * 64, passphrase=PW)
    with pytest.raises((IntegrityError, FormatError)):
        container.decrypt(blob[:-16], passphrase=PW)


# --------------------------------------------------------------------------
# Test 9 — hybrid RSA
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def keypair():
    return hybrid.generate_keypair()


def test_hybrid_roundtrip(keypair):
    priv, pub = keypair
    msg = b"hybrid envelope test " * 10
    blob = container.encrypt(msg, public_key=pub)
    c = parse(blob)
    assert c.is_hybrid and c.flags & FLAG_HYBRID
    assert len(c.wrapped_key) == hybrid.WRAPPED_LEN
    assert container.decrypt(blob, private_key=priv) == msg


def test_hybrid_needs_no_passphrase(keypair):
    """Both modes funnel through derive_subkeys, so hybrid needs no passphrase."""
    priv, pub = keypair
    blob = container.encrypt(b"no passphrase here", public_key=pub)
    assert container.decrypt(blob, private_key=priv) == b"no passphrase here"


def test_wrong_private_key_raises(keypair):
    _, pub = keypair
    other_priv, _ = hybrid.generate_keypair()
    blob = container.encrypt(b"nope", public_key=pub)
    with pytest.raises(IntegrityError):
        container.decrypt(blob, private_key=other_priv)


def test_pem_roundtrip(keypair):
    priv, pub = keypair
    p2 = hybrid.load_private(hybrid.serialize_private(priv))
    u2 = hybrid.load_public(hybrid.serialize_public(pub))
    key = hybrid.new_root_key()
    assert hybrid.unwrap_key(p2, hybrid.wrap_key(u2, key)) == key


def test_rsa_capacity_is_the_reason_for_hybrid():
    """190 bytes at 2048-bit — the number that justifies hybrid encryption."""
    assert hybrid.max_plaintext_bytes(2048) == 190


def test_encrypt_requires_exactly_one_key_source(keypair):
    _, pub = keypair
    with pytest.raises(ValueError):
        container.encrypt(b"x")
    with pytest.raises(ValueError):
        container.encrypt(b"x", passphrase=PW, public_key=pub)


# --------------------------------------------------------------------------
# Statistical sanity of real ciphertext
# --------------------------------------------------------------------------
def test_ciphertext_entropy_is_high():
    blob = container.encrypt(b"A" * 60_000, passphrase=PW)
    c = parse(blob)
    assert shannon_entropy(c.ciphertext) > 7.99
