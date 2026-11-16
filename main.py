#!/usr/bin/env python3
"""Make the AI judge excited — ai-excited-01 entry.

Procedurally draws a single 1024x1024 PNG, standard library only.

The scene: a deep indigo night sky, one huge blazing sun low on the
horizon, and a bold ribbon of light — cyan melting into magenta — that
sweeps up from the bottom corner and curls straight into the sun. A tiny
white paper plane rides the crest of the ribbon, and where the ribbon
breaks it bursts into a flock of birds. The twist is the scale: the
smallest thing in the picture (a paper plane) is the one flying into
the sun. Big punchy text speaks straight to the judge: WOW. / DON'T BLINK.

Everything is deterministic: a fixed-seed generator for the stars, no
time, no randomness from the environment, no network. Run twice and the
bytes are identical.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- pixels

buf = bytearray(W * H * 3)


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend_px(x, y, r, g, b, a):
    """Blend colour (r,g,b) over the pixel at (x,y) with alpha a (0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        if a >= 1.0:
            set_px(x, y, r, g, b)
            return
        i = (y * W + x) * 3
        buf[i] = int(buf[i] + (r - buf[i]) * a)
        buf[i + 1] = int(buf[i + 1] + (g - buf[i + 1]) * a)
        buf[i + 2] = int(buf[i + 2] + (b - buf[i + 2]) * a)


def lerp(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def fill_span(y, x0, x1, r, g, b, a=1.0):
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    if a >= 1.0:
        for x in range(x0, x1 + 1):
            i = (y * W + x) * 3
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
    else:
        for x in range(x0, x1 + 1):
            blend_px(x, y, r, g, b, a)


def disc(cx, cy, rad, colour, a=1.0):
    """Filled circle, centre (cx,cy), radius rad, colour (r,g,b)."""
    r = int(rad)
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        fill_span(cy + dy, cx - dx, cx + dx, colour[0], colour[1], colour[2], a)


def line(x0, y0, x1, y1, colour, a=1.0, width=1):
    """Bresenham line, optionally thick."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        if width <= 1:
            blend_px(x, y, colour[0], colour[1], colour[2], a)
        else:
            disc(x, y, width // 2, colour, a)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def fill_poly(points, colour, a=1.0):
    """Scanline fill of a simple polygon given as [(x,y), ...]."""
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H - 1, max(ys)) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
        if len(xs) >= 2:
            xs.sort()
            fill_span(y, xs[0], xs[-1], colour[0], colour[1], colour[2], a)


# ------------------------------------------------------- deterministic rng

_seed = 987654321


def rnd():
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed / 0x7FFFFFFF


# ------------------------------------------------------------------- sky

def draw_sky():
    top = (8, 6, 38)
    mid = (48, 16, 92)
    low = (150, 42, 96)
    for y in range(H):
        t = y / (H - 1)
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        else:
            c = lerp(mid, low, (t - 0.55) / 0.45)
        base = y * W * 3
        for x in range(W):
            i = base + x * 3
            buf[i] = c[0]
            buf[i + 1] = c[1]
            buf[i + 2] = c[2]


def draw_stars():
    for _ in range(240):
        x = int(rnd() * W)
        y = int(rnd() * 640)
        b = 140 + int(rnd() * 115)
        s = rnd()
        if s < 0.12:
            # sparkle: little cross
            line(x - 3, y, x + 3, y, (b, b, 255), 0.9)
            line(x, y - 3, x, y + 3, (b, b, 255), 0.9)
        elif s < 0.5:
            disc(x, y, 2, (b, b, 255), 0.95)
        else:
            set_px(x, y, b, b, 255)


# ------------------------------------------------------------------- sun

SUN_X, SUN_Y, SUN_R = 712, 648, 148


def draw_sun():
    # outer glow: concentric discs, fading out (fine steps so no banding)
    for rad in range(330, SUN_R, -2):
        t = (330 - rad) / (330 - SUN_R)
        a = 0.04 + 0.12 * t * t
        col = lerp((255, 90, 40), (255, 170, 60), t)
        disc(SUN_X, SUN_Y, rad, col, a)
    # body: warm gradient rings, brightest at the core
    for rad in range(SUN_R, 0, -2):
        t = 1.0 - rad / SUN_R
        col = lerp((255, 120, 30), (255, 236, 150), t)
        disc(SUN_X, SUN_Y, rad, col, 1.0)
    # crisp rim
    for ang in range(0, 360, 2):
        a = math.radians(ang)
        x = int(SUN_X + math.cos(a) * (SUN_R + 1))
        y = int(SUN_Y + math.sin(a) * (SUN_R + 1))
        set_px(x, y, 255, 220, 130)


# ------------------------------------------------------------- light ribbon

def bezier(p0, p1, p2, t):
    u = 1.0 - t
    return (
        int(u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]),
        int(u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]),
    )


def draw_ribbon():
    """The swoosh: cyan -> magenta -> orange, curling into the sun."""
    p0 = (30, 990)
    p1 = (330, 660)
    p2 = (648, 592)
    n = 220
    pts = [bezier(p0, p1, p2, i / n) for i in range(n + 1)]
    cyan = (0, 214, 255)
    magenta = (255, 45, 170)
    orange = (255, 140, 40)
    for i, (x, y) in enumerate(pts):
        t = i / n
        if t < 0.55:
            col = lerp(cyan, magenta, t / 0.55)
        else:
            col = lerp(magenta, orange, (t - 0.55) / 0.45)
        rad = int(78 - 46 * t)  # ribbon tapers as it climbs
        disc(x, y, rad, col, 1.0)
    # bright white core, thinner, so the ribbon reads as a beam of light
    for i, (x, y) in enumerate(pts):
        t = i / n
        if t > 0.88:
            continue
        rad = max(6, int(20 - 12 * t))
        disc(x, y, rad, (255, 255, 255), 0.85)
    # spray: white flecks bursting off the upper edge near the tip
    for i in range(26):
        t = 0.55 + rnd() * 0.4
        x, y = bezier(p0, p1, p2, t)
        ox = int((rnd() - 0.3) * 150)
        oy = -int(rnd() * 130)
        disc(x + ox, y + oy, 2 + int(rnd() * 3), (255, 255, 255), 0.9)


def draw_birds():
    """The ribbon's crest breaks into a flock — the twist."""
    flock = [
        (560, 470, 26), (610, 430, 32), (665, 398, 22), (715, 360, 30),
        (770, 330, 20), (820, 300, 26), (860, 268, 17), (520, 520, 18),
    ]
    for (x, y, s) in flock:
        col = (255, 240, 180) if s % 3 else (255, 255, 255)
        line(x - s, y - s // 3, x, y, col, 1.0, 3)
        line(x, y, x + s, y - s // 3, col, 1.0, 3)


def draw_plane():
    """Tiny white paper plane at the ribbon's tip, nose into the sun."""
    nose = (730, 546)
    tail_top = (622, 536)
    tail_bot = (640, 596)
    fold = (664, 560)
    fill_poly([nose, tail_top, fold], (255, 255, 255))
    fill_poly([nose, fold, tail_bot], (215, 228, 255))
    line(nose[0], nose[1], fold[0], fold[1], (160, 170, 220), 1.0, 2)
    # dotted trail behind it, back along the ribbon
    for i in range(7):
        t = 0.86 - i * 0.035
        x, y = bezier((30, 990), (330, 660), (648, 592), t)
        disc(x, y - 6, 4, (255, 255, 255), 0.9)


def draw_shooting_stars():
    for (x, y, ln) in [(150, 120, 90), (880, 90, 70), (420, 60, 60)]:
        for i in range(ln):
            t = i / ln
            blend_px(
                x + i, y + i // 2,
                255, 255, 255, 0.9 * (1 - t),
            )


# -------------------------------------------------------------------- text

# 5x7 bitmap font, only the glyphs we need. '#' = on.
FONT = {
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(s, x0, y0, scale, colour):
    x = x0
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            set_px(
                                x + gx * scale + dx,
                                y0 + gy * scale + dy,
                                colour[0], colour[1], colour[2],
                            )
        x += 6 * scale


def draw_texts():
    # "WOW." huge across the top, with a hot-orange drop shadow.
    big = "WOW."
    scale = 15
    w = text_width(big, scale)
    x = (W - w) // 2
    draw_text(big, x + 7, 78, scale, (255, 90, 30))
    draw_text(big, x, 70, scale, (255, 255, 255))
    # "DON'T BLINK." small along the bottom.
    small = "DON'T BLINK."
    scale2 = 6
    w2 = text_width(small, scale2)
    draw_text(small, (W - w2) // 2, 936, scale2, (255, 236, 170))


# --------------------------------------------------------------------- png

def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png


def main():
    draw_sky()
    draw_stars()
    draw_shooting_stars()
    draw_sun()
    draw_ribbon()
    draw_birds()
    draw_plane()
    draw_texts()
    data = encode_png()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
