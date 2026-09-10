#!/usr/bin/env python3
"""Generate the six Bifurcate flowcharts as SVG.

Every figure is drawn from code so the geometry is exact, the palette matches
the app, and the whole set can be regenerated if the spec changes.

    python docs/flowcharts/build_flowcharts.py

Outputs (into this directory):
    fig1_master.svg        the system, end to end
    fig2_chaos.svg         the chaotic engine + sponge
    fig3_sbox.svg          key-derived S-box generation
    fig4_encrypt.svg       the Feistel network (encryption)
    fig5_decrypt.svg       the Feistel network (decryption)
    fig6_roundf.svg        the round function F

Design system — light variant for print:
    slate ink on white, amber = the chaotic keystream/trail,
    green = verified/output, red = RESERVED for integrity failure.
"""

from __future__ import annotations

import pathlib

OUT = pathlib.Path(__file__).parent

# ---------------------------------------------------------------- palette --
INK = "#0B1220"
SLATE = "#334155"
MUTED = "#64748B"
LINE = "#CBD5E1"
TRAIL = "#F59E0B"       # the chaotic keystream
TRAIL_BG = "#FEF3C7"
VERIFIED = "#16A34A"    # correct / output
VERIFIED_BG = "#DCFCE7"
TAMPER = "#DC2626"      # RESERVED — integrity failure only
BLUE = "#1E5FD0"
BLUE_BG = "#DBEAFE"
PURPLE = "#7C3AED"
PURPLE_BG = "#EDE9FE"
WHITE = "#FFFFFF"
PAPER = "#FDFDFF"

FONT = "Inter, 'Segoe UI', Calibri, sans-serif"
MONO = "Consolas, 'SF Mono', monospace"
SERIF = "Fraunces, Georgia, serif"


# ------------------------------------------------------------------ canvas --
class SVG:
    """Tiny SVG builder — no dependencies, exact coordinates."""

    def __init__(self, w: int, h: int, title: str, subtitle: str = ""):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.title = title
        self.subtitle = subtitle

    # -- primitives ---------------------------------------------------------
    def rect(self, x, y, w, h, fill=WHITE, stroke=LINE, rx=8, sw=1.6, dash=None,
             shadow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        f_ = ' filter="url(#ds)"' if shadow else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{f_}/>'
        )

    def text(self, x, y, s, size=13, fill=INK, anchor="middle", weight="400",
             font=FONT, style=""):
        st = f' font-style="{style}"' if style else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{st}>'
            f"{esc(s)}</text>"
        )

    def line(self, x1, y1, x2, y2, stroke=SLATE, sw=1.8, arrow=True, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#a)"' if arrow else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="round"{d}{m}/>'
        )

    def path(self, d, stroke=SLATE, sw=1.8, arrow=True, fill="none", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#a)"' if arrow else ""
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round"{da}{m}/>'
        )

    def circle(self, cx, cy, r, fill=WHITE, stroke=SLATE, sw=1.8):
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    # -- composites ---------------------------------------------------------
    def box(self, x, y, w, h, label, sub="", fill=WHITE, stroke=LINE,
            color=INK, size=13, rx=8, weight="600", mono=False):
        self.rect(x, y, w, h, fill, stroke, rx, shadow=True)
        cx = x + w / 2
        if sub:
            self.text(cx, y + h / 2 - 3, label, size, color, weight=weight,
                      font=MONO if mono else FONT)
            self.text(cx, y + h / 2 + 14, sub, size - 3, MUTED)
        else:
            self.text(cx, y + h / 2 + size / 3, label, size, color, weight=weight,
                      font=MONO if mono else FONT)

    def xor(self, cx, cy, r=15):
        """The XOR node — drawn as a real ⊕, not a glyph."""
        self.circle(cx, cy, r, WHITE, TAMPER, 2)
        self.line(cx - r * 0.62, cy, cx + r * 0.62, cy, TAMPER, 2, arrow=False)
        self.line(cx, cy - r * 0.62, cx, cy + r * 0.62, TAMPER, 2, arrow=False)

    def note(self, x, y, w, lines, accent=TRAIL, bg=TRAIL_BG, size=11.5):
        """A side annotation explaining the PURPOSE of a block."""
        h = 16 + len(lines) * 16
        self.rect(x, y, w, h, bg, accent, rx=7, sw=1.2, shadow=True)
        self.line(x, y + 7, x, y + h - 7, accent, 3, arrow=False)
        for i, ln in enumerate(lines):
            self.text(x + 11, y + 21 + i * 16, ln, size, SLATE, anchor="start")
        return h

    def caption(self, x, y, s, size=11.5, anchor="start", fill=MUTED):
        self.text(x, y, s, size, fill, anchor=anchor, style="italic")

    # -- render -------------------------------------------------------------
    def save(self, name: str):
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
            f'<defs><marker id="a" markerWidth="9" markerHeight="9" refX="7.5" '
            f'refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="{SLATE}"/>'
            f'</marker>'
            f'<marker id="ag" markerWidth="9" markerHeight="9" refX="7.5" refY="3" '
            f'orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="{VERIFIED}"/></marker>'
            f'<marker id="at" markerWidth="9" markerHeight="9" refX="7.5" refY="3" '
            f'orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="{TRAIL}"/></marker>'
            # soft drop shadow — gives every card gentle depth without noise
            f'<filter id="ds" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feDropShadow dx="0" dy="1.6" stdDeviation="2.6" '
            f'flood-color="{INK}" flood-opacity="0.13"/></filter>'
            # paper gradient — a hint of light falling from the top
            f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#FEFEFF"/>'
            f'<stop offset="1" stop-color="#F2F6FB"/></linearGradient>'
            f"</defs>"
            f'<rect width="{self.w}" height="{self.h}" fill="url(#bg)"/>'
        )
        # title block with an amber accent bar
        head += (
            f'<rect x="34" y="28" width="5" height="26" rx="2.5" fill="{TRAIL}"/>'
            f'<text x="50" y="44" font-family="{SERIF}" font-size="21" '
            f'fill="{INK}" font-weight="700">{esc(self.title)}</text>'
        )
        if self.subtitle:
            head += (
                f'<text x="50" y="66" font-family="{FONT}" font-size="12.5" '
                f'fill="{MUTED}">{esc(self.subtitle)}</text>'
            )
        head += (
            f'<line x1="34" y1="80" x2="{self.w-34}" y2="80" stroke="{LINE}" stroke-width="1.4"/>'
            f'<line x1="34" y1="80" x2="150" y2="80" stroke="{TRAIL}" stroke-width="2.4"/>'
        )
        body = "".join(self.parts)
        foot = (
            f'<text x="34" y="{self.h-16}" font-family="{FONT}" font-size="10.5" '
            f'fill="{MUTED}">Bifurcate — a chaos-seeded Feistel cipher</text></svg>'
        )
        (OUT / name).write_text(head + body + foot, encoding="utf-8")
        print(f"  wrote {name}  ({self.w}x{self.h})")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ============================================================ FIGURE 1 ======
def fig1_master():
    s = SVG(1180, 940, "Figure 1 — Bifurcate: the complete system",
            "Key derivation, the chaotic engine, the cipher, and the authenticated container.")

    # ---- lane A: key material (left column) ----
    s.text(34, 112, "KEY MATERIAL", 11, MUTED, anchor="start", weight="700")
    s.box(34, 124, 250, 52, "Passphrase", "human-chosen, low entropy", BLUE_BG, BLUE, BLUE)
    s.line(159, 176, 159, 200)
    s.box(34, 200, 250, 58, "PBKDF2-HMAC-SHA256", "200 000 iterations · 16-byte salt", WHITE, SLATE)
    s.line(159, 258, 159, 282)
    s.box(34, 282, 250, 50, "root_key  (256-bit)", "", TRAIL_BG, TRAIL, INK, mono=True)

    # alternative hybrid path
    s.box(320, 124, 236, 52, "RSA-2048 public key", "recipient's", PURPLE_BG, PURPLE, PURPLE)
    s.line(438, 176, 438, 200)
    s.box(320, 200, 236, 58, "OAEP-wrap random", "session key = root_key", WHITE, PURPLE)
    s.path(f"M 438 258 L 438 272 L 300 272 L 300 300 L 288 300", SLATE)
    s.caption(322, 292, "hybrid mode — no passphrase needed")

    # HKDF split
    s.line(159, 332, 159, 358)
    s.box(34, 358, 250, 52, "HKDF-SHA256", "domain-separated split", WHITE, SLATE)
    s.path("M 100 410 L 100 440", SLATE)
    s.path("M 220 410 L 220 440", SLATE)
    s.box(20, 440, 150, 48, "enc_seed", "→ the cipher", TRAIL_BG, TRAIL, INK, mono=True)
    s.box(186, 440, 150, 48, "mac_key", "→ the tag", VERIFIED_BG, VERIFIED, INK, mono=True)
    h = s.note(34, 506, 302, [
        "PURPOSE — key separation.",
        "Encryption and authentication never",
        "share key material, so breaking one",
        "cannot compromise the other.",
    ])

    # ---- lane B: the chaotic engine (middle) ----
    s.text(320, 112, "HYBRID KEY PATH", 11, MUTED, anchor="start", weight="700")
    s.text(400, 320, "THE CHAOTIC ENGINE", 11, MUTED, anchor="start", weight="700")
    s.path("M 170 464 L 400 464", TRAIL, 2.2)
    s.box(400, 330, 250, 54, "Integer logistic map", "X ← (R·X·(S−X)) ÷ (S·2²⁰)", WHITE, TRAIL)
    s.line(525, 384, 525, 408, TRAIL)
    s.box(400, 408, 250, 50, "SHA-256 whitening", "the sponge", WHITE, TRAIL)
    s.line(525, 458, 525, 482, TRAIL)
    s.box(400, 482, 250, 44, "keystream bytes", "", TRAIL_BG, TRAIL, INK, mono=True)
    s.path("M 460 526 L 460 556", TRAIL)
    s.path("M 590 526 L 590 556", TRAIL)
    s.box(374, 556, 168, 50, "Key-derived S-box", "Fisher–Yates, 256 B", TRAIL_BG, TRAIL, INK, size=12)
    s.box(556, 556, 176, 50, "12 round keys", "+ rotations 1–7", TRAIL_BG, TRAIL, INK, size=12)
    s.note(374, 622, 358, [
        "PURPOSE — the novelty. The substitution table and",
        "every round key are grown from YOUR key, so two",
        "passphrases are effectively two different ciphers.",
        "Integer arithmetic ⇒ bit-identical on every machine.",
    ])

    # ---- lane C: the data path (right) ----
    s.text(790, 112, "THE DATA PATH", 11, MUTED, anchor="start", weight="700")
    s.box(790, 124, 250, 50, "Plaintext", "any length", BLUE_BG, BLUE, BLUE)
    s.line(915, 174, 915, 198)
    s.box(790, 198, 250, 50, "PKCS#7 padding", "→ multiple of 16 B", WHITE, SLATE)
    s.line(915, 248, 915, 272)
    s.box(790, 272, 250, 54, "CBC chaining", "C₀ = random IV", WHITE, SLATE)
    s.line(915, 326, 915, 350)
    s.box(790, 350, 250, 62, "12 Feistel rounds", "see Figure 4", VERIFIED_BG, VERIFIED, INK)
    s.path("M 732 590 L 768 590 L 768 381 L 788 381", TRAIL, 2, dash="6 4")
    s.text(762, 452, "round keys", 10.5, TRAIL, anchor="end", weight="600")
    s.line(915, 412, 915, 436)
    s.box(790, 436, 250, 46, "Ciphertext", "", WHITE, SLATE, mono=True)
    s.line(915, 482, 915, 506)
    s.box(790, 506, 250, 56, "HMAC-SHA256", "over the WHOLE container", VERIFIED_BG, VERIFIED, INK)
    s.path("M 336 464 L 360 464 L 360 700 L 700 700 L 700 534 L 788 534", VERIFIED, 2, dash="6 4")
    s.caption(704, 692, "mac_key", fill=VERIFIED)
    s.line(915, 562, 915, 586)
    s.box(790, 586, 250, 54, ".bfc container", "self-describing", VERIFIED_BG, VERIFIED, INK)

    s.note(790, 656, 356, [
        "PURPOSE — encrypt-then-MAC. The tag covers every",
        "header byte too, so the mode and hybrid flags cannot",
        "be downgraded undetected. Verified BEFORE decryption.",
    ], accent=VERIFIED, bg=VERIFIED_BG)

    # container strip
    s.text(34, 790, "CONTAINER LAYOUT", 11, MUTED, anchor="start", weight="700")
    fields = [("magic", 74), ("ver", 42), ("flags", 52), ("salt (16)", 108),
              ("IV (16)", 100), ("len", 44), ("wrapped key", 150),
              ("ciphertext", 300), ("HMAC tag (32)", 190)]
    x = 34
    for name, w in fields:
        fill = VERIFIED_BG if "HMAC" in name else (TRAIL_BG if "wrapped" in name else WHITE)
        stroke = VERIFIED if "HMAC" in name else (TRAIL if "wrapped" in name else LINE)
        s.rect(x, 804, w, 40, fill, stroke, rx=5)
        s.text(x + w / 2, 828, name, 11, SLATE, weight="600")
        x += w + 3
    s.path(f"M 34 856 L {x-3} 856", VERIFIED, 1.6, arrow=False, dash="5 4")
    s.text(34, 876, "└─ authenticated by the tag: every byte above ─┘", 11, VERIFIED, anchor="start", weight="600")
    s.save("fig1_master.svg")


# ============================================================ FIGURE 2 ======
def fig2_chaos():
    s = SVG(1080, 720, "Figure 2 — The chaotic engine",
            "Why the map is integer, and why its output is whitened before use.")

    s.box(60, 112, 260, 50, "enc_seed  (32 B)", "from HKDF", TRAIL_BG, TRAIL, INK, mono=True)
    s.line(190, 162, 190, 190)
    s.box(60, 190, 260, 56, "Seed the state", "X₀ = int(seed[:4]) mod (S−2) + 1", WHITE, SLATE, size=12)
    s.line(190, 246, 190, 276)

    # the map
    s.rect(60, 276, 260, 92, WHITE, TRAIL, rx=10, sw=2)
    s.text(190, 302, "Integer logistic map", 13.5, INK, weight="700")
    s.text(190, 328, "X ← (R · X · (S − X)) ÷ (S · 2²⁰)", 13, TRAIL, font=MONO, weight="600")
    s.text(190, 350, "S = 2³²   R = round(3.99 × 2²⁰)", 11, MUTED, font=MONO)

    # feedback loop
    s.path("M 60 322 L 32 322 L 32 400 L 190 400 L 190 372", TRAIL, 1.8)
    s.caption(38, 416, "iterate ×8 between squeezes", fill=TRAIL)

    # degeneracy guard — title at the top of the box, not centred (avoids overlap)
    s.rect(372, 276, 250, 92, WHITE, TAMPER, rx=8, sw=1.8)
    s.text(497, 302, "Degeneracy guard", 13, INK, weight="700")
    s.text(497, 326, "if X = 0 or X unchanged →", 11, SLATE)
    s.text(497, 346, "re-inject SHA-256(ctr ‖ seed)", 10.5, TAMPER, font=MONO)
    s.line(320, 322, 370, 322, TAMPER)

    s.line(190, 400, 190, 432, TRAIL) if False else None
    s.path("M 190 400 L 190 428", TRAIL)
    s.box(60, 428, 260, 66, "SHA-256 sponge", "block = H(X ‖ ctr ‖ enc_seed)", WHITE, TRAIL)
    s.line(190, 494, 190, 522, TRAIL)
    s.box(60, 522, 260, 48, "keystream bytes", "", TRAIL_BG, TRAIL, INK, mono=True)

    s.note(372, 400, 420, [
        "PURPOSE — determinism. A float logistic map is NOT",
        "bit-identical across platforms or Python builds. One",
        "differing bit makes decryption fail irrecoverably.",
        "Python ints are arbitrary-precision, so fixed-point",
        "integer arithmetic reproduces exactly, everywhere.",
    ])

    s.note(372, 528, 420, [
        "PURPOSE — whitening. Security must NOT rest on the",
        "statistics of a discretised map: the literature",
        "(Alvarez & Li, 2006) shows naive chaos ciphers are",
        "frequently broken. Chaos supplies key-dependent",
        "STRUCTURE; SHA-256 supplies statistical QUALITY.",
    ], accent=VERIFIED, bg=VERIFIED_BG)

    s.caption(60, 646, "Floating-point orbits are used only to DRAW the bifurcation diagram — never to key the cipher.")
    s.save("fig2_chaos.svg")


# ============================================================ FIGURE 3 ======
def fig3_sbox():
    s = SVG(1020, 656, "Figure 3 — Key-derived S-box generation",
            "Fisher–Yates shuffle driven by the chaotic keystream.")

    s.box(60, 112, 240, 48, "sbox = [0, 1, 2, … 255]", "identity", WHITE, SLATE, mono=True, size=12)
    s.line(180, 160, 180, 188)
    s.box(60, 188, 240, 46, "i ← 255", "loop counter", WHITE, SLATE, size=12)
    s.line(180, 234, 180, 262)

    s.rect(60, 262, 240, 96, TRAIL_BG, TRAIL, rx=10, sw=2)
    s.text(180, 288, "j ← keystream_byte() mod (i+1)", 12, INK, font=MONO, weight="600")
    s.line(80, 302, 280, 302, TRAIL, 1.2, arrow=False)
    s.text(180, 326, "swap( sbox[i], sbox[j] )", 12.5, TRAIL, font=MONO, weight="700")
    s.text(180, 346, "i ← i − 1", 11.5, MUTED, font=MONO)

    # loop back
    s.path("M 60 310 L 30 310 L 30 210 L 58 210", TRAIL, 1.8)
    s.caption(24, 178, "while i > 0", fill=TRAIL)

    s.line(180, 358, 180, 388)
    s.box(60, 388, 240, 50, "256-byte S-box", "a bijection, by construction", VERIFIED_BG, VERIFIED, INK)

    s.note(356, 200, 430, [
        "PURPOSE — the novelty of Bifurcate.",
        "Classical ciphers ship ONE fixed substitution table",
        "for every user on earth. Here the table is grown from",
        "the key: change one passphrase character and ~99.6%",
        "of entries change (measured: 99.61%, matching the",
        "theoretical 255/256 for independent permutations).",
    ])

    s.note(356, 340, 430, [
        "NO INVERSE TABLE IS EVER NEEDED.",
        "In a Feistel network the round function F is never",
        "inverted (Figure 5), so an un-invertible chaotic",
        "S-box is safe here — removing an entire class of bug.",
    ], accent=VERIFIED, bg=VERIFIED_BG)

    # a strip of the actual box
    s.text(60, 486, "EXAMPLE — first 16 entries for two passphrases differing by one character", 11, MUTED, anchor="start", weight="700")
    a = [0x6E, 0x1B, 0xC4, 0x7A, 0x03, 0xF1, 0x59, 0x8D, 0x22, 0xB0, 0x4E, 0xD7, 0x95, 0x30, 0xAC, 0x6B]
    b = [0xD2, 0x84, 0x1F, 0x60, 0xBB, 0x0A, 0xE7, 0x35, 0x9C, 0x48, 0xF3, 0x21, 0x7D, 0xCE, 0x56, 0x08]
    for row, (vals, lbl, col) in enumerate([(a, "key A", TRAIL), (b, "key B", PURPLE)]):
        y = 500 + row * 44
        s.text(66, y + 25, lbl, 11, col, anchor="start", weight="700")
        for i, v in enumerate(vals):
            x = 122 + i * 50
            s.rect(x, y, 44, 32, WHITE, col, rx=5, sw=1.3)
            s.text(x + 22, y + 21, f"{v:02X}", 12, INK, font=MONO, weight="600")
    s.caption(122, 596, "every position differs — the table is not perturbed, it is regenerated")
    s.save("fig3_sbox.svg")


# ======================================================== FIGURES 4 & 5 =====
def feistel(reverse: bool):
    """Encryption and decryption share one drawing routine — because they ARE
    the same algorithm. That is the point the figure must make."""
    title = ("Figure 5 — Feistel network: DECRYPTION" if reverse
             else "Figure 4 — Feistel network: ENCRYPTION")
    sub = ("Identical structure. Only the round-key order is reversed."
           if reverse else "12 rounds. The right half is transformed; the left half is copied.")
    s = SVG(920, 1130, title, sub)

    cx_l, cx_r = 250, 590
    top = 112
    s.box(cx_l - 105, top, 210, 46,
          "R₁₂ (ciphertext)" if reverse else "L₀ (plaintext)", "",
          BLUE_BG if not reverse else VERIFIED_BG, BLUE if not reverse else VERIFIED, INK, mono=True)
    s.box(cx_r - 105, top, 210, 46,
          "L₁₂" if reverse else "R₀", "",
          BLUE_BG if not reverse else VERIFIED_BG, BLUE if not reverse else VERIFIED, INK, mono=True)

    y = top + 46
    shown = [0, 1, 2]
    # Decryption consumes the 12 round keys in reverse (K₁₂ first) and retraces
    # the encryption states backwards: after round 1 the halves are (R₁₁, L₁₁).
    labels = ([("round 1", "K₁₂"), ("round 2", "K₁₁"), ("round 3", "K₁₀")] if reverse
              else [("round 1", "K₁"), ("round 2", "K₂"), ("round 3", "K₃")])
    halves = ([("R₁₁", "L₁₁"), ("R₁₀", "L₁₀"), ("R₉", "L₉")] if reverse
              else [("L₁", "R₁"), ("L₂", "R₂"), ("L₃", "R₃")])
    for idx, i in enumerate(shown):
        ry = y + idx * 190
        name, key = labels[idx]
        # F box
        s.rect(cx_r - 78, ry + 44, 156, 52, TRAIL_BG, TRAIL, rx=9, sw=1.8)
        s.text(cx_r, ry + 70, "F", 17, TRAIL, weight="700", font=SERIF)
        s.text(cx_r, ry + 86, "see Figure 6", 10, MUTED)
        # key in
        s.text(cx_r + 132, ry + 74, key, 13, PURPLE, font=MONO, weight="700")
        s.line(cx_r + 108, ry + 70, cx_r + 82, ry + 70, PURPLE)
        # right rail down into F
        s.line(cx_r, ry, cx_r, ry + 42, SLATE)
        # F out to XOR on the left rail
        s.path(f"M {cx_r-80} {ry+70} L {cx_l+34} {ry+70}", TRAIL)
        s.xor(cx_l, ry + 70)
        # left rail into XOR
        s.line(cx_l, ry, cx_l, ry + 53, SLATE)
        # the crossover
        s.path(f"M {cx_l} {ry+87} L {cx_l} {ry+126} L {cx_r} {ry+126} L {cx_r} {ry+152}", SLATE)
        s.path(f"M {cx_r} {ry+42} L {cx_r+150} {ry+42} L {cx_r+150} {ry+118} L {cx_l-150} {ry+118} L {cx_l-150} {ry+152} L {cx_l} {ry+152}",
               VERIFIED, 1.7, dash="6 4")
        copied_note = ("right half copied to the next left, untouched" if reverse
                       else "R becomes the next L, untouched")
        s.text(cx_l - 148, ry + 108, copied_note, 10.5, VERIFIED, anchor="start", weight="600")
        s.text(60, ry + 74, name, 12, MUTED, anchor="start", weight="700")
        # the halves after this round
        ly = ry + 152
        left_lbl, right_lbl = halves[idx]
        s.box(cx_l - 105, ly, 210, 40, left_lbl, "", WHITE, LINE, INK, mono=True, size=12)
        s.box(cx_r - 105, ly, 210, 40, right_lbl, "", TRAIL_BG, TRAIL, INK, mono=True, size=12)

    yd = y + 3 * 190
    s.text(cx_l, yd + 26, "⋮", 22, MUTED)
    s.text(cx_r, yd + 26, "⋮", 22, MUTED)
    s.text(60, yd + 26, "rounds 4–12", 12, MUTED, anchor="start", weight="700")

    yf = yd + 50
    s.box(cx_l - 105, yf, 210, 42, "R₀" if reverse else "L₁₂", "", WHITE, LINE, INK, mono=True, size=12)
    s.box(cx_r - 105, yf, 210, 42, "L₀" if reverse else "R₁₂", "", TRAIL_BG, TRAIL, INK, mono=True, size=12)
    # final swap
    s.path(f"M {cx_l} {yf+42} L {cx_l} {yf+64} L {cx_r} {yf+64} L {cx_r} {yf+86}", SLATE)
    s.path(f"M {cx_r} {yf+42} L {cx_r} {yf+56} L {cx_l} {yf+56} L {cx_l} {yf+86}", SLATE)
    s.text((cx_l + cx_r) / 2, yf + 78, "final swap", 11, MUTED, weight="600")
    out_fill = BLUE_BG if reverse else VERIFIED_BG
    out_stroke = BLUE if reverse else VERIFIED
    s.box(cx_l - 105, yf + 86, 210, 46,
          "L₀ (plaintext)" if reverse else "R₁₂", "", out_fill, out_stroke, INK, mono=True)
    s.box(cx_r - 105, yf + 86, 210, 46,
          "R₀" if reverse else "L₁₂ (ciphertext)", "", out_fill, out_stroke, INK, mono=True)

    # the formulas
    fy = yf + 160
    s.rect(60, fy, 800, 74, WHITE, SLATE, rx=9)
    if reverse:
        s.text(80, fy + 30, "Rᵢ = Lᵢ₊₁", 15, INK, anchor="start", font=MONO, weight="700")
        s.text(80, fy + 56, "Lᵢ = Rᵢ₊₁ ⊕ F(Lᵢ₊₁, Kᵢ₊₁)      i = 11, 10, … 0", 15, INK, anchor="start", font=MONO, weight="700")
    else:
        s.text(80, fy + 30, "Lᵢ₊₁ = Rᵢ", 15, INK, anchor="start", font=MONO, weight="700")
        s.text(80, fy + 56, "Rᵢ₊₁ = Lᵢ ⊕ F(Rᵢ, Kᵢ₊₁)          i = 0, 1, … 11", 15, INK, anchor="start", font=MONO, weight="700")

    msg = ("PURPOSE — decryption is the SAME function as encryption. Only the key order flips. "
           "This holds no matter what F does." if reverse else
           "PURPOSE — F is never inverted. Whatever F does, the structure still inverts, "
           "so a chaotic S-box needs no inverse table.")
    s.note(60, fy + 88, 800, [msg], accent=VERIFIED, bg=VERIFIED_BG, size=12)
    s.save("fig5_decrypt.svg" if reverse else "fig4_encrypt.svg")


# ============================================================ FIGURE 6 ======
def fig6_roundf():
    s = SVG(1080, 760, "Figure 6 — The round function F",
            "Confusion and diffusion, one step at a time (Shannon, 1949).")

    cx = 300
    s.box(cx - 120, 112, 240, 46, "Rᵢ₋₁  (64 bits)", "", BLUE_BG, BLUE, INK, mono=True)
    y = 158

    steps = [
        ("1.  XOR round key Kᵢ", "key mixing", "confusion", PURPLE, PURPLE_BG),
        ("2.  S-box substitution", "8 bytes → 8 bytes", "CONFUSION", TRAIL, TRAIL_BG),
        ("3.  Rotate left rot ᵢ bits", "1–7, key-dependent", "DIFFUSION", VERIFIED, VERIFIED_BG),
        ("4.  Byte permutation", "PERM = 5 2 6 7 1 3 0 4", "DIFFUSION", VERIFIED, VERIFIED_BG),
    ]
    for i, (label, sub, tag, col, bg) in enumerate(steps):
        by = y + 22 + i * 104
        s.line(cx, by - 22, cx, by - 2)
        s.rect(cx - 150, by, 300, 66, bg, col, rx=9, sw=1.8)
        s.text(cx, by + 27, label, 13.5, INK, weight="700")
        s.text(cx, by + 47, sub, 11.5, MUTED, font=MONO)
        s.rect(cx + 160, by + 18, 118, 30, WHITE, col, rx=15, sw=1.5)
        s.text(cx + 219, by + 38, tag, 11, col, weight="700")

    last = y + 22 + 3 * 104 + 66
    s.line(cx, last, cx, last + 22)
    s.box(cx - 120, last + 22, 240, 46, "F(Rᵢ₋₁, Kᵢ)", "", TRAIL_BG, TRAIL, INK, mono=True)

    # annotations
    s.note(620, 176, 420, [
        "STEP 2 — CONFUSION.",
        "Substitution obscures the relationship between",
        "key, plaintext and ciphertext, and destroys",
        "statistical patterns. The table is key-derived,",
        "so the confusion itself depends on your key.",
    ])
    s.note(620, 300, 420, [
        "STEP 3 — the rotation floor.",
        "rot ∈ 1…7, never 0. A zero rotation would leave",
        "the round's diffusion resting on the byte",
        "permutation alone; the floor guarantees every",
        "round mixes ACROSS byte boundaries.",
    ], accent=VERIFIED, bg=VERIFIED_BG)
    s.note(620, 424, 420, [
        "STEP 4 — a single 8-cycle derangement.",
        "0→5→3→7→4→1→2→6→0. No byte stays in its lane,",
        "and one cycle links all eight positions, so",
        "repeated rounds carry every byte to every",
        "position. Asserted in the test suite.",
    ], accent=VERIFIED, bg=VERIFIED_BG)

    # the permutation, drawn
    s.text(620, 580, "THE BYTE PERMUTATION", 11, MUTED, anchor="start", weight="700")
    for i in range(8):
        x = 620 + i * 52
        s.rect(x, 592, 44, 30, WHITE, LINE, rx=5)
        s.text(x + 22, 613, str(i), 12, MUTED, font=MONO)
        s.rect(x, 682, 44, 30, WHITE, VERIFIED, rx=5)
        s.text(x + 22, 703, str(i), 12, INK, font=MONO, weight="600")
    PERM = (5, 2, 6, 7, 1, 3, 0, 4)
    for i, d in enumerate(PERM):
        x1 = 620 + i * 52 + 22
        x2 = 620 + d * 52 + 22
        s.path(f"M {x1} 624 C {x1} 654, {x2} 650, {x2} 680", VERIFIED, 1.5)
    s.caption(620, 736, "position i moves to position PERM[i] — a derangement with a single 8-cycle")
    s.save("fig6_roundf.svg")


if __name__ == "__main__":
    print("Generating Bifurcate flowcharts…")
    fig1_master()
    fig2_chaos()
    fig3_sbox()
    feistel(reverse=False)
    feistel(reverse=True)
    fig6_roundf()
    print(f"\nAll six figures written to {OUT}")
