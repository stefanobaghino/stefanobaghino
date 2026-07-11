#!/usr/bin/env python3
"""Generate assets/alps-day.svg and assets/alps-night.svg.

An ultrawide (256x64, rendered 1024x256) pixel-art alpine panorama: a high
meadow with granite outcrops, shrubs and a winding footpath, tiered spruces
standing against layer after hazy layer of blue ridges, and a snow-capped
massif on the horizon. Drawn twice — bright summer daylight for light GitHub
themes, a moonlit night with fireflies for dark themes — with animated
touches layered on top as CSS-driven SVG rects.

Edit palettes / draw calls and re-run:  python3 assets/generate_alps.py

Note: GitHub's image proxy (Camo) caches aggressively — when updating the
art, bump a query string on the README's img srcs (e.g. ?v=2).
"""

import base64
import struct
import zlib
from pathlib import Path

W, H = 256, 64
SCALE = 4
HERE = Path(__file__).parent


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


DAY = {
    "sky0": (0x7F, 0xB4, 0xDC), "sky1": (0x96, 0xC6, 0xE8),
    "sky2": (0xAD, 0xD8, 0xF0), "sky3": (0xC4, 0xE6, 0xF6),
    "cloud": (0xF6, 0xFB, 0xFE), "cloud_sh": (0xDC, 0xED, 0xF6),
    "star": (0xFF, 0xFF, 0xFF), "star_dim": (0xE8, 0xF2, 0xFA),
    "moon": (0xF6, 0xFB, 0xFE), "moon_sh": (0xD6, 0xE9, 0xF4),
    "snow": (0xF4, 0xF8, 0xFC), "snow_sh": (0xC9, 0xDC, 0xEC),
    "rock": (0x7E, 0x94, 0xB2), "rock_sh": (0x5E, 0x76, 0x96),
    "ridge1": (0x8A, 0xA6, 0xC4), "ridge2": (0x6C, 0x8A, 0xAC),
    "fir_far": (0x2E, 0x52, 0x44), "fir_hi": (0x3E, 0x6A, 0x56),
    "grass_a": (0x6F, 0xA0, 0x46), "grass_b": (0x5C, 0x8A, 0x38),
    "grass_hi": (0x8A, 0xBC, 0x5A), "grass_dk": (0x4A, 0x72, 0x30),
    "shrub": (0x3E, 0x6A, 0x34), "shrub_hi": (0x55, 0x8A, 0x42),
    "tree_dk": (0x1F, 0x44, 0x34), "tree_md": (0x2E, 0x5E, 0x46),
    "tree_hi": (0x41, 0x7C, 0x58), "trunk": (0x6E, 0x4A, 0x30),
    "bld": (0xA8, 0xB2, 0xA4), "bld_hi": (0xC6, 0xCE, 0xC0),
    "bld_sh": (0x7E, 0x8A, 0x7A),
    "path": (0xC9, 0xB8, 0x94), "path_sh": (0xA8, 0x98, 0x70),
    "fl_w": (0xF4, 0xF0, 0xE8), "fl_p": (0xE8, 0x6A, 0x8A),
    "fl_y": (0xE8, 0xC8, 0x48),
    "bird": (0x3A, 0x44, 0x48), "ff": (0xFF, 0xE2, 0x8A),
    "vig": (0x5E, 0x78, 0x92),
}
NIGHT = {
    "sky0": (0x0A, 0x0A, 0x1E), "sky1": (0x10, 0x10, 0x31),
    "sky2": (0x16, 0x17, 0x41), "sky3": (0x1D, 0x1E, 0x4C),
    "cloud": (0x2A, 0x2B, 0x58), "cloud_sh": (0x22, 0x23, 0x4E),
    "star": (0xD9, 0xD7, 0xF2), "star_dim": (0x7B, 0x7C, 0xB0),
    "moon": (0xE8, 0xE0, 0xBC), "moon_sh": (0xC4, 0xB9, 0x8E),
    "snow": (0xB8, 0xC2, 0xDC), "snow_sh": (0x8A, 0x96, 0xBC),
    "rock": (0x3A, 0x44, 0x68), "rock_sh": (0x2C, 0x34, 0x50),
    "ridge1": (0x2A, 0x33, 0x54), "ridge2": (0x22, 0x2A, 0x48),
    "fir_far": (0x14, 0x25, 0x1E), "fir_hi": (0x1A, 0x2E, 0x26),
    "grass_a": (0x1E, 0x33, 0x24), "grass_b": (0x18, 0x2A, 0x1E),
    "grass_hi": (0x28, 0x42, 0x2E), "grass_dk": (0x12, 0x20, 0x16),
    "shrub": (0x16, 0x28, 0x1A), "shrub_hi": (0x1E, 0x36, 0x24),
    "tree_dk": (0x0E, 0x1E, 0x16), "tree_md": (0x14, 0x28, 0x1E),
    "tree_hi": (0x1C, 0x36, 0x26), "trunk": (0x2A, 0x1E, 0x14),
    "bld": (0x3A, 0x42, 0x48), "bld_hi": (0x4A, 0x54, 0x5C),
    "bld_sh": (0x2A, 0x32, 0x38),
    "path": (0x3A, 0x3A, 0x50), "path_sh": (0x2E, 0x2E, 0x42),
    "fl_w": (0x3A, 0x42, 0x48), "fl_p": (0x3A, 0x42, 0x48),
    "fl_y": (0x3A, 0x42, 0x48),
    "bird": (0x3A, 0x44, 0x48), "ff": (0xFF, 0xE2, 0x8A),
    "vig": (0x05, 0x05, 0x0D),
}


def skyline(points, x):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def build(night):
    P = {k: v + (255,) for k, v in (NIGHT if night else DAY).items()}
    buf = [[P["sky0"]] * W for _ in range(H)]

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            buf[y][x] = P[c] if isinstance(c, str) else c

    def rect(x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                px(xx, yy, c)

    def tint(x, y, c, t):
        if 0 <= x < W and 0 <= y < H:
            col = P[c] if isinstance(c, str) else c
            buf[y][x] = mix(buf[y][x], col, t)

    def hexc(c):
        return "#{:02x}{:02x}{:02x}".format(*(P[c][:3] if isinstance(c, str) else c[:3]))

    def hex_at(x, y):
        return "#{:02x}{:02x}{:02x}".format(*buf[y][x][:3])

    # ------------------------------------------------------------------ sky
    for y in range(H):
        band = "sky0" if y <= 8 else ("sky1" if y <= 16 else ("sky2" if y <= 24 else "sky3"))
        rect(0, y, W, 1, band)
    for y, below in [(8, "sky1"), (16, "sky2"), (24, "sky3")]:
        for x in range(W):
            if (x + y) % 2:
                px(x, y, below)

    if night:
        for x, y in [(16, 5), (44, 9), (76, 4), (104, 7), (132, 10), (160, 4),
                     (188, 9), (240, 12), (252, 5), (60, 13), (146, 6)]:
            px(x, y, "star")
        for x, y in [(76, 4), (188, 9)]:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                px(x + dx, y + dy, "star_dim")
        for x, y in [(8, 11), (30, 7), (52, 3), (68, 10), (92, 12), (116, 3),
                     (124, 8), (152, 12), (172, 7), (200, 5), (216, 10), (230, 4)]:
            px(x, y, "star_dim")
        for r, t in [(6, 0.10), (5, 0.15)]:      # moon halo
            for yy in range(7 - r, 7 + r + 1):
                for xx in range(214 - r, 214 + r + 1):
                    d2 = (xx - 214) ** 2 + (yy - 7) ** 2
                    if r * r - r < d2 <= r * r + r and (xx + yy) % 2:
                        tint(xx, yy, "moon", t)
        for yy in range(4, 11):
            for xx in range(211, 218):
                if (xx - 214) ** 2 + (yy - 7) ** 2 <= 11:
                    px(xx, yy, "moon")
        px(213, 6, "moon_sh")
        px(215, 8, "moon_sh")
        px(212, 8, "moon_sh")
    else:
        # ragged, banded clouds in the style of the reference
        for x0, y0, w in [(30, 5, 42), (118, 9, 52), (198, 4, 34)]:
            for x in range(x0, x0 + w):
                if (x * 5) % 9 != 0:
                    px(x, y0 + 1, "cloud")
                if x0 + 4 < x < x0 + w - 6 and (x * 3) % 7 != 0:
                    px(x, y0, "cloud")
                if x0 + 2 < x < x0 + w - 2 and (x * 7) % 5 != 0:
                    px(x, y0 + 2, "cloud_sh")

    # --------------------------------------------- snow massif on the horizon
    FAR = [(0, 18), (10, 15), (22, 17), (32, 11), (45, 15), (52, 9), (64, 14),
           (72, 12), (84, 16), (95, 10), (106, 15), (118, 13), (130, 17),
           (142, 19), (152, 20), (160, 16), (170, 13), (182, 15), (198, 8),
           (210, 13), (222, 11), (234, 15), (246, 13), (255, 16)]
    for x in range(W):
        top = round(skyline(FAR, x))
        snow_to = top + 2 + (x * 7) % 2
        for y in range(top, 25):
            if y < snow_to:
                px(x, y, "snow" if (y < snow_to - 1 or (x + y) % 2) else "snow_sh")
            elif (x * 5 + y * 3) % 13 == 0 and y < top + 7:
                px(x, y, "snow_sh")              # snow gullies down the face
            elif x % 3 == 0 and (x + y) % 2:
                px(x, y, "rock_sh")
            else:
                px(x, y, "rock")
    for y in range(22, 25):                      # atmospheric haze at the base
        for x in range(W):
            if (x + y) % 2:
                tint(x, y, "sky3", 0.35)

    # ------------------------------------------------- receding hazy ridges
    R1 = [(0, 26), (20, 24), (40, 27), (60, 25), (85, 28), (110, 26), (135, 28),
          (160, 25), (185, 27), (210, 24), (235, 27), (255, 25)]
    R2 = [(0, 30), (25, 28), (50, 31), (75, 29), (100, 32), (125, 30), (150, 32),
          (175, 29), (200, 31), (225, 29), (255, 31)]
    for pts, c, bot in [(R1, "ridge1", 31), (R2, "ridge2", 35)]:
        for x in range(W):
            top = round(skyline(pts, x))
            rect(x, top, 1, bot - top, c)
            if (x + top) % 2:
                tint(x, top, "sky3", 0.25)

    # dark forested ridge with tiny tree spikes
    R3 = [(0, 34), (30, 32), (60, 35), (90, 33), (120, 35), (150, 33),
          (180, 35), (210, 33), (240, 35), (255, 34)]
    for x in range(W):
        top = round(skyline(R3, x))
        rect(x, top, 1, 40 - top, "fir_far")
        if x % 3 == 1:
            px(x, top - 1, "fir_far")
        if x % 7 == 3:
            px(x, top - 2, "fir_far")
            px(x, top - 1, "fir_far")
        if (x + top) % 4 == 0:
            px(x, top + 1, "fir_hi")

    # ------------------------------------------------------------ the meadow
    MEAD = [(0, 37), (30, 36), (60, 38), (90, 36), (120, 38), (150, 37),
            (180, 39), (210, 37), (240, 38), (255, 38)]
    for x in range(W):
        top = round(skyline(MEAD, x))
        for y in range(top, H):
            c = "grass_a"
            if (x * 7 + y * 13) % 11 < 3:
                c = "grass_b"
            if y >= 58 and (x + y) % 3 == 0:
                c = "grass_dk"
            px(x, y, c)
        px(x, top, "grass_hi" if x % 2 else "grass_a")
        if (x * 3) % 5 == 0:
            px(x, top + 2, "grass_hi")

    # shrub clumps, reference-style bumpy texture
    for x0, w, base in [(6, 34, 60), (78, 30, 58), (150, 24, 61), (226, 30, 60)]:
        for x in range(x0, x0 + w):
            hgt = 2 + (x * 11) % 4
            for y in range(base - hgt, base):
                px(x, y, "shrub" if (x + y) % 2 else "shrub_hi")
            if (x * 5) % 3 == 0:
                px(x, base - hgt - 1, "shrub")

    # granite outcrops with mossy feet
    for bx, by, bw, bh in [(44, 50, 22, 9), (2, 44, 14, 7), (180, 46, 14, 6)]:
        for x in range(bx, bx + bw):
            dome = round(bh * (1 - ((x - bx - bw / 2) / (bw / 2)) ** 2))
            for y in range(by + bh - dome, by + bh):
                px(x, y, "bld")
        for x in range(bx + 1, bx + bw - 1, 2):
            px(x, by + bh - round(bh * (1 - ((x - bx - bw / 2) / (bw / 2)) ** 2)), "bld_hi")
        for x in range(bx, bx + bw, 3):
            px(x, by + bh - 1, "bld_sh")
            tint(x + 1, by + bh - 1, "shrub", 0.5)

    # winding footpath climbing to the ridge
    trail = [(140, 63), (138, 61), (134, 59), (129, 57), (124, 55), (120, 53),
             (117, 51), (113, 49), (108, 47), (103, 45), (99, 43), (96, 41),
             (93, 39), (91, 38)]
    for i, (x, y) in enumerate(trail):
        wdt = 3 if y > 56 else (2 if y > 46 else 1)
        for dx in range(wdt):
            px(x + dx, y, "path" if (x + dx + y) % 2 else "path_sh")

    # wildflowers scattered on the sunny slopes (day only)
    if not night:
        for x, y, c in [(24, 52, "fl_w"), (38, 57, "fl_y"), (70, 51, "fl_p"),
                        (88, 55, "fl_w"), (112, 58, "fl_y"), (146, 54, "fl_w"),
                        (166, 57, "fl_p"), (196, 55, "fl_y"), (214, 59, "fl_w"),
                        (244, 56, "fl_p"), (58, 61, "fl_y"), (128, 61, "fl_w")]:
            px(x, y, c)

    # ------------------------------------------------------- tiered spruces
    def spruce(cx, base, h):
        trunk_h = max(2, h // 6)
        rect(cx, base - trunk_h, 1, trunk_h, "trunk")
        rows = h - trunk_h
        top = base - h
        max_w = (max(5, h // 2)) | 1
        for i in range(rows):
            y = top + i
            wdt = min(max_w, 1 + (i // 3) * 2 + (i % 3) * 2)  # sawtooth tiers
            wdt |= 1
            x0 = cx - wdt // 2
            c = "tree_dk" if i % 3 == 2 else "tree_md"
            rect(x0, y, wdt, 1, c)
            if not night:
                px(x0, y, "tree_hi")
                if (x0 + i) % 4 == 0:
                    px(x0 + wdt // 3, y, "tree_hi")
            if i % 3 == 2 and wdt < max_w:
                px(x0 - 1, y, c)
                px(x0 + wdt, y, c)
        px(cx, top - 1, "tree_md")

    for cx, base, h in sorted([(126, 46, 16), (176, 44, 13), (58, 52, 24),
                               (152, 52, 20), (236, 50, 18), (28, 56, 28),
                               (96, 50, 30), (206, 54, 26)], key=lambda s: s[1]):
        spruce(cx, base, h)
    for cx, base, h in [(14, 50, 6), (70, 48, 5), (112, 46, 5), (190, 50, 6), (248, 52, 7)]:
        spruce(cx, base, h)

    # -------------------------------------------------------------- vignette
    cx, cy = W / 2, H * 0.45
    for y in range(H):
        for x in range(W):
            dx = (x - cx) / (W * 0.62)
            dy = (y - cy) / (H * 0.80)
            d = (dx * dx + dy * dy) ** 0.5
            t = (d - 0.62) * (0.55 if night else 0.30)
            if t > 0:
                buf[y][x] = mix(buf[y][x], P["vig"], min(t, 0.40 if night else 0.20))

    # ------------------------------------------------------------ png + svg
    def png():
        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
        raw = b"".join(b"\x00" + b"".join(bytes(c) for c in row) for row in buf)
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))

    parts = []

    def orect(x, y, color, cls, w=1, h=1, opacity=None):
        op = f' opacity="{opacity}"' if opacity is not None else ""
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" class="{cls}"{op}/>')

    if night:
        for i, (x, y) in enumerate([(16, 5), (76, 4), (132, 10), (188, 9), (252, 5), (104, 7)]):
            orect(x, y, hex_at(x, y), f"tw d{i % 5}", opacity=0)
        for i, (x, y) in enumerate([(34, 50), (74, 47), (120, 52), (168, 49), (222, 53)]):
            orect(x, y, hexc("ff"), f"ff d{i % 5}", opacity=0)
        parts.append(f'<g class="shoot" opacity="0">'
                     f'<rect x="120" y="4" width="1" height="1" fill="{hexc("star")}"/>'
                     f'<rect x="121" y="3" width="1" height="1" fill="{hexc("star_dim")}"/>'
                     f'<rect x="122" y="3" width="1" height="1" fill="{hexc("star_dim")}"/></g>')
    else:
        for i, (x, y) in enumerate([(60, 7), (150, 12), (226, 9)]):
            parts.append(f'<g class="fly d{i * 2}" opacity="0">'
                         f'<rect x="{x}" y="{y}" width="1" height="1" fill="{hexc("bird")}"/>'
                         f'<rect x="{x + 1}" y="{y + 1}" width="1" height="1" fill="{hexc("bird")}"/>'
                         f'<rect x="{x + 2}" y="{y}" width="1" height="1" fill="{hexc("bird")}"/></g>')
        parts.append(f'<g class="drift" opacity="0">'
                     f'<rect x="70" y="14" width="12" height="1" fill="{hexc("cloud")}"/>'
                     f'<rect x="73" y="13" width="6" height="1" fill="{hexc("cloud")}"/></g>')
        for i, (x, y) in enumerate([(72, 50), (148, 53)]):
            parts.append(f'<g class="flut d{i * 2}" opacity=".9">'
                         f'<rect x="{x}" y="{y}" width="1" height="1" fill="{hexc("fl_w")}"/></g>')

    css = """
    .tw{animation:twinkle 3.4s ease-in-out infinite}
    .ff{animation:firefly 2.6s ease-in-out infinite}
    .shoot{animation:shoot 13s steps(6) infinite}
    .fly{animation:fly 26s steps(48) infinite}
    .drift{animation:drift 70s steps(40) infinite}
    .flut{animation:flut 9s steps(2) infinite}
    .d1{animation-delay:.9s}.d2{animation-delay:1.8s}.d3{animation-delay:2.9s}.d4{animation-delay:3.8s}
    @keyframes twinkle{0%,100%{opacity:0}50%{opacity:.95}}
    @keyframes firefly{0%,100%{opacity:0}40%,60%{opacity:.9}}
    @keyframes shoot{0%,90%{opacity:0;transform:translate(0,0)}91%{opacity:.95}100%{opacity:0;transform:translate(-16px,8px)}}
    @keyframes fly{0%{transform:translate(0,0);opacity:0}6%{opacity:.8}94%{opacity:.8}100%{transform:translate(-48px,2px);opacity:0}}
    @keyframes drift{0%{transform:translateX(0);opacity:0}6%{opacity:.9}94%{opacity:.9}100%{transform:translateX(-40px);opacity:0}}
    @keyframes flut{0%,100%{transform:translate(0,0)}25%{transform:translate(2px,-1px)}50%{transform:translate(4px,0)}75%{transform:translate(2px,1px)}}
    @media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
    title = ("Alpine meadow by night — lofi pixel art" if night
             else "Alpine meadow by day — lofi pixel art")
    b64 = base64.b64encode(png()).decode()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W * SCALE}" height="{H * SCALE}" viewBox="0 0 {W} {H}">
  <title>{title}</title>
  <style>
    image{{image-rendering:crisp-edges;image-rendering:pixelated}}
    rect{{shape-rendering:crispEdges}}
{css}  </style>
  <image href="data:image/png;base64,{b64}" width="{W}" height="{H}"/>
  {chr(10).join("  " + p for p in parts)}
</svg>
"""


def main():
    for mode, night in (("day", False), ("night", True)):
        out = HERE / f"alps-{mode}.svg"
        svg = build(night)
        out.write_text(svg)
        print(f"wrote {out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
