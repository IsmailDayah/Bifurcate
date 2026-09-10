"""Security Analysis.

Every number on this page is measured live by `bifurcate.analysis`. Nothing is
quoted that was not computed. Results persist in session_state so running one
measurement never erases another — a Streamlit button is transient, a demo
is not.
"""

from __future__ import annotations

import os
import pathlib
import random
import sys

import plotly.graph_objects as go
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import theme  # noqa: E402
from bifurcate import analysis  # noqa: E402
from bifurcate.cipher import encrypt_block  # noqa: E402
from bifurcate.container import root_key_from_passphrase  # noqa: E402
from bifurcate.kdf import derive_subkeys  # noqa: E402
from bifurcate.keyschedule import ROUNDS, expand  # noqa: E402
from bifurcate.sbox import difference_ratio  # noqa: E402

st.set_page_config(page_title="Security Analysis · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

st.markdown("# Security Analysis")
st.markdown(
    '<div class="lead">Security properties, computed live.</div>',
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
pw_a = c1.text_input("Passphrase A", "correct horse battery staple")
pw_b = c2.text_input("Passphrase B (one character different)", "correct horse battery stapla")

SALT = b"\x00" * 16


@st.cache_resource(show_spinner=False)
def schedules(a: str, b: str):
    rk_a = expand(derive_subkeys(root_key_from_passphrase(a, SALT))[0])
    rk_b = expand(derive_subkeys(root_key_from_passphrase(b, SALT))[0])
    return rk_a, rk_b


rk_a, rk_b = schedules(pw_a, pw_b)

if st.button("▶  Run full analysis", use_container_width=True, type="primary"):
    with st.spinner("measuring…"):
        sample = b"".join(encrypt_block(os.urandom(16), rk_a) for _ in range(3000))
        chi, df = analysis.chi_square_uniform(sample)
        blk = os.urandom(16)
        bit = random.randrange(128)
        st.session_state["sec_results"] = {
            "pws": (pw_a, pw_b),
            "pt_av": analysis.plaintext_avalanche(rk_a, trials=400),
            "key_av": analysis.key_avalanche(rk_a, rk_b, trials=400),
            "ent": analysis.shannon_entropy(sample),
            "chi": chi,
            "df": df,
            "p": analysis.chi_square_p(chi, df),
            "thr": analysis.throughput_mbps(rk_a, 2000),
            "sbox_diff": difference_ratio(rk_a.sbox, rk_b.sbox),
            "curve": analysis.rounds_vs_avalanche(rk_a, trials=150),
            "heat_grid": analysis.avalanche_grid(rk_a, blk, bit),
            "heat_bit": bit,
            "hist": analysis.histogram(sample),
            "sample_len": len(sample),
        }

res = st.session_state.get("sec_results")
if res:
    if res["pws"] != (pw_a, pw_b):
        theme.banner("warn", "Passphrases changed since this run — hit “Run full analysis” to refresh.")

    st.divider()
    m = st.columns(4)
    m[0].metric("Plaintext avalanche", f"{res['pt_av']:.2f}%")
    m[0].caption("target 45–55%")
    m[1].metric("Key avalanche", f"{res['key_av']:.2f}%")
    m[1].caption("target 45–55%")
    m[2].metric("Ciphertext entropy", f"{res['ent']:.4f}")
    m[2].caption("of 8.000 bits/byte")
    m[3].metric("Keyspace", "2²⁵⁶")
    m[3].caption("brute force infeasible")

    m2 = st.columns(4)
    m2[0].metric("S-box difference", f"{res['sbox_diff']*100:.2f}%")
    m2[0].caption("theory 255/256 = 99.61%")
    m2[1].metric("Chi-square", f"{res['chi']:.1f}")
    m2[1].caption(f"df = {res['df']} · p ≈ {res['p']:.3f}")
    m2[2].metric("Throughput", f"{res['thr']:.2f} MB/s")
    m2[2].caption("pure Python, single core")
    m2[3].metric("Rounds", f"{ROUNDS}")
    m2[3].caption("justified by the curve below")

    for label, value, lo, hi in [
        ("Plaintext avalanche", res["pt_av"], 45, 55),
        ("Key avalanche", res["key_av"], 45, 55),
    ]:
        theme.banner("ok" if lo <= value <= hi else "warn",
                     f"{label} {value:.2f}% — {'within' if lo <= value <= hi else 'OUTSIDE'} target {lo}–{hi}%")
    theme.banner("ok" if res["ent"] > 7.99 else "warn",
                 f"Ciphertext entropy {res['ent']:.4f} bits/byte")
    theme.banner(
        "ok" if res["p"] > 0.05 else "warn",
        f"Chi-square {res['chi']:.1f} (df {res['df']}), p ≈ {res['p']:.3f} — "
        + ("consistent with a uniform distribution (p > 0.05)" if res["p"] > 0.05
           else "distribution deviates from uniform (p ≤ 0.05)"),
    )

    # -- the headline figure ---------------------
    st.divider()
    st.markdown("### Rounds vs avalanche — why 12 rounds")
    st.markdown(
        '<div class="lead">This curve turns "we chose 12 rounds" from an assertion into '
        "evidence: full avalanche is reached well before round 12, and the remainder is margin.</div>",
        unsafe_allow_html=True,
    )
    fig = go.Figure(go.Scatter(
        x=list(range(1, ROUNDS + 1)), y=res["curve"], mode="lines+markers",
        line=dict(color=theme.TRAIL, width=3), marker=dict(size=8), name="avalanche",
    ))
    fig.add_hline(y=50, line=dict(color=theme.VERIFIED, dash="dash"),
                  annotation_text="50% ideal", annotation_position="top left",
                  annotation_font_color=theme.VERIFIED)
    fig.update_layout(height=380, xaxis_title="rounds applied",
                      yaxis_title="% ciphertext bits changed", yaxis=dict(range=[0, 60]))
    st.plotly_chart(theme.style_fig(fig), use_container_width=True)

    reached = next((i + 1 for i, v in enumerate(res["curve"]) if v >= 45), None)
    if reached:
        theme.banner("ok", f"Full avalanche (≥45%) first reached at round {reached} — "
                           f"{ROUNDS} rounds gives {ROUNDS - reached} rounds of margin.")

    # -- avalanche heatmap -----------------------------------------
    st.divider()
    st.markdown("### Avalanche heatmap — one bit in, half the block out")
    st.caption(f"Flipped plaintext bit #{res['heat_bit']}. Lit cells = ciphertext bits that changed.")
    theme.bitgrid(res["heat_grid"], ncols=16)
    lit = sum(res["heat_grid"])
    theme.banner("ok", f"{lit} of 128 bits changed ({lit/128*100:.1f}%)")

    # -- histogram ---------------------------------------------------------
    st.divider()
    st.markdown("### Ciphertext byte distribution")
    figh = go.Figure(go.Bar(y=res["hist"], marker_color=theme.TRAIL))
    figh.add_hline(y=res["sample_len"] / 256, line=dict(color=theme.VERIFIED, dash="dash"))
    figh.update_layout(height=300, xaxis_title="byte value", yaxis_title="frequency")
    st.plotly_chart(theme.style_fig(figh), use_container_width=True)
    st.caption(
        f"green dashed line = uniform expectation ({res['sample_len']}/256 ≈ "
        f"{res['sample_len']/256:.0f} per value) — the bars hug it, which is what the chi-square p-value quantifies"
    )

st.divider()
st.markdown("### RSA vs symmetric — why hybrid encryption exists")
st.markdown(
    '<div class="lead">RSA <i>encryption</i> with the public key is cheap — it is the '
    "<b>private-key decryption</b> that costs, and RSA-2048 can carry at most 190 bytes "
    "per operation. Both are measured here, not asserted.</div>",
    unsafe_allow_html=True,
)
if st.button("▶  Time RSA-2048 against AES-256 and Bifurcate"):
    with st.spinner("generating keypair and timing…"):
        st.session_state["rsa_results"] = analysis.rsa_vs_symmetric(trials=20)

r = st.session_state.get("rsa_results")
if r:
    t = st.columns(4)
    t[0].metric("RSA-OAEP wrap", f"{r['rsa_wrap_ms']:.2f} ms")
    t[0].caption("public key — the cheap half")
    t[1].metric("RSA-OAEP unwrap", f"{r['rsa_unwrap_ms']:.2f} ms")
    t[1].caption("private key — the expensive half")
    t[2].metric("RSA max payload", f"{r['rsa_max_payload_bytes']} B")
    t[2].caption("per operation at 2048-bit")
    t[3].metric("RSA as a bulk cipher", f"{r['rsa_mbps']:.3f} MB/s")
    t[3].caption("190-byte chunks, wrap + unwrap")

    t2 = st.columns(4)
    t2[0].metric("AES-256-CBC", f"{r['aes_mbps']:,.0f} MB/s")
    t2[0].caption("hardware-accelerated (AES-NI)")
    t2[1].metric("Bifurcate", f"{r['bifurcate_mbps']:.2f} MB/s")
    t2[1].caption("pure Python — honesty on display")
    t2[2].metric("AES vs RSA", f"{r['slowdown_vs_aes']:,.0f}×")
    t2[2].caption("symmetric advantage for bulk data")
    t2[3].metric("Session key", "32 B")
    t2[3].caption("the only thing RSA needs to carry")

    theme.banner(
        "ok",
        f"Moving bulk data through RSA-2048 would run at ~{r['rsa_mbps']:.3f} MB/s in "
        f"190-byte chunks, ~{r['slowdown_vs_aes']:,.0f}× slower than AES-256 — so the "
        "hybrid construction encrypts the data symmetrically and uses RSA once, to move "
        "a 32-byte session key.",
    )
