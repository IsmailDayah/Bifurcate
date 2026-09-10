"""About — algorithm summary, limitations, references."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import theme  # noqa: E402

st.set_page_config(page_title="About · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

st.markdown("# About Bifurcate")
st.markdown(
    '<div class="lead">A key-dependent 12-round Feistel cipher whose S-box and round keys '
    "are grown from a deterministic integer logistic map, wrapped in an RSA hybrid "
    "envelope and authenticated end-to-end.</div>",
    unsafe_allow_html=True,
)

st.divider()
st.markdown("## The name")
st.markdown(
    """
**Bifurcation** is what the logistic map does as *r* rises: behaviour splits, splits again,
and collapses into chaos near *r* ≈ 3.57. We draw the keystream from **r = 3.99**.

**Bifurcation** is also exactly what a **Feistel network does to a block** — it splits it
into two halves and feeds them through each other.

One word, both the entropy source and the structure.
"""
)

st.divider()
st.markdown("## The algorithm, end to end")
st.markdown(
    """
| Step | What happens | Purpose |
|---|---|---|
| 1 | `PBKDF2-HMAC-SHA256`, 200 000 iterations | stretch a human passphrase to 256 bits; make dictionary attacks expensive |
| 2 | `HKDF` splits the root key into `enc_seed` + `mac_key` | **key separation** — encryption and authentication never share material |
| 3 | Integer fixed-point logistic map, whitened by SHA-256 | key-dependent structure with *deterministic*, platform-independent output |
| 4 | Fisher–Yates builds a **key-derived S-box** | the novelty: your passphrase defines your substitution table |
| 5 | 12 round keys + 12 rotation amounts (1–7, never 0) | every round mixes across byte boundaries |
| 6 | `F = XOR → S-box → rotate → permute` | confusion (substitution) + diffusion (rotation, permutation) |
| 7 | 12 **Feistel** rounds | invertible regardless of what F does |
| 8 | **CBC** with a random IV | identical plaintexts never produce identical ciphertexts |
| 9 | **Encrypt-then-MAC** over the whole container | tampering — including header downgrades — is always detected |
| 10 | Optional **RSA-2048-OAEP** wrap of the session key | hybrid mode |
"""
)

st.divider()
st.markdown("## Limitations — stated deliberately")
theme.banner("warn", "Bifurcate is a study project. It is not a replacement for AES.")
st.markdown(
    """
- **No formal cryptanalysis.** We report empirical avalanche and entropy, which are
  *necessary but not sufficient*. No differential or linear trail bounds are proven.
- **Not constant-time.** No side-channel resistance; timing and cache behaviour are unstudied.
- **No public review.** AES has 25 years of it; Bifurcate has none.
- **Pure Python throughput** is far below a hardware-accelerated AES implementation.
- **Chaos is not the security argument.** The literature (Alvarez & Li, 2006) shows naive
  chaos ciphers are frequently broken. We therefore use chaos as a *key-dependent
  structural generator* and delegate statistical quality to SHA-256 — a deliberate
  engineering choice, not a claim that chaos is inherently secure.
"""
)

st.divider()
st.markdown("## Glossary")
st.markdown(
    """
- **Feistel network** — a block-cipher structure that splits a block in two and applies a
  round function to one half; invertible even when that function is not.
- **S-box** — a substitution table providing non-linearity.
- **Confusion / diffusion** — Shannon's two design goals: obscure the key–ciphertext
  relationship, and spread each input bit's influence widely.
- **Avalanche effect** — one input bit flipping should change ~50% of output bits.
- **Logistic map** — `x → r·x·(1−x)`, a simple recurrence with chaotic behaviour.
- **Shannon entropy** — bits of information per byte; 8.000 is perfectly uniform.
- **PBKDF2 / HKDF** — key stretching and key derivation.
- **HMAC / encrypt-then-MAC** — authentication that is verified before decryption.
- **OAEP** — the padding scheme that makes RSA encryption secure.
- **IV** — initialisation vector; randomises CBC so repeats don't show.
"""
)

st.divider()
st.markdown("## References")
st.markdown(
    """
1. C. E. Shannon, "Communication Theory of Secrecy Systems," *Bell System Technical Journal*, 1949.
2. NIST, *FIPS 46-3: Data Encryption Standard*, 1999.
3. NIST, *FIPS 197: Advanced Encryption Standard*, 2001.
4. R. Matthews, "On the derivation of a chaotic encryption algorithm," *Cryptologia*, 1989.
5. M. S. Baptista, "Cryptography with chaos," *Physics Letters A*, 1998.
6. G. Alvarez and S. Li, "Some basic cryptographic requirements for chaos-based cryptosystems," *Int. J. Bifurcation and Chaos*, 2006.
7. J. Fridrich, "Symmetric ciphers based on two-dimensional chaotic maps," *Int. J. Bifurcation and Chaos*, 1998.
8. M. Bellare and C. Namprempre, "Authenticated Encryption: Relations among Notions," *ASIACRYPT*, 2000.
9. IETF, *RFC 8017: PKCS #1 v2.2 (RSA)*, 2016.
10. IETF, *RFC 5869: HKDF*, 2010.
11. R. M. May, "Simple mathematical models with very complicated dynamics," *Nature*, 1976.
"""
)

st.divider()
st.caption("Bifurcate v0.1")
