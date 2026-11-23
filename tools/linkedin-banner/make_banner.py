"""Generate the LinkedIn banner (1584x396) matching the zhaobo.me dark theme.

Usage:
    python3 make_banner.py

Writes, next to this file:
    banner-final.svg      vector source
    banner-final.png      1584x396 (LinkedIn's recommended size)
    banner-final@2x.png   3168x792 (upload this one; sharper on high-DPI screens)

PNGs are rendered with headless Google Chrome. Set CHROME=/path/to/chrome if it is not
at the default macOS location.

Design: the profile photo is the input to a small layered neural network; one highlighted
path runs through it to an output node, which opens into a probabilistic forecast
(dashed median with P25-P75 and P10-P90 quantile bands). Text sits upper right.
"""
import math
import os
import subprocess
import tempfile
from pathlib import Path

W, H = 1584, 396
BG0, BG1 = "#0c0d0f", "#15161a"
ACCENT = "#f0a37c"
ACCENT_DEEP = "#b4542a"
INK = "#f4f4f5"
SUBTLE = "#b9b9c3"
FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Inter, Arial, sans-serif"

# LinkedIn desktop profile photo, measured in banner coordinates (incl. white border).
PHOTO_C, PHOTO_R = (208, 364), 160

TITLE = "Financial Foundation Models"
SUBTITLE = "From Research to Production"
URL = "zhaobo.me"

# Text layout (right-aligned at TEXT_R). Title and subtitle are grouped; the pill sits apart,
# with its bottom (~224) clear of the forecast band.
TEXT_R = 1500
TITLE_SIZE, TITLE_Y = 39, 110
SUB_SIZE, SUB_Y = 29, 155
PILL_TOP, PILL_H = 182, 42
URL_SIZE, URL_W = 23, 121  # URL_W: measured width of URL at URL_SIZE in Chrome
GLOBE, ARROW = 20, 17      # icon sizes in px

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def smooth_path(points):
    """Catmull-Rom -> cubic Bezier path through points."""
    d = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d)


def ring_point(angle_deg, r):
    """Point on a circle of radius r around the profile photo."""
    a = math.radians(angle_deg)
    return PHOTO_C[0] + r * math.cos(a), PHOTO_C[1] + r * math.sin(a)


def base(out) -> None:
    """SVG header, shared gradients, background, glows and dot grid."""
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    out.append(f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/>
  </linearGradient>
  <radialGradient id="glow" cx="0.78" cy="0.35" r="0.55">
    <stop offset="0" stop-color="{ACCENT_DEEP}" stop-opacity="0.32"/>
    <stop offset="1" stop-color="{ACCENT_DEEP}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glow2" cx="0.30" cy="0.0" r="0.45">
    <stop offset="0" stop-color="#5b6b8c" stop-opacity="0.18"/>
    <stop offset="1" stop-color="#5b6b8c" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.3" stop-color="#fff" stop-opacity="1"/>
    <stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="fadeMask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <radialGradient id="halo" gradientUnits="userSpaceOnUse" cx="{PHOTO_C[0]}" cy="{PHOTO_C[1]}" r="330">
    <stop offset="0.45" stop-color="{ACCENT}" stop-opacity="0.16"/>
    <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
  </radialGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#ffffff" fill-opacity="0.06"/>
  </pattern>
</defs>""")

    # --- Background, glows, dot grid
    out.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#glow2)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#fadeMask)"/>')


def text_block(out) -> None:
    """Title, subtitle and the zhaobo.me pill (upper right)."""
    # --- Title and subtitle (upper right, clear of the photo and LinkedIn's buttons)
    out.append(f'<g font-family="{FONT}" text-anchor="end">')
    out.append(
        f'<text x="{TEXT_R}" y="{TITLE_Y}" fill="{INK}" font-size="{TITLE_SIZE}" font-weight="650" '
        f'letter-spacing="-0.6">{TITLE}</text>'
    )
    out.append(
        f'<text x="{TEXT_R}" y="{SUB_Y}" fill="{SUBTLE}" font-size="{SUB_SIZE}" font-weight="450">{SUBTITLE}</text>'
    )
    out.append("</g>")

    # --- URL as a link-style pill: globe icon + URL + up-right arrow, laid out right-to-left
    cy = PILL_TOP + PILL_H / 2
    arrow_x = TEXT_R - 16 - ARROW
    text_end = arrow_x - 8
    globe_x = text_end - URL_W - 9 - GLOBE
    left = globe_x - 14
    out.append(
        f'<rect x="{left}" y="{PILL_TOP}" width="{TEXT_R - left}" height="{PILL_H}" rx="{PILL_H / 2}" '
        f'fill="{ACCENT}" fill-opacity="0.12" stroke="{ACCENT}" stroke-opacity="0.6" stroke-width="1.5"/>'
    )
    out.append(
        f'<g transform="translate({globe_x},{cy - GLOBE / 2}) scale({GLOBE / 24:.4f})" fill="none" '
        f'stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
        f'<path d="M2 12h20"/></g>'
    )
    out.append(
        f'<text x="{text_end}" y="{cy + URL_SIZE / 3:.1f}" text-anchor="end" font-family="{FONT}" '
        f'fill="{ACCENT}" font-size="{URL_SIZE}" font-weight="600" letter-spacing="0.4">{URL}</text>'
    )
    out.append(
        f'<g transform="translate({arrow_x},{cy - ARROW / 2}) scale({ARROW / 24:.4f})" fill="none" '
        f'stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M7 7h10v10"/><path d="M7 17 17 7"/></g>'
    )


def port_dot(out, p):
    """White dot with a soft accent halo, used at the network input (photo) and output nodes."""
    out.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="10" fill="{ACCENT}" fill-opacity="0.22"/>')
    out.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="4.5" fill="{INK}"/>')


def fan_chart(out, o, end_x=W + 20, steps=17) -> None:
    """Quantile forecast from point o: dashed median (P50), P25-P75 and P10-P90 bands.
    Band width grows ~ sqrt(horizon); the lower side is a bit wider (downside skew)."""
    med = [(o[0] + (end_x - o[0]) * k / steps, o[1] - 12 * math.sin(k / 3.0) - 1.2 * k) for k in range(steps + 1)]

    def edge(width, side):
        return [(x, y + side * width * math.sqrt(k / steps)) for k, (x, y) in enumerate(med)]

    p90, p10 = edge(50, -1), edge(58, +1)
    p75, p25 = edge(22, -1), edge(26, +1)

    def band(upper, lower):
        return smooth_path(upper) + " L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in reversed(lower)) + " Z"

    out.append(
        f'<line x1="{o[0]}" y1="232" x2="{o[0]}" y2="372" stroke="#ffffff" stroke-opacity="0.18" '
        f'stroke-dasharray="2 5"/>'
    )
    out.append(f'<path d="{band(p90, p10)}" fill="{ACCENT}" fill-opacity="0.08"/>')
    out.append(f'<path d="{band(p75, p25)}" fill="{ACCENT}" fill-opacity="0.16"/>')
    for line, op in ((p90, 0.28), (p10, 0.28), (p75, 0.45), (p25, 0.45)):
        out.append(f'<path d="{smooth_path(line)}" fill="none" stroke="{ACCENT}" stroke-opacity="{op}" '
                   f'stroke-width="1"/>')
    out.append(f'<path d="{smooth_path(med)}" fill="none" stroke="{ACCENT}" stroke-width="2.2" '
               f'stroke-dasharray="7 7" stroke-linecap="round"/>')


def network(out) -> None:
    """Deep learning: a small layered network. The photo is the input; a prediction exits right."""
    out.append(f'<rect width="{W}" height="{H}" fill="url(#halo)"/>')
    xs, counts = [500, 615, 730, 845, 945], [4, 6, 6, 4, 2]
    cy0, gap = 220, 46
    layers = [[(x, cy0 + (i - (n - 1) / 2) * gap) for i in range(n)] for x, n in zip(xs, counts)]
    path_idx = [2, 4, 2, 1, 1]
    path = [layers[k][i] for k, i in enumerate(path_idx)]

    g = ['<g stroke="#ffffff" stroke-opacity="0.07" stroke-width="1">']
    for a, b in zip(layers, layers[1:]):
        for x1, y1 in a:
            for x2, y2 in b:
                g.append(f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}"/>')
    g.append("</g>")
    out += g

    port = ring_point(-30, PHOTO_R + 10)
    for x, y in layers[0]:
        out.append(
            f'<line x1="{port[0]:.1f}" y1="{port[1]:.1f}" x2="{x}" y2="{y:.1f}" stroke="{ACCENT}" '
            f'stroke-opacity="0.4" stroke-width="1.2" stroke-dasharray="3 5"/>'
        )
    pts = [port] + path
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    out.append(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-opacity="0.9" stroke-width="2.2" '
               f'stroke-linejoin="round"/>')

    # Output node, then a probabilistic forecast (quantile fan chart) to the right
    o = (1050, 300)
    for x, y in layers[-1]:
        on_path = (x, y) == path[-1]
        out.append(f'<line x1="{x}" y1="{y:.1f}" x2="{o[0]}" y2="{o[1]}" stroke="{ACCENT if on_path else "#ffffff"}" '
                   f'stroke-opacity="{0.9 if on_path else 0.12}" stroke-width="{2.2 if on_path else 1}"/>')
    fan_chart(out, o)

    for li, layer in enumerate(layers):
        for x, y in layer:
            hot = (x, y) == path[li]
            if hot:
                out.append(f'<circle cx="{x}" cy="{y:.1f}" r="14" fill="{ACCENT}" fill-opacity="0.14"/>')
            out.append(f'<circle cx="{x}" cy="{y:.1f}" r="6.5" fill="{ACCENT if hot else BG1}" '
                       f'stroke="{ACCENT if hot else "#ffffff"}" stroke-opacity="{1 if hot else 0.35}" stroke-width="1.2"/>')
    port_dot(out, o)
    port_dot(out, port)


def render_png(svg: str, dest: Path, scale: int) -> None:
    """Rasterize the SVG with headless Chrome at the given device scale factor."""
    html = (
        "<!doctype html><meta charset='utf-8'>"
        "<style>html,body{margin:0;background:#0c0d0f}svg{display:block}</style>" + svg
    )
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        page = Path(f.name)
    try:
        subprocess.run(
            [CHROME, "--headless=new", "--hide-scrollbars", f"--window-size={W},{H}",
             f"--force-device-scale-factor={scale}", f"--screenshot={dest}", page.as_uri()],
            check=True, capture_output=True,
        )
    finally:
        page.unlink(missing_ok=True)


def build() -> str:
    out = []
    base(out)
    network(out)
    text_block(out)
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    here = Path(__file__).parent
    svg = build()
    (here / "banner-final.svg").write_text(svg)
    render_png(svg, here / "banner-final.png", 1)
    render_png(svg, here / "banner-final@2x.png", 2)
    print("wrote banner-final.svg, banner-final.png, banner-final@2x.png")
