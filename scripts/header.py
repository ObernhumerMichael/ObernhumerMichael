"""Build assets/header-{light,dark}.svg in the Ledger style (the blog's design system).

Fonts are instanced to one weight, subset to the glyphs used, and embedded
as woff2 data URIs, because GitHub renders README SVGs as <img>, which
never loads external resources.

Usage (from this repo, with the blog checked out next to it):

  nix shell --impure --expr 'with import <nixpkgs> {}; python3.withPackages (ps: [ps.fonttools ps.brotli])' \
    -c python3 scripts/header.py ../blog/public/fonts assets
"""
import base64, io, math, sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

FONTS = sys.argv[1]
OUT = sys.argv[2]

W, H = 900, 316
PAD = 48

NAME = "Michael Obernhumer"
ROLE = "backend · infrastructure"
LINE1 = [("I build backend systems and write down", False)]
LINE2 = [("what actually happens", True), (" while building them.", False)]
META_L = "Spring Boot · Laravel · Ansible · NixOS"
META_R = "obernhumer.com ↗"


def oklch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    def enc(x):
        x = min(max(x, 0), 1)
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)
    return "#%02x%02x%02x" % tuple(enc(x) for x in rgb)


# DESIGN_SYSTEM.md §2 — light "paper" and dark "ink".
THEMES = {
    "light": dict(
        bg=oklch(0.982, 0.006, 75), text=oklch(0.26, 0.012, 75),
        text2=oklch(0.40, 0.012, 75), muted=oklch(0.58, 0.012, 75),
        rule=oklch(0.90, 0.008, 75), frame=oklch(0.82, 0.008, 75),
        accent=oklch(0.55, 0.14, 40),
    ),
    "dark": dict(
        bg=oklch(0.185, 0.008, 75), text=oklch(0.90, 0.008, 75),
        text2=oklch(0.72, 0.012, 75), muted=oklch(0.60, 0.012, 75),
        rule=oklch(0.30, 0.008, 75), frame=oklch(0.30, 0.008, 75),
        accent=oklch(0.72, 0.120, 45),
    ),
}


def load(file, axes, text):
    f = TTFont(f"{FONTS}/{file}")
    f = instantiateVariableFont(f, axes)
    # Unsubset copy of the instance, for measuring advance widths.
    buf = io.BytesIO(); f.save(buf); buf.seek(0); measure = TTFont(buf)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []; opts.notdef_outline = True
    s = subset.Subsetter(opts); s.populate(text=text); s.subset(f)
    out = io.BytesIO(); f.flavor = "woff2"; f.save(out)
    return base64.b64encode(out.getvalue()).decode(), measure


def width(font, text, size):
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / upm


serif_text = "".join(t for t, it in LINE1 + LINE2 if not it)
serif_it_text = "".join(t for t, it in LINE1 + LINE2 if it)
serif, serif_m = load("source-serif-roman.woff2", {"wght": 400, "opsz": 48}, serif_text)
serif_it, serif_it_m = load("source-serif-italic.woff2", {"wght": 400, "opsz": 48}, serif_it_text)
sans, _ = load("plex-sans-roman.woff2", {"wght": 600, "wdth": 100}, NAME)
mono, mono_m = load("plex-mono-roman.woff2", {"wght": 400}, ROLE + META_L + META_R)


def line_width(runs, size):
    return sum(width(serif_it_m if it else serif_m, t, size) for t, it in runs)


# Largest statement size that fits the frame, capped at 46.
avail = W - 2 * PAD
size = min(46, math.floor(avail / max(line_width(LINE1, 1), line_width(LINE2, 1))))

name_y = 66
rule1_y = 98
st1_y = rule1_y + 30 + size
st2_y = st1_y + round(size * 1.2)
rule2_y = st2_y + 40
meta_y = rule2_y + 42
H = meta_y + 42

link_w = width(mono_m, META_R, 15)


def spans(runs):
    return "".join(
        f'<tspan class="{"si" if it else "s"}">{t.replace("&", "&amp;")}</tspan>' for t, it in runs
    )


def svg(t):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Michael Obernhumer — backend · infrastructure. I build backend systems and write down what actually happens while building them.</title>
<style>
@font-face{{font-family:S;src:url(data:font/woff2;base64,{serif}) format("woff2")}}
@font-face{{font-family:SI;src:url(data:font/woff2;base64,{serif_it}) format("woff2")}}
@font-face{{font-family:P;src:url(data:font/woff2;base64,{sans}) format("woff2")}}
@font-face{{font-family:M;src:url(data:font/woff2;base64,{mono}) format("woff2")}}
.s{{font-family:S,Georgia,serif}}
.si{{font-family:SI,Georgia,serif;font-style:italic}}
.n{{font:600 24px P,Helvetica,Arial,sans-serif;letter-spacing:-0.01em;fill:{t['text']}}}
.m{{font:400 15px M,ui-monospace,Menlo,monospace;fill:{t['muted']}}}
.st{{font-size:{size}px;letter-spacing:-0.015em;fill:{t['text']}}}
</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="6" fill="{t['bg']}" stroke="{t['frame']}"/>
<text x="{PAD}" y="{name_y}" class="n">{NAME}</text>
<text x="{W-PAD}" y="{name_y}" class="m" text-anchor="end">{ROLE}</text>
<path d="M{PAD} {rule1_y}.5H{W-PAD}" stroke="{t['rule']}"/>
<text x="{PAD}" y="{st1_y}" class="st">{spans(LINE1)}</text>
<text x="{PAD}" y="{st2_y}" class="st">{spans(LINE2)}</text>
<path d="M{PAD} {rule2_y}.5H{W-PAD}" stroke="{t['rule']}"/>
<text x="{PAD}" y="{meta_y}" class="m">{META_L}</text>
<text x="{W-PAD}" y="{meta_y}" class="m" text-anchor="end" style="fill:{t['text']}">{META_R}</text>
<path d="M{W-PAD-link_w:.1f} {meta_y+6}.5H{W-PAD}" stroke="{t['accent']}"/>
</svg>
"""


for name, t in THEMES.items():
    with open(f"{OUT}/header-{name}.svg", "w") as fh:
        fh.write(svg(t))
print("statement size", size, "height", H)
