# Bifurcate 🜂

**A chaos-seeded hybrid Feistel cipher, with an instrument-grade console.**

**▶ Live demo: [bifurcate.vercel.app](https://bifurcate.vercel.app)** — the cipher runs entirely
in your browser (nothing is uploaded). The web app is a TypeScript port of the Python
reference, cross-validated byte-for-byte against the same 36 known-answer vectors in
[`shared/test_vectors.json`](shared/test_vectors.json).

---

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

pytest -q                        # the test suite
python cli.py selftest           # round-trips every mode + both key paths
streamlit run app/Home.py        # the console
```

The cipher core in `bifurcate/` depends on **the Python standard library only**.
Everything in `requirements.txt` serves RSA, the GUI, the visuals, or the tests.

---

## What it is

A 128-bit block cipher with a 256-bit key and 12 Feistel rounds, whose
**substitution table and round keys are grown from the passphrase** by a
deterministic integer logistic map. Two passphrases are effectively two
different ciphers.

| Property | Value |
|---|---|
| Block size | 128 bits |
| Key size | 256 bits (keyspace 2²⁵⁶) |
| Rounds | 12 (justified empirically — see the rounds-vs-avalanche curve) |
| Structure | Feistel — F never needs to be invertible |
| S-box | 256 bytes, **derived from your key** |
| Mode | CBC + random IV (ECB available as a labelled counter-example) |
| Integrity | Encrypt-then-MAC, HMAC-SHA256 over the **whole container** |
| Hybrid | RSA-2048-OAEP wraps a random session key |

### The pipeline

```
passphrase ──PBKDF2(200k)──> root_key ──HKDF──> enc_seed ──> integer logistic map
                                    │                          │ (whitened by SHA-256)
                                    │                          ├─> key-derived S-box
                                    │                          └─> 12 round keys + rotations
                                    └──HKDF──> mac_key ──> HMAC over the whole container

plaintext ──PKCS#7──> CBC ──> 12 Feistel rounds ──> ciphertext ──> .bfc container + tag
```

---

## CLI

```bash
python cli.py keygen  --out keys/
python cli.py encrypt --in demo.txt --out demo.bfc --pass "secret"
python cli.py decrypt --in demo.bfc --out back.txt --pass "secret"
python cli.py info    --in demo.bfc
python cli.py selftest
```

Hybrid mode:

```bash
python cli.py encrypt --in demo.txt --out demo.bfc --pubkey keys/public.pem
python cli.py decrypt --in demo.bfc --out back.txt --privkey keys/private.pem
```

---

## The console

| Page | What it shows |
|---|---|
| **Home** | The bifurcation diagram, and a **live self-test** that proves correctness in seconds |
| **Encrypt** | Text / file / image; CBC or ECB; optional hybrid. Images dissolve to noise with a flattening histogram |
| **Decrypt** | The integrity verdict **first** — green VERIFIED or red INTEGRITY FAIL |
| **Round Visualizer** | A block crossing all 12 rounds. Amber = computed this round; dashed = copied verbatim (the Feistel guarantee, made visible) |
| **Security Analysis** | Avalanche, entropy, chi-square, the rounds-vs-avalanche curve, and RSA-vs-symmetric timing |
| **Keys** | RSA-2048 keypair generation for hybrid mode |
| **About** | Algorithm summary, **limitations stated plainly**, glossary, references |

---

## Design notes worth knowing

- **The chaos is integer, not floating point.** A float logistic map is not
  bit-identical across platforms; one differing bit breaks decryption
  irrecoverably. `chaos.py` uses fixed-point integer arithmetic, so the
  keystream is reproducible everywhere. (Floats appear only in the
  *bifurcation drawing*, which never touches key material.)
- **Chaos is not the security argument.** Raw states are whitened through
  SHA-256. Chaos supplies key-dependent *structure*; SHA-256 supplies
  *statistical quality*. This is deliberate — see the Alvarez & Li (2006) critique.
- **The MAC covers the entire container**, headers included, so the mode and
  hybrid flags cannot be downgraded undetected.
- **F is never inverted.** That is why an un-invertible chaotic S-box is safe
  here, and why decryption is structurally guaranteed.

---

## Honest limitations

Bifurcate is a study project, not a replacement for AES:

- no formal differential/linear cryptanalysis — empirical avalanche only
- not constant-time; no side-channel analysis
- no public peer review (AES has 25 years of it)
- pure-Python throughput, far below hardware-accelerated AES

---

## Layout

```
bifurcate/     the Python reference — stdlib only (except RSA)
cipher-ts/     the TypeScript port, cross-validated against it
web/           the browser build (Next.js)
app/           Streamlit console + design system
tests/         the test suite
shared/        known-answer vectors, shared by both implementations
cli.py         headless proof
assets/        demo images and exported figures
docs/          generated flowcharts
```

## License

MIT — see [`LICENSE`](LICENSE).
