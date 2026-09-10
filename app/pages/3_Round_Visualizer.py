"""Round Visualizer.

The clearest artefact in the console: it makes the flowchart
move. Watch a 128-bit block cross the Feistel network, round by round, with the
bits that changed this round glowing amber.
"""

from __future__ import annotations

import os
import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

import theme  # noqa: E402
from bifurcate.container import root_key_from_passphrase  # noqa: E402
from bifurcate.kdf import derive_subkeys  # noqa: E402
from bifurcate.keyschedule import ROUNDS, expand  # noqa: E402
from bifurcate.round import F  # noqa: E402

st.set_page_config(page_title="Round Visualizer · Bifurcate", page_icon="🜂", layout="wide")
theme.apply()

st.markdown("# Round Visualizer")
st.markdown(
    '<div class="lead">Twelve Feistel rounds. Each row shows the halves <b>L</b> and '
    "<b>R</b> after that round; bytes that changed are lit. Notice that <b>R becomes "
    "the next L</b> untouched — that is the Feistel guarantee which makes decryption "
    "work no matter what the round function does.</div>",
    unsafe_allow_html=True,
)

c1, c2 = st.columns([2, 1])
with c1:
    pw = st.text_input("Passphrase", value="correct horse battery staple")
with c2:
    if st.button("🎲 Random block", use_container_width=True):
        st.session_state["blk"] = os.urandom(16).hex()

block_hex = st.text_input(
    "Plaintext block (32 hex digits = 16 bytes)",
    value=st.session_state.get("blk", "00112233445566778899aabbccddeeff"),
)

try:
    block = bytes.fromhex(block_hex.replace(" ", ""))
    assert len(block) == 16
except Exception:
    theme.banner("warn", "Enter exactly 32 hex digits (16 bytes).")
    st.stop()

@st.cache_resource(show_spinner=False)
def schedule(passphrase: str):
    """PBKDF2 costs 200k iterations — cache so typing in other fields is instant."""
    return expand(derive_subkeys(root_key_from_passphrase(passphrase, b"\x00" * 16))[0])


rk = schedule(pw)

# -- run the network, capturing every intermediate state --------------------
states = []
left, right = block[:8], block[8:]
states.append((left, right, None, None))
for i in range(ROUNDS):
    f = F(right, rk.keys[i], rk.rots[i], rk.sbox)
    new_left, new_right = right, bytes(a ^ b for a, b in zip(left, f))
    states.append((new_left, new_right, rk.keys[i], rk.rots[i]))
    left, right = new_left, new_right

st.divider()
st.markdown("#### Round-by-round")


def row(label, l_bytes, r_bytes, key, rot, is_input):
    """One round.

    L is always a verbatim copy of the previous round's R (the Feistel
    guarantee) -> render it 'copied'. R is the only half actually computed
    this round -> render it 'computed'. Exactly one half glows.
    """

    def cells(data, kind):
        return "".join(f'<td class="{kind}">{b:02X}</td>' for b in data)

    keytxt = f"{key.hex().upper()}  ↺{rot}" if key else "—"
    lk = "" if is_input else "copied"
    rk_ = "" if is_input else "computed"
    return (
        f'<tr><td style="background:none;color:{theme.MUTED};text-align:right">{label}</td>'
        + cells(l_bytes, lk)
        + f'<td style="background:none;color:{theme.LINE}">│</td>'
        + cells(r_bytes, rk_)
        + f'<td style="background:none;color:{theme.MUTED};font-size:11px">{keytxt}</td></tr>'
    )


st.markdown(
    '<div class="legend">'
    '<span><span class="sw computed"></span>computed this round — R = L<sub>prev</sub> ⊕ F(R<sub>prev</sub>, K)</span>'
    '<span><span class="sw copied"></span>copied verbatim — L = R<sub>prev</sub></span>'
    "</div>",
    unsafe_allow_html=True,
)

html = ['<table class="state"><tr>'
        f'<td style="background:none;color:{theme.MUTED}">round</td>'
        f'<td colspan="8" style="background:none;color:{theme.MUTED}">L (left half)</td>'
        '<td style="background:none"></td>'
        f'<td colspan="8" style="background:none;color:{theme.MUTED}">R (right half)</td>'
        f'<td style="background:none;color:{theme.MUTED}">round key ↺rot</td></tr>']
for i, (l, r, k, rot) in enumerate(states):
    html.append(row("in" if i == 0 else str(i), l, r, k, rot, is_input=(i == 0)))
html.append("</table>")
st.markdown("".join(html), unsafe_allow_html=True)

st.markdown(
    f'<div class="lead" style="margin-top:6px;font-size:13px">Read down the dashed column: '
    f'every <b>L</b> is the previous round\'s <b>R</b>, unchanged. That is the Feistel '
    f"guarantee — and it is why decryption works no matter what F does.</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="lead" style="margin-top:8px">Ciphertext block = '
    f'<b style="color:{theme.TRAIL}">{(states[-1][1] + states[-1][0]).hex().upper()}</b> '
    "&nbsp;(final swap: R ‖ L)</div>",
    unsafe_allow_html=True,
)

st.divider()
st.markdown("#### Cumulative diffusion")
st.markdown(
    '<div class="lead">Bits differing from the original block after each round — '
    "how one block spreads across the whole 128-bit space.</div>",
    unsafe_allow_html=True,
)

import plotly.graph_objects as go  # noqa: E402

orig = block
pcts = []
for l, r, _, _ in states:
    cur = l + r
    diff = sum(bin(a ^ b).count("1") for a, b in zip(orig, cur))
    pcts.append(diff / 128 * 100)

fig = go.Figure(go.Scatter(
    x=list(range(len(pcts))), y=pcts, mode="lines+markers",
    line=dict(color=theme.TRAIL, width=3), marker=dict(size=7),
))
fig.add_hline(y=50, line=dict(color=theme.VERIFIED, dash="dash"),
              annotation_text="50% — ideal", annotation_position="top left",
              annotation_font_color=theme.VERIFIED)
fig.update_layout(height=320, xaxis_title="round", yaxis_title="% bits changed",
                  yaxis=dict(range=[0, 100]))
st.plotly_chart(theme.style_fig(fig), use_container_width=True)

st.divider()
with st.expander("The key-derived S-box for this passphrase", expanded=False):
    st.markdown(
        '<div class="lead">A 16×16 heatmap of the substitution table — each cell is '
        "coloured by its value. Change one character of the passphrase and essentially "
        "every cell changes, because the table is <b>grown from the key</b>, not perturbed.</div>",
        unsafe_allow_html=True,
    )

    def sbox_cell(v: int) -> str:
        alpha = 0.06 + 0.90 * (v / 255)
        txt = "#17233b" if v > 120 else theme.MUTED
        return (f'<td style="background:rgba(245,158,11,{alpha:.2f});'
                f'color:{txt}">{v:02X}</td>')

    hm_col, surf_col = st.columns([1, 1])
    with hm_col:
        grid = ['<table class="state">']
        for r_ in range(16):
            grid.append("<tr>" + "".join(sbox_cell(rk.sbox[r_ * 16 + c_]) for c_ in range(16)) + "</tr>")
        grid.append("</table>")
        st.markdown("".join(grid), unsafe_allow_html=True)
        st.caption("dark = low values, bright amber = high — a different passphrase redraws the whole picture")
    with surf_col:
        z = [[rk.sbox[r_ * 16 + c_] for c_ in range(16)] for r_ in range(16)]
        axis3d = dict(
            backgroundcolor="rgba(0,0,0,0)", gridcolor=theme.LINE,
            zerolinecolor=theme.LINE, color=theme.MUTED, showspikes=False,
        )
        fig3d = go.Figure(go.Surface(
            z=z, showscale=False,
            colorscale=[[0.0, "#111A2E"], [0.55, "#B45309"], [1.0, "#FDE68A"]],
            contours=dict(z=dict(show=True, usecolormap=True, width=2,
                                 highlightcolor=theme.TRAIL_SOFT)),
        ))
        fig3d.update_layout(
            height=380, margin=dict(l=0, r=0, t=6, b=36),
            paper_bgcolor="rgba(0,0,0,0)",
            scene=dict(
                xaxis={**axis3d, "title": "column"},
                yaxis={**axis3d, "title": "row"},
                zaxis={**axis3d, "title": "value"},
                camera=dict(eye=dict(x=1.6, y=-1.6, z=0.9)),
            ),
            font=dict(color=theme.MUTED, size=10),
        )
        st.plotly_chart(fig3d, use_container_width=True)
        st.caption("the same table as a 3D landscape — drag to rotate; the jagged terrain IS the chaos")
