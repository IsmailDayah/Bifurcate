"""Decrypt — the integrity verdict comes FIRST, always."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import imagepack  # noqa: E402
import theme  # noqa: E402
from bifurcate import container, hybrid  # noqa: E402
from bifurcate.mac import IntegrityError  # noqa: E402

st.set_page_config(page_title="Decrypt · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

MAX_TEXT_PREVIEW = 20_000

st.markdown("# Decrypt")
st.markdown(
    '<div class="lead">The tag is verified <b>before</b> a single byte is decrypted. '
    "Bifurcate never returns garbage — a failure is always explicit.</div>",
    unsafe_allow_html=True,
)

up = st.file_uploader("Encrypted container (.bfc)", type=["bfc"])

if up:
    blob = up.read()
    try:
        c = container.parse(blob)
    except Exception as exc:
        theme.banner("fail", f"Not a valid container — {exc}")
        st.stop()

    st.markdown("#### Header")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Version", c.version)
    h2.metric("Mode", c.mode_name)
    h3.metric("Hybrid", "yes" if c.is_hybrid else "no")
    h4.metric("Ciphertext", f"{len(c.ciphertext):,} B")
    st.caption(f"salt {c.salt.hex()}  ·  iv {c.iv.hex()}")

    st.divider()
    passphrase = None
    private_key = None
    if c.is_hybrid:
        pem = st.file_uploader("Your RSA private key (.pem)", type=["pem"])
        if pem:
            private_key = hybrid.load_private(pem.read())
    else:
        passphrase = st.text_input("Passphrase", type="password")

    if st.button("🔓  Verify & decrypt", use_container_width=True, type="primary"):
        try:
            eta_s = len(c.ciphertext) / 100_000
            spin_text = "Verifying tag, then decrypting…"
            if eta_s > 3:
                spin_text = (f"Verifying tag, then decrypting {len(c.ciphertext):,} bytes "
                             f"— roughly {eta_s:.0f} s at pure-Python speed…")
            with st.spinner(spin_text):
                data = container.decrypt(
                    blob,
                    passphrase=passphrase if not c.is_hybrid else None,
                    private_key=private_key if c.is_hybrid else None,
                )
        except IntegrityError as exc:
            # The one moment of theatre. Red appears only here.
            theme.banner("fail", str(exc))
            st.markdown(
                '<div class="lead">The passphrase is wrong, or the file was altered '
                "after it was sealed. No plaintext is produced.</div>",
                unsafe_allow_html=True,
            )
        except ValueError as exc:
            theme.banner("warn", str(exc))
        else:
            theme.banner("ok", f"VERIFIED — HMAC valid · {len(data):,} bytes recovered")

            recovered_img = imagepack.try_unpack(data)
            if recovered_img is not None:
                st.markdown("#### Recovered image")
                ic1, ic2 = st.columns([1, 1])
                ic1.image(
                    recovered_img,
                    caption=f"{recovered_img.width} × {recovered_img.height} — every pixel back in place",
                    use_container_width=True,
                )
                ic2.markdown(
                    '<div class="lead">The noise you saw on the Encrypt page was this '
                    "picture. Same passphrase, and it snaps back — one character "
                    "different, and you get the red banner instead.</div>",
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "⬇  Download recovered.png", imagepack.to_png_bytes(recovered_img),
                    file_name="recovered.png", mime="image/png",
                    use_container_width=True,
                )
            else:
                st.download_button(
                    "⬇  Download plaintext", data, file_name="recovered.bin",
                    use_container_width=True,
                )
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    st.markdown("#### Recovered bytes")
                    theme.hexblock(data)
                else:
                    st.markdown("#### Recovered text")
                    st.code(text[:MAX_TEXT_PREVIEW])
                    if len(text) > MAX_TEXT_PREVIEW:
                        st.caption(
                            f"Showing the first {MAX_TEXT_PREVIEW:,} of {len(text):,} "
                            "characters — download for the full text."
                        )
