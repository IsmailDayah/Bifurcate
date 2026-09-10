"""Encrypt — text, files, and images; CBC or ECB; optional hybrid."""

from __future__ import annotations

import math
import pathlib
import sys
import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import imagepack  # noqa: E402
import theme  # noqa: E402
from bifurcate import container, hybrid  # noqa: E402
from bifurcate.analysis import histogram, shannon_entropy  # noqa: E402
from bifurcate.modes import MODE_CBC, MODE_ECB  # noqa: E402

st.set_page_config(page_title="Encrypt · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

st.markdown("# Encrypt")
st.markdown('<div class="lead">Turn anything into authenticated noise.</div>', unsafe_allow_html=True)

source = st.radio("Input", ["Text", "File", "Image"], horizontal=True)

payload: bytes | None = None
image: Image.Image | None = None

if source == "Text":
    text = st.text_area("Plaintext", "Attack at dawn — meet by the old pier.", height=120)
    payload = text.encode("utf-8")
elif source == "File":
    up = st.file_uploader("Any file")
    if up:
        payload = up.read()
else:
    up = st.file_uploader("Image (PNG/JPG)", type=["png", "jpg", "jpeg", "bmp"])
    if up:
        image = Image.open(up).convert("RGB")
        orig_size = image.size
        # A camera photo decodes to tens of MB of raw pixels — hours of work
        # for a pure-Python cipher. Cap the demo size; File mode still
        # encrypts the original bytes untouched.
        cap_label = st.select_slider(
            "Demo resolution cap (pure-Python cipher ≈ 0.1 MB/s — bigger is slower)",
            options=["256 px — fastest", "512 px — balanced", "original — can take minutes"],
            value="512 px — balanced",
        )
        if not cap_label.startswith("original"):
            cap = int(cap_label.split(" ")[0])
            if max(image.size) > cap:
                image = image.copy()
                image.thumbnail((cap, cap))
        if image.size != orig_size:
            st.caption(
                f"Downscaled {orig_size[0]}×{orig_size[1]} → {image.width}×{image.height} "
                "to keep the live demo fast. To encrypt the original file byte-for-byte, "
                "use **File** mode — it skips pixel decoding entirely."
            )
        # 12-byte size header inside the payload -> the image can snap back
        # after decryption (see app/imagepack.py).
        payload = imagepack.pack(image)
        eta = len(payload) / 100_000  # ≈ pure-Python seconds/byte, measured
        if eta > 60:
            theme.banner("warn", f"{len(payload):,} bytes of raw pixels ≈ {eta/60:.0f} min "
                                 "per encryption at pure-Python speed. Choose a smaller cap for the demo.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    mode_label = st.selectbox("Mode of operation", ["CBC (secure, default)", "ECB — INSECURE demo only"])
    mode = MODE_ECB if mode_label.startswith("ECB") else MODE_CBC
    if mode == MODE_ECB:
        theme.banner("fail", "ECB selected — identical blocks encrypt identically. Demo only.")
with c2:
    use_hybrid = st.checkbox("Hybrid mode (RSA-2048 wraps the session key)")
    compare_modes = False
    if image is not None:
        compare_modes = st.checkbox("Side-by-side CBC vs ECB comparison (the classic demo)")


def passphrase_bits(pw: str) -> float:
    """Crude entropy estimate: length x log2 of the character classes used."""
    charset = 0
    if any(c.islower() for c in pw):
        charset += 26
    if any(c.isupper() for c in pw):
        charset += 26
    if any(c.isdigit() for c in pw):
        charset += 10
    if any(not c.isalnum() for c in pw):
        charset += 33
    return len(pw) * math.log2(charset) if charset else 0.0


passphrase = None
public_key = None
if use_hybrid:
    pem = st.file_uploader("Recipient public key (.pem)", type=["pem"])
    if pem:
        public_key = hybrid.load_public(pem.read())
        theme.banner("ok", f"Public key loaded · fingerprint {hybrid.fingerprint(public_key)}")
else:
    passphrase = st.text_input("Passphrase", type="password", value="correct horse battery staple")
    if passphrase:
        bits = passphrase_bits(passphrase)
        label = "weak" if bits < 60 else ("fair" if bits < 100 else "strong")
        st.progress(min(bits / 128, 1.0), text=f"estimated strength ≈ {bits:.0f} bits — {label}")
        st.caption(
            "Estimate = length × log₂(character classes). PBKDF2's 200 000 iterations "
            "stretch whatever you type, but they cannot rescue a short passphrase."
        )

st.divider()

if st.button("🔒  Encrypt", use_container_width=True, type="primary"):
    if not payload:
        theme.banner("warn", "Nothing to encrypt — provide some input first.")
    elif use_hybrid and public_key is None:
        theme.banner("warn", "Hybrid mode needs a recipient public key.")
    elif not use_hybrid and not passphrase:
        theme.banner("warn", "Enter a passphrase.")
    else:
        eta_s = len(payload) / 100_000
        spin_text = f"Encrypting {len(payload):,} bytes…"
        if eta_s > 3:
            spin_text = f"Encrypting {len(payload):,} bytes — roughly {eta_s:.0f} s at pure-Python speed…"
        t0 = time.perf_counter()
        with st.spinner(spin_text):
            blob = container.encrypt(
                payload,
                passphrase=passphrase if not use_hybrid else None,
                public_key=public_key if use_hybrid else None,
                mode=mode,
            )
        elapsed = (time.perf_counter() - t0) * 1000
        c = container.parse(blob)

        theme.banner("ok", f"Encrypted {len(payload):,} bytes in {max(elapsed, 0.1):,.1f} ms · mode {c.mode_name}")

        ct_entropy = shannon_entropy(c.ciphertext)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Plaintext entropy", f"{shannon_entropy(payload):.3f}")
        m1.caption("bits/byte")
        m2.metric("Ciphertext entropy", f"{ct_entropy:.3f}")
        m2.caption("bits/byte · 8.000 = perfectly uniform")
        m3.metric("Container size", f"{len(blob):,} B")
        m3.caption("salt + IV + ciphertext + tag")
        m4.metric("Overhead", f"{len(blob) - len(payload)} B")
        m4.caption("header, padding and HMAC tag")
        if len(c.ciphertext) < 4096:
            st.caption(
                f"ℹ A {len(c.ciphertext)}-byte sample can reach at most "
                f"log₂({len(c.ciphertext)}) ≈ {math.log2(len(c.ciphertext)):.2f} bits/byte — "
                "short messages cap the entropy readout, not the cipher. "
                "Encrypt a file or image to see it approach 8.000."
            )

        st.download_button(
            "⬇  Download .bfc", blob, file_name="message.bfc",
            mime="application/octet-stream", use_container_width=True,
        )

        st.markdown("#### Ciphertext")
        theme.hexblock(c.ciphertext)

        # -- image dissolves, histogram flattens ----
        if image is not None:
            st.markdown("#### The dissolve")
            w, h = image.size
            enc_img = None
            noise = np.frombuffer(c.ciphertext[: w * h * 3], dtype=np.uint8)
            if noise.size >= w * h * 3:
                enc_img = Image.fromarray(noise[: w * h * 3].reshape(h, w, 3))
                ic1, ic2 = st.columns(2)
                ic1.image(image, caption="original", use_container_width=True)
                ic2.image(
                    enc_img,
                    caption=f"encrypted ({c.mode_name})",
                    use_container_width=True,
                )
            if c.mode == MODE_ECB:
                theme.banner(
                    "fail",
                    "Look closely: the outline survives. ECB encrypts identical blocks "
                    "identically, so large uniform areas keep their shape — this is why "
                    "CBC is the default.",
                )

            if compare_modes:
                st.markdown("#### CBC vs ECB — same image, same key")
                other_mode = MODE_ECB if mode == MODE_CBC else MODE_CBC
                with st.spinner("Encrypting a second time for the comparison…"):
                    blob2 = container.encrypt(
                        payload,
                        passphrase=passphrase if not use_hybrid else None,
                        public_key=public_key if use_hybrid else None,
                        mode=other_mode,
                    )
                c2p = container.parse(blob2)
                noise2 = np.frombuffer(c2p.ciphertext[: w * h * 3], dtype=np.uint8)
                pair = {c.mode_name: enc_img}
                if noise2.size >= w * h * 3:
                    pair[c2p.mode_name] = Image.fromarray(noise2[: w * h * 3].reshape(h, w, 3))
                cc1, cc2 = st.columns(2)
                cbc_img, ecb_img = pair.get("CBC"), pair.get("ECB")
                if cbc_img is not None:
                    cc1.image(cbc_img, caption="CBC — pure noise, no structure", use_container_width=True)
                if ecb_img is not None:
                    cc2.image(ecb_img, caption="ECB — the outline leaks (INSECURE)", use_container_width=True)
                st.caption(
                    "The famous “ECB penguin”: identical plaintext blocks → identical "
                    "ciphertext blocks, so uniform regions of the image survive encryption. "
                    "CBC chains each block into the next, so nothing survives."
                )

            st.markdown("#### Histogram — peaky becomes flat")
            hp, hc = histogram(payload), histogram(c.ciphertext)
            fig = go.Figure()
            fig.add_bar(y=hp, name="plaintext", marker_color=theme.MUTED, opacity=0.75)
            fig.add_bar(y=hc, name="ciphertext", marker_color=theme.TRAIL, opacity=0.85)
            fig.update_layout(barmode="overlay", height=320,
                              xaxis_title="byte value", yaxis_title="frequency")
            st.plotly_chart(theme.style_fig(fig), use_container_width=True)
            if ct_entropy > 7.99:
                theme.banner(
                    "ok",
                    f"Entropy {shannon_entropy(payload):.3f} → {ct_entropy:.3f} bits/byte "
                    "(8.000 is perfectly uniform)",
                )
            else:
                theme.banner(
                    "warn",
                    f"Entropy {shannon_entropy(payload):.3f} → {ct_entropy:.3f} bits/byte — "
                    "below the 7.99 target because ECB repeats identical blocks. "
                    "That residual structure is exactly what this demo mode is for.",
                )
