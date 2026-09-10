"""Design system. "A laboratory instrument, not a toy."

Palette semantics are RESERVED. Red appears exactly once in the whole demo:
when integrity fails. That is why it means something when it does.

    slate  #0B1220 / #111A2E   surfaces
    green  #16A34A             verified / correct decryption
    amber  #F59E0B             the chaotic keystream (the trail, energy)
    red    #DC2626             wrong key / tamper / INSECURE mode ONLY
"""

from __future__ import annotations

import streamlit as st

SLATE = "#0B1220"
RAISED = "#111A2E"
INK = "#F8FAFC"
MUTED = "#94A3B8"
VERIFIED = "#16A34A"
TRAIL = "#F59E0B"
TRAIL_SOFT = "#FDE68A"
TAMPER = "#DC2626"
LINE = "#1E2C48"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=INK, family="Inter, Segoe UI, sans-serif", size=13),
    xaxis=dict(gridcolor=LINE, zerolinecolor=LINE),
    yaxis=dict(gridcolor=LINE, zerolinecolor=LINE),
    margin=dict(l=48, r=24, t=48, b=44),
)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}

/* Depth: a faint cone of light from the top-left, fixed while scrolling. */
.stApp {{
    background:
        radial-gradient(1100px 520px at 18% -12%, #142442 0%, rgba(20,36,66,0) 60%),
        radial-gradient(900px 500px at 95% 8%, rgba(245,158,11,.05) 0%, rgba(245,158,11,0) 55%),
        {SLATE};
    background-attachment: fixed;
}}

/* Display serif for headers — the "documentary title card" feel. */
h1, h2 {{ font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -.01em; }}
h1 {{
    background: linear-gradient(92deg, {INK} 55%, {TRAIL_SOFT} 130%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* Tabular numerals everywhere data lives. */
code, pre, .tnum, [data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums;
    font-family: 'Consolas', ui-monospace, monospace;
}}

section[data-testid="stSidebar"] {{
    background: {RAISED};
    border-right: 1px solid {LINE};
}}

/* Motion rule: 200-300ms ease-out, no bounce. */
.stButton>button, .card {{ transition: all 240ms cubic-bezier(.22,1,.36,1); }}

.stButton>button {{
    background: linear-gradient(180deg, {TRAIL_SOFT} -40%, {TRAIL} 45%);
    color: #17233b; border: 0; font-weight: 700; border-radius: 10px;
    box-shadow: 0 6px 18px rgba(245,158,11,.22), inset 0 1px 0 rgba(255,255,255,.25);
}}
.stButton>button:hover {{
    background: {TRAIL_SOFT}; color: #17233b;
    box-shadow: 0 8px 24px rgba(245,158,11,.34), inset 0 1px 0 rgba(255,255,255,.3);
}}

/* Metric tiles — raised glass cards instead of bare numbers. */
[data-testid="stMetric"] {{
    background: linear-gradient(180deg, rgba(23,35,60,.85), rgba(13,21,38,.65));
    border: 1px solid {LINE}; border-radius: 12px;
    padding: 12px 14px 10px;
    box-shadow: 0 8px 22px rgba(0,0,0,.30), inset 0 1px 0 rgba(248,250,252,.04);
}}
[data-testid="stMetricLabel"] {{ color: {MUTED}; }}

.card {{
    background: {RAISED}; border: 1px solid {LINE}; border-radius: 14px;
    padding: 16px 18px; margin: 10px 0;
    box-shadow: 0 10px 26px rgba(0,0,0,.30);
}}
.kicker {{
    font-size: 11px; letter-spacing: .12em; text-transform: uppercase;
    color: {MUTED}; font-weight: 700; margin-bottom: 4px;
}}
.lead {{ color: {MUTED}; font-size: 15px; line-height: 1.6; }}

/* The three reserved states. */
.banner {{ border-radius: 12px; padding: 14px 18px; font-weight: 700; margin: 12px 0;
           display:flex; align-items:center; gap:10px; font-size: 15px; }}
.banner.ok   {{ background: rgba(22,163,74,.12);  border: 1px solid {VERIFIED}; color: #86efac;
                box-shadow: 0 6px 20px rgba(22,163,74,.10); }}
.banner.warn {{ background: rgba(245,158,11,.10); border: 1px solid {TRAIL};    color: {TRAIL_SOFT};
                box-shadow: 0 6px 20px rgba(245,158,11,.10); }}
.banner.fail {{ background: rgba(220,38,38,.14);  border: 1px solid {TAMPER};   color: #fca5a5;
                box-shadow: 0 6px 26px rgba(220,38,38,.22); }}

.hexblock {{
    font-family: Consolas, monospace; font-size: 13px; line-height: 1.9;
    letter-spacing: .5px; word-break: break-all; color: {TRAIL_SOFT};
    background: linear-gradient(180deg, #0A1322, #060d19);
    border: 1px solid {LINE}; border-radius: 10px; padding: 12px 14px;
    box-shadow: inset 0 2px 10px rgba(0,0,0,.45);
}}

/* Bit grid — avalanche heatmap and round visualiser. */
.bitgrid {{ display: grid; grid-template-columns: repeat(16, 1fr); gap: 3px; margin: 8px 0; }}
.bitgrid .b {{ aspect-ratio: 1; border-radius: 2px; background: #16233c; }}
.bitgrid .b.on {{ background: {TRAIL}; box-shadow: 0 0 6px rgba(245,158,11,.55); }}

table.state {{ border-collapse: separate; border-spacing: 4px; }}
table.state td {{
    background: #16233c; border-radius: 5px; padding: 5px 9px;
    font-family: Consolas, monospace; font-size: 13px; color: {INK}; text-align: center;
}}
/* Round visualiser semantics: amber = newly COMPUTED this round;
   outlined/dim = COPIED verbatim from the previous round's other half.
   Only one of the two halves ever glows, so the Feistel guarantee
   ("R becomes the next L, untouched") is visible at a glance. */
table.state td.computed {{ background: {TRAIL}; color: #17233b; font-weight: 700; }}
table.state td.copied {{
    background: transparent; border: 1px dashed {LINE}; color: {MUTED};
}}
.legend {{ display:flex; gap:18px; align-items:center; font-size:12px; color:{MUTED}; margin:6px 0 10px; }}
.legend .sw {{ display:inline-block; width:14px; height:14px; border-radius:3px; margin-right:6px; vertical-align:-3px; }}
.legend .sw.computed {{ background:{TRAIL}; }}
.legend .sw.copied {{ border:1px dashed {LINE}; background:transparent; }}

hr {{ border-color: {LINE}; }}
</style>
"""


def apply() -> None:
    """Inject the design system. Call once at the top of every page."""
    st.markdown(CSS, unsafe_allow_html=True)


def banner(kind: str, text: str) -> None:
    """kind: 'ok' | 'warn' | 'fail'. Red is reserved for integrity failure."""
    icon = {"ok": "✓", "warn": "▲", "fail": "✕"}[kind]
    st.markdown(f'<div class="banner {kind}">{icon} {text}</div>', unsafe_allow_html=True)


def card(title: str, body: str = "") -> None:
    st.markdown(
        f'<div class="card"><div class="kicker">{title}</div>'
        f'<div class="lead">{body}</div></div>',
        unsafe_allow_html=True,
    )


def hexblock(data: bytes, limit: int = 512) -> None:
    shown = data[:limit]
    text = " ".join(f"{b:02X}" for b in shown)
    if len(data) > limit:
        text += f"  … (+{len(data) - limit} bytes)"
    st.markdown(f'<div class="hexblock">{text}</div>', unsafe_allow_html=True)


def bitgrid(bits, ncols: int = 16) -> None:
    """Render a list of 0/1 as a glowing grid."""
    cells = "".join(f'<div class="b{" on" if b else ""}"></div>' for b in bits)
    st.markdown(
        f'<div class="bitgrid" style="grid-template-columns:repeat({ncols},1fr)">{cells}</div>',
        unsafe_allow_html=True,
    )


def style_fig(fig):
    """Apply the dark plot theme to a Plotly figure."""
    fig.update_layout(**PLOT_LAYOUT)
    return fig
