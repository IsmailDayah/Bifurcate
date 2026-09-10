"""Keys — RSA-2048 keypair generation for hybrid mode."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import theme  # noqa: E402
from bifurcate import hybrid  # noqa: E402

st.set_page_config(page_title="Keys · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

st.markdown("# Keys")
st.markdown(
    '<div class="lead">Hybrid mode wraps a random 32-byte session key with RSA-2048-OAEP. '
    "The recipient unwraps it with their private key and derives the S-box and MAC key "
    "with no passphrase at all.</div>",
    unsafe_allow_html=True,
)

theme.banner("warn", "Research project — these keys are for the demo only. Never reuse them.")

st.divider()
if st.button("🔑  Generate RSA-2048 keypair", use_container_width=True, type="primary"):
    with st.spinner("generating…"):
        priv, pub = hybrid.generate_keypair()
    st.session_state["priv_pem"] = hybrid.serialize_private(priv)
    st.session_state["pub_pem"] = hybrid.serialize_public(pub)
    st.session_state["fp"] = hybrid.fingerprint(pub)

if "pub_pem" in st.session_state:
    theme.banner("ok", f"Keypair ready · public fingerprint {st.session_state['fp']}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Public key")
        st.caption("Share this. Anyone can encrypt to you with it.")
        st.code(st.session_state["pub_pem"].decode(), language="text")
        st.download_button("⬇  public.pem", st.session_state["pub_pem"],
                           file_name="public.pem", use_container_width=True)
    with c2:
        st.markdown("#### Private key")
        st.caption("Keep this secret. Required to decrypt hybrid containers.")
        st.code(st.session_state["priv_pem"].decode()[:400] + "\n…", language="text")
        st.download_button("⬇  private.pem", st.session_state["priv_pem"],
                           file_name="private.pem", use_container_width=True)

st.divider()
st.markdown("#### Why hybrid?")
c = st.columns(3)
c[0].metric("RSA-2048 max payload", f"{hybrid.max_plaintext_bytes()} B")
c[0].caption("hard OAEP limit per operation")
c[1].metric("Session key", "32 B")
c[1].caption("fits comfortably inside that limit")
c[2].metric("Your data", "unlimited")
c[2].caption("via the symmetric core")
st.markdown(
    '<div class="lead">RSA-OAEP at 2048 bits can carry only 190 bytes and is orders of '
    "magnitude slower than a block cipher. So we encrypt the <i>data</i> symmetrically and "
    "use RSA only to move the 32-byte key — the standard hybrid construction.</div>",
    unsafe_allow_html=True,
)
