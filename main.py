#!/usr/bin/env python3
"""Draw one 1024x1024 PNG: a paper plane rides a ribbon of light into a
blazing sun under the words WOW. / DON'T BLINK.

Pure standard library (zlib, struct, math, os). Deterministic: every star,
bird and curve point comes from fixed constants and a fixed-seed generator,
so two runs write byte-identical files.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- canvas

ROWS = [bytearray(W * 3) for _ in range(H)]


def rgb(r, g, b):
    return bytes((r, g, b))


def mix(a, b, t):
    """Blend colour a towards colour b by t (0..1)."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def span(y, x0, x1, colour):
    """Fill one horizontal run on row y with a solid colour."""
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W, x1)
    if x1 <= x0:
        return
    ROWS[y][x0 * 3:x1 * 3] = rgb(*colour) * (x1 - x0)


def rect(x, y, w, h, colour):
    for yy in range(max(0, y), min(H, y + h)):
        span(yy, x, x + w, colour)


def disc(cx, cy, r, colour):
    """Filled circle, clipped to the canvas."""
    if r <= 0:
        return
    for dy in range(-r, r + 1):
        yy = cy + dy
        if 0 <= yy < H:
            dx = math.isqrt(r * r - dy * dy)
            span(yy, cx - dx, cx + dx + 1, colour)


def thick_line(x0, y0, x1, y1, r, colour):
    """A thick straight stroke, drawn as a chain of discs."""
    steps = max(1, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(steps + 1):
        t = i / steps
        disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, colour)


def fill_poly(points, colour):
    """Scanline fill of a simple polygon given as [(x, y), ...]."""
    ys = [p[1] for p in points]
    top, bottom = max(0, min(ys)), min(H - 1, max(ys))
    n = len(points)
    for y in range(top, bottom + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            span(y, int(math.ceil(xs[i])), int(math.floor(xs[i + 1])) + 1, colour)


# ------------------------------------------------------- deterministic rng

_seed = 987654321


def rnd():
    """Fixed-seed linear congruential generator; returns 0..1."""
    global _seed
    _seed = (1103515245 * _seed + 12345) & 0x7FFFFFFF
    return _seed / 0x7FFFFFFF


# ------------------------------------------------------------------- font
# Hand-drawn 5x7 bitmap letters, only the glyphs this picture needs.

GLYPHS = {
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def draw_text(text, x, y, scale, colour):
    """Draw text with the bitmap font; returns the width in pixels."""
    cx = x
    for ch in text:
        glyph = GLYPHS[ch]
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    rect(cx + col_i * scale, y + row_i * scale,
                         scale, scale, colour)
        cx += 6 * scale
    return cx - x


def text_width(text, scale):
    return (6 * len(text) - 1) * scale


def draw_text_centred(text, y, scale, colour, shadow):
    w = text_width(text, scale)
    x = (W - w) // 2
    if shadow is not None:
        draw_text(text, x + 5, y + 6, scale, shadow)
    draw_text(text, x, y, scale, colour)


# ------------------------------------------------------------------- scene

SUN_X, SUN_Y, SUN_R = 655, 690, 205


def paint_sky():
    """Deep indigo night, dark at the top, warming towards the horizon."""
    top = (8, 10, 42)
    mid = (24, 24, 88)
    low = (72, 38, 122)
    for y in range(H):
        if y < 512:
            colour = mix(top, mid, y / 512)
        else:
            colour = mix(mid, low, (y - 512) / 512)
        ROWS[y][:] = rgb(*colour) * W


def paint_stars():
    for _ in range(230):
        x = int(rnd() * W)
        y = int(rnd() * 760)
        bright = rnd()
        if bright > 0.92:
            colour = (255, 244, 200)
            disc(x, y, 2, colour)
            span(y, x - 5, x + 6, colour)
            span(y - 1, x, x + 1, colour)
            span(y + 1, x, x + 1, colour)
        elif bright > 0.6:
            disc(x, y, 2, (235, 238, 255))
        else:
            disc(x, y, 1, (200, 205, 240))


def paint_shooting_stars():
    streaks = [
        (120, 130, 260, 205, (255, 255, 255)),
        (820, 90, 930, 160, (255, 240, 190)),
        (430, 210, 520, 262, (210, 230, 255)),
    ]
    for x0, y0, x1, y1, colour in streaks:
        thick_line(x0, y0, x1, y1, 2, colour)
        disc(x0, y0, 4, colour)


def paint_sun():
    """Layered flat halo, then the blazing disc itself."""
    for r, colour in (
        (335, (122, 42, 110)),
        (300, (178, 52, 92)),
        (268, (232, 74, 52)),
        (238, (255, 110, 16)),
    ):
        disc(SUN_X, SUN_Y, r, colour)
    disc(SUN_X, SUN_Y, SUN_R, (255, 138, 0))
    disc(SUN_X, SUN_Y, 168, (255, 179, 0))
    disc(SUN_X, SUN_Y, 122, (255, 210, 63))
    disc(SUN_X, SUN_Y, 72, (255, 243, 176))
    # Corona spikes: short thick rays around the rim.
    for k in range(12):
        a = k * math.pi / 6 + 0.26
        x0 = SUN_X + int(math.cos(a) * (SUN_R + 6))
        y0 = SUN_Y + int(math.sin(a) * (SUN_R + 6))
        x1 = SUN_X + int(math.cos(a) * (SUN_R + 52))
        y1 = SUN_Y + int(math.sin(a) * (SUN_R + 52))
        thick_line(x0, y0, x1, y1, 5, (255, 170, 30))


def paint_ridge():
    """Dark horizon ridge the sun sits on."""
    fill_poly([
        (0, 905), (170, 862), (410, 898), (690, 866),
        (1024, 902), (1024, H), (0, H),
    ], (10, 10, 38))


def ribbon_point(t):
    """Quadratic Bezier from the bottom-left corner into the sun."""
    x0, y0 = -40, 1035
    x1, y1 = 260, 480
    x2, y2 = SUN_X, SUN_Y
    u = 1 - t
    return (
        int(u * u * x0 + 2 * u * t * x1 + t * t * x2),
        int(u * u * y0 + 2 * u * t * y1 + t * t * y2),
    )


def paint_ribbon():
    """Bold cyan ribbon with a white-hot core, sweeping into the sun.

    Two passes: every outer disc first, then every core disc, so the
    core stripe is never painted over by the next outer disc.
    """
    steps = 260
    points = [ribbon_point(i / steps) for i in range(steps + 1)]
    for i, pt in enumerate(points):
        width = 34 - 20 * (i / steps)
        disc(pt[0], pt[1], int(width), (16, 190, 255))
    for i, pt in enumerate(points):
        width = 34 - 20 * (i / steps)
        disc(pt[0], pt[1], int(width * 0.52), (255, 255, 255))


def paint_plane():
    """Tiny white paper plane on the ribbon's crest, nose into the sun."""
    t = 0.855
    px, py = ribbon_point(t)
    qx, qy = ribbon_point(t + 0.02)
    ang = math.atan2(qy - py, qx - px)
    ca, sa = math.cos(ang), math.sin(ang)

    def rot(lx, ly):
        return (px + int(lx * ca - ly * sa), py + int(lx * sa + ly * ca))

    # Dart body: long nose, swept-back wings, folded tail.
    fill_poly([rot(58, 0), rot(-42, -38), rot(-22, 0), rot(-42, 38)],
              (255, 255, 255))
    fill_poly([rot(58, 0), rot(-22, 0), rot(-42, 38)], (214, 226, 255))
    fill_poly([rot(58, 0), rot(-22, 0), rot(-42, -38)], (255, 255, 255))
    disc(px, py, 3, (255, 255, 255))


def paint_birds():
    """The ribbon's crest breaking into a flock of small dark birds."""
    flock = [
        (0.90, -58, 26), (0.93, -96, 22), (0.96, -70, 30),
        (0.88, -118, 18), (0.985, -120, 20), (0.92, -150, 16),
        (0.86, -170, 14), (0.99, -168, 15), (0.94, -196, 13),
    ]
    colour = (22, 14, 58)
    for t, lift, size in flock:
        bx, by = ribbon_point(t)
        by += lift
        thick_line(bx - size, by - size // 3, bx, by + size // 4, 3, colour)
        thick_line(bx + size, by - size // 3, bx, by + size // 4, 3, colour)


def paint_scene():
    paint_sky()
    paint_stars()
    paint_shooting_stars()
    paint_sun()
    paint_ridge()
    paint_ribbon()
    paint_plane()
    paint_birds()
    draw_text_centred("WOW.", 64, 26, (255, 255, 255), (10, 8, 48))
    draw_text_centred("DON'T BLINK.", 928, 8, (255, 236, 120), (10, 8, 48))


# --------------------------------------------------------------------- png

def chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(
        ">I", zlib.crc32(body) & 0xFFFFFFFF)


def encode_png():
    raw = b"".join(b"\x00" + bytes(row) for row in ROWS)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(out_dir, exist_ok=True)
    paint_scene()
    data = encode_png()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
