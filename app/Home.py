"""Bifurcate console — Home.

Run:  streamlit run app/Home.py
"""

from __future__ import annotations

import pathlib
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import theme  # noqa: E402  (local module, needs the path insert above)
from bifurcate.chaos import orbit  # noqa: E402

st.set_page_config(page_title="Bifurcate", page_icon="🜂", layout="wide")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
theme.apply()


# -- the title card ---------------------------------------------------------
st.markdown("# Bifurcate")
st.markdown(
    '<div class="lead">A chaos-seeded hybrid Feistel cipher. The substitution table '
    "and every round key are <b>grown from your passphrase</b> by a deterministic "
    "logistic map — two passphrases are effectively two different ciphers.</div>",
    unsafe_allow_html=True,
)

st.markdown("")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Block size", "128 bits")
c2.metric("Key size", "256 bits")
c3.metric("Rounds", "12")
c4.metric("Keyspace", "2²⁵⁶")


# -- hero: the bifurcation diagram ----------------------------------
st.markdown("### The bifurcation diagram")
st.markdown(
    '<div class="lead">As <i>r</i> increases the logistic map splits, splits again, and '
    "collapses into chaos near <i>r</i> ≈ 3.57. Bifurcate draws its keystream from "
    "<b>r = 3.99</b> — deep in the chaotic band. The same word describes what a Feistel "
    "network does to a block: it <b>bifurcates</b> it into two halves.</div>",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def bifurcation_points(r_min=2.5, r_max=4.0, steps=900, keep=90):
    xs, ys = [], []
    for i in range(steps):
        r = r_min + (r_max - r_min) * i / (steps - 1)
        for v in orbit(0.5, r, keep, skip=250):
            xs.append(r)
            ys.append(v)
    return xs, ys


xs, ys = bifurcation_points()
fig = go.Figure(
    go.Scattergl(
        x=xs, y=ys, mode="markers",
        marker=dict(
            size=1.4, opacity=0.32, color=ys,
            colorscale=[[0.0, "#92400E"], [0.5, theme.TRAIL], [1.0, theme.TRAIL_SOFT]],
        ),
        hoverinfo="skip",
    )
)
fig.add_vline(
    x=3.99, line=dict(color=theme.VERIFIED, width=2, dash="dash"),
    annotation_text="r = 3.99 — our operating point",
    annotation_position="top left",
    annotation_font_color=theme.VERIFIED,
)
fig.update_layout(
    height=460, xaxis_title="growth parameter r", yaxis_title="orbit x",
    xaxis=dict(range=[2.45, 4.08]),  # margin so the r=3.99 annotation never clips
)
st.plotly_chart(theme.style_fig(fig), use_container_width=True)

st.caption(
    "Visualisation only — drawn in floating point. The cipher itself uses an integer "
    "fixed-point map so the keystream is bit-identical on every machine."
)

st.divider()

# -- live self-test (the live correctness proof) -----------------------------
left, right = st.columns([1, 1])

with left:
    st.markdown("### Live self-test")
    st.markdown(
        '<div class="lead">Proves correctness in three seconds: round-trips '
        "every mode and both key paths, then confirms a wrong passphrase and a tampered "
        "byte are both rejected.</div>",
        unsafe_allow_html=True,
    )
    if st.button("▶  Run self-test", use_container_width=True):
        from bifurcate import container, hybrid
        from bifurcate.mac import IntegrityError
        from bifurcate.modes import MODE_ECB

        msg = b"Bifurcate self-test " + bytes(range(256)) * 2
        results = []

        blob = container.encrypt(msg, passphrase="pw")
        results.append(("Passphrase CBC round-trip", container.decrypt(blob, passphrase="pw") == msg))

        blob = container.encrypt(msg, passphrase="pw", mode=MODE_ECB)
        results.append(("Passphrase ECB round-trip", container.decrypt(blob, passphrase="pw") == msg))

        with st.spinner("generating RSA-2048 keypair…"):
            priv, pub = hybrid.generate_keypair()
        blob = container.encrypt(msg, public_key=pub)
        results.append(("Hybrid RSA round-trip", container.decrypt(blob, private_key=priv) == msg))

        blob = container.encrypt(msg, passphrase="pw")
        try:
            container.decrypt(blob, passphrase="wrong")
            ok = False
        except IntegrityError:
            ok = True
        results.append(("Wrong passphrase rejected", ok))

        bad = bytearray(container.encrypt(msg, passphrase="pw"))
        bad[60] ^= 0x01
        try:
            container.decrypt(bytes(bad), passphrase="pw")
            ok = False
        except IntegrityError:
            ok = True
        results.append(("Tampered byte detected", ok))
        st.session_state["selftest"] = results

    for name, passed in st.session_state.get("selftest", []):
        theme.banner("ok" if passed else "fail", f"{name} — {'OK' if passed else 'FAILED'}")
    if st.session_state.get("selftest") and all(p for _, p in st.session_state["selftest"]):
        theme.banner("ok", "SELF-TEST PASSED — all five checks green")

with right:
    st.markdown("### How it works")
    st.markdown(
        """
1. **PBKDF2-HMAC-SHA256** (200 000 iterations) stretches your passphrase into a 256-bit `root_key`.
2. **HKDF** splits it into an encryption seed and a separate MAC key — *key separation*.
3. The seed drives a **deterministic integer logistic map**, whitened through SHA-256.
4. That stream builds a **key-derived S-box** (Fisher–Yates) and **12 round keys + rotations**.
5. **12 Feistel rounds** encrypt each 128-bit block; **CBC** with a random IV chains them.
6. **Encrypt-then-MAC** authenticates the whole container — tampering is always caught.
7. Optionally **RSA-2048-OAEP** wraps the session key for hybrid mode.
        """
    )
    theme.banner("warn", "Research project — not for production use. See About.")

st.divider()
st.caption(
    "Bifurcate v0.1 — "
    "encryption and decryption are the same function; only the key order flips."
)
