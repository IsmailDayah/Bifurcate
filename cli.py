"""Bifurcate CLI — headless proof that the core works without the GUI.

The cross-machine gate: encrypting a file on one
machine and decrypting it on another, byte-identical.

    python cli.py keygen  --out keys/
    python cli.py encrypt --in demo.txt --out demo.bfc --pass "secret"
    python cli.py decrypt --in demo.bfc --out back.txt --pass "secret"
    python cli.py info    --in demo.bfc
    python cli.py selftest
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from bifurcate import container, hybrid
from bifurcate.mac import IntegrityError
from bifurcate.modes import MODE_CBC, MODE_ECB


def _read(path: str) -> bytes:
    return pathlib.Path(path).read_bytes()


def _write(path: str, data: bytes) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def cmd_keygen(args) -> int:
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    priv, pub = hybrid.generate_keypair()
    (out / "private.pem").write_bytes(hybrid.serialize_private(priv))
    (out / "public.pem").write_bytes(hybrid.serialize_public(pub))
    print(f"RSA-2048 keypair written to {out}/")
    print(f"  fingerprint: {hybrid.fingerprint(pub)}")
    return 0


def cmd_encrypt(args) -> int:
    data = _read(args.inp)
    mode = MODE_ECB if args.ecb else MODE_CBC
    if args.pubkey:
        pub = hybrid.load_public(_read(args.pubkey))
        blob = container.encrypt(data, public_key=pub, mode=mode)
    else:
        blob = container.encrypt(data, passphrase=args.password, mode=mode)
    _write(args.out, blob)
    print(f"encrypted {len(data)} B -> {args.out} ({len(blob)} B, mode={'ECB' if args.ecb else 'CBC'})")
    return 0


def cmd_decrypt(args) -> int:
    blob = _read(args.inp)
    try:
        if args.privkey:
            priv = hybrid.load_private(_read(args.privkey))
            data = container.decrypt(blob, private_key=priv)
        else:
            data = container.decrypt(blob, passphrase=args.password)
    except IntegrityError as exc:
        print(f"INTEGRITY FAIL: {exc}", file=sys.stderr)
        return 2
    _write(args.out, data)
    print(f"decrypted -> {args.out} ({len(data)} B)  [VERIFIED]")
    return 0


def cmd_info(args) -> int:
    c = container.parse(_read(args.inp))
    print(f"version    : {c.version}")
    print(f"mode       : {c.mode_name}")
    print(f"hybrid     : {c.is_hybrid}")
    print(f"salt       : {c.salt.hex()}")
    print(f"iv         : {c.iv.hex()}")
    print(f"wrapped_key: {len(c.wrapped_key)} B")
    print(f"ciphertext : {len(c.ciphertext)} B")
    print(f"tag        : {c.tag.hex()}")
    return 0


def cmd_selftest(args) -> int:
    """Round-trip every mode and both key paths — the on-stage 3-second proof."""
    ok = True
    msg = b"Bifurcate self-test: " + bytes(range(256)) * 3

    blob = container.encrypt(msg, passphrase="pw")
    ok &= container.decrypt(blob, passphrase="pw") == msg
    print(f"  passphrase CBC round-trip : {'OK' if ok else 'FAIL'}")

    blob = container.encrypt(msg, passphrase="pw", mode=MODE_ECB)
    r = container.decrypt(blob, passphrase="pw") == msg
    ok &= r
    print(f"  passphrase ECB round-trip : {'OK' if r else 'FAIL'}")

    priv, pub = hybrid.generate_keypair()
    blob = container.encrypt(msg, public_key=pub)
    r = container.decrypt(blob, private_key=priv) == msg
    ok &= r
    print(f"  hybrid RSA round-trip     : {'OK' if r else 'FAIL'}")

    blob = container.encrypt(msg, passphrase="pw")
    try:
        container.decrypt(blob, passphrase="wrong")
        r = False
    except IntegrityError:
        r = True
    ok &= r
    print(f"  wrong passphrase rejected : {'OK' if r else 'FAIL'}")

    tampered = bytearray(container.encrypt(msg, passphrase="pw"))
    tampered[60] ^= 0x01
    try:
        container.decrypt(bytes(tampered), passphrase="pw")
        r = False
    except IntegrityError:
        r = True
    ok &= r
    print(f"  tamper detected           : {'OK' if r else 'FAIL'}")

    print("SELF-TEST PASSED" if ok else "SELF-TEST FAILED")
    return 0 if ok else 1


def cmd_dump_vectors(args) -> int:
    """Freeze the Known-Answer Tests that BOTH implementations must reproduce.

    This is the single source of truth for the Python↔TypeScript cross-check.
    Every entry is deterministic, so the TypeScript
    port can load this same JSON and assert byte-for-byte equality.
    """
    import hashlib
    import json

    from bifurcate.chaos import ChaosEngine
    from bifurcate.cipher import decrypt_block, encrypt_block
    from bifurcate.container import PBKDF2_ITERATIONS, root_key_from_passphrase
    from bifurcate.kdf import derive_subkeys
    from bifurcate.keyschedule import expand
    from bifurcate.mac import compute_tag
    from bifurcate.modes import cbc_encrypt
    from bifurcate.sbox import generate_sbox

    hx = bytes.hex
    roots = [
        bytes(range(32)),
        bytes(32),
        bytes([0xFF]) * 32,
        hashlib.sha256(b"bifurcate-kat").digest(),
    ]
    cases: dict = {}

    # PBKDF2 — proves the TS WebCrypto PBKDF2 matches (same iterations/salt).
    cases["pbkdf2"] = [
        {"passphrase": pw, "salt": hx(salt), "root_key": hx(root_key_from_passphrase(pw, salt))}
        for pw, salt in [("password", bytes(16)), ("correct horse battery staple", bytes(range(16)))]
    ]
    # HKDF split.
    cases["hkdf"] = []
    for rk in roots:
        e, m = derive_subkeys(rk)
        cases["hkdf"].append({"root_key": hx(rk), "enc_seed": hx(e), "mac_key": hx(m)})
    # Chaos keystream (the integer map + sponge).
    cases["chaos"] = []
    for rk in roots[:3]:
        e, _ = derive_subkeys(rk)
        cases["chaos"].append({"enc_seed": hx(e), "stream64": hx(ChaosEngine(e).stream(64))})
    # Key-derived S-box.
    cases["sbox"] = []
    for rk in roots[:3]:
        e, _ = derive_subkeys(rk)
        cases["sbox"].append({"enc_seed": hx(e), "sbox": hx(generate_sbox(ChaosEngine(e)))})
    # Round schedule.
    cases["keyschedule"] = []
    for rk in roots[:3]:
        e, _ = derive_subkeys(rk)
        ks = expand(e)
        cases["keyschedule"].append(
            {"enc_seed": hx(e), "keys": [hx(k) for k in ks.keys], "rots": list(ks.rots)}
        )
    # Single-block encryption (the Feistel core) — with a round-trip assertion.
    cases["block"] = []
    for rk in roots[:3]:
        e, _ = derive_subkeys(rk)
        ks = expand(e)
        for pt in [bytes(16), bytes(range(16)), bytes([0xFF]) * 16]:
            ct = encrypt_block(pt, ks)
            assert decrypt_block(ct, ks) == pt, "round-trip failed while dumping vectors"
            cases["block"].append({"enc_seed": hx(e), "plaintext": hx(pt), "ciphertext": hx(ct)})
    # CBC with a FIXED iv (deterministic).
    cases["cbc"] = []
    for rk in roots[:2]:
        e, _ = derive_subkeys(rk)
        ks = expand(e)
        iv = bytes(range(16))
        for msg in [b"", b"hello", bytes(range(40))]:
            cases["cbc"].append(
                {"enc_seed": hx(e), "iv": hx(iv), "plaintext": hx(msg),
                 "ciphertext": hx(cbc_encrypt(msg, ks, iv))}
            )
    # HMAC tag.
    cases["mac"] = []
    for rk in roots[:2]:
        _, m = derive_subkeys(rk)
        for msg in [b"", b"authenticate me", bytes(range(64))]:
            cases["mac"].append({"mac_key": hx(m), "message": hx(msg), "tag": hx(compute_tag(m, msg))})

    payload = {
        "schema": "bifurcate-kat/1",
        "note": "Known-Answer Tests. Python and TypeScript MUST both reproduce every value.",
        "pbkdf2_iterations": PBKDF2_ITERATIONS,
        "cases": cases,
    }
    text = json.dumps(payload, indent=2)
    total = sum(len(v) for v in cases.values())
    if args.out:
        p = pathlib.Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"wrote {args.out} — {total} vectors across {len(cases)} categories")
    else:
        print(text)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="bifurcate", description="Bifurcate cipher CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen", help="generate an RSA-2048 keypair")
    k.add_argument("--out", default="keys")
    k.set_defaults(func=cmd_keygen)

    e = sub.add_parser("encrypt")
    e.add_argument("--in", dest="inp", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--pass", dest="password")
    e.add_argument("--pubkey")
    e.add_argument("--ecb", action="store_true", help="INSECURE demo mode")
    e.set_defaults(func=cmd_encrypt)

    d = sub.add_parser("decrypt")
    d.add_argument("--in", dest="inp", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--pass", dest="password")
    d.add_argument("--privkey")
    d.set_defaults(func=cmd_decrypt)

    i = sub.add_parser("info")
    i.add_argument("--in", dest="inp", required=True)
    i.set_defaults(func=cmd_info)

    s = sub.add_parser("selftest")
    s.set_defaults(func=cmd_selftest)

    dv = sub.add_parser("dump-vectors", help="freeze Known-Answer Tests for the TS cross-check")
    dv.add_argument("--out", default="shared/test_vectors.json")
    dv.set_defaults(func=cmd_dump_vectors)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
