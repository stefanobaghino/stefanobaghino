#!/usr/bin/env python3
"""Generate assets/header.svg — ultrawide lofi pixel-art README header.

A 256x64 night scene (someone quietly coding by a window) is drawn into a
pixel buffer, packed as a PNG, and base64-embedded into a 1024x256 SVG.
Animated touches (star twinkle, antenna beacons, city-window flicker, cursor
blink, mug steam, music notes, cat Zzz, breathing LEDs) are small SVG rects
layered on top and driven by CSS keyframes.

Edit the palette / draw calls and re-run:  python3 assets/generate_header.py

Note: GitHub's image proxy (Camo) caches aggressively — when updating the
art, bump a query string on the README's img src (e.g. header.svg?v=2).
"""

import base64
import struct
import zlib
from pathlib import Path

W, H = 256, 64
SCALE = 4
OUT = Path(__file__).parent / "header.svg"


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


C = {
    # room
    "wall":     (0x22, 0x1D, 0x33, 255),
    "wall_dk":  (0x1B, 0x17, 0x29, 255),
    "board":    (0x12, 0x0F, 0x1C, 255),
    "floor":    (0x16, 0x12, 0x1D, 255),
    "floor_ln": (0x1E, 0x18, 0x26, 255),
    "rug":      (0x2E, 0x24, 0x40, 255),
    "rug_hi":   (0x3A, 0x2E, 0x52, 255),
    # window & sky
    "frame":    (0x45, 0x37, 0x57, 255),
    "frame_hi": (0x57, 0x49, 0x69, 255),
    "sill":     (0x4E, 0x40, 0x60, 255),
    "sky0":     (0x0A, 0x0A, 0x1E, 255),
    "sky1":     (0x10, 0x10, 0x31, 255),
    "sky2":     (0x16, 0x17, 0x41, 255),
    "sky3":     (0x1D, 0x1E, 0x4C, 255),
    "star":     (0xD9, 0xD7, 0xF2, 255),
    "star_dim": (0x7B, 0x7C, 0xB0, 255),
    "moon":     (0xE8, 0xE0, 0xBC, 255),
    "moon_sh":  (0xC4, 0xB9, 0x8E, 255),
    "city_far": (0x19, 0x1A, 0x38, 255),
    "city":     (0x0E, 0x0F, 0x26, 255),
    "win_lit":  (0xE8, 0xB3, 0x66, 255),
    "beacon":   (0xD9, 0x57, 0x57, 255),
    # desk & furniture
    "desk_hi":  (0x7E, 0x53, 0x40, 255),
    "desk":     (0x6E, 0x47, 0x36, 255),
    "desk_gr":  (0x64, 0x40, 0x30, 255),
    "desk_sh":  (0x48, 0x2D, 0x22, 255),
    "leg":      (0x3A, 0x24, 0x1C, 255),
    "shelf":    (0x48, 0x2D, 0x22, 255),
    "case":     (0x24, 0x1C, 0x30, 255),
    "case_dk":  (0x1A, 0x14, 0x24, 255),
    "case_ln":  (0x3A, 0x2E, 0x48, 255),
    "chair":    (0x32, 0x2B, 0x47, 255),
    "chair_dk": (0x26, 0x21, 0x38, 255),
    # monitor & laptop
    "mon":      (0x10, 0x10, 0x19, 255),
    "screen":   (0x0B, 0x1A, 0x22, 255),
    "titlebar": (0x14, 0x24, 0x2E, 255),
    "panel":    (0x0E, 0x20, 0x2A, 255),
    "status":   (0x2A, 0x4A, 0x5A, 255),
    "code_g":   (0x7F, 0xB9, 0x8A, 255),
    "code_p":   (0x9A, 0x7B, 0xC9, 255),
    "code_c":   (0x5F, 0xB8, 0xCC, 255),
    "code_o":   (0xC9, 0x9B, 0x5F, 255),
    "code_r":   (0xC9, 0x6A, 0x6A, 255),
    "comment":  (0x4A, 0x60, 0x70, 255),
    "claude":   (0xD9, 0x77, 0x57, 255),
    "cursor":   (0xC9, 0xE8, 0xD6, 255),
    "keyb":     (0x2E, 0x28, 0x44, 255),
    "keyb_hi":  (0x3E, 0x38, 0x58, 255),
    "laptop":   (0x1A, 0x18, 0x26, 255),
    "lap_scr":  (0x0A, 0x14, 0x18, 255),
    "lap_g":    (0x5F, 0x9E, 0x6A, 255),
    "tower":    (0x16, 0x12, 0x1F, 255),
    "vent":     (0x10, 0x0D, 0x18, 255),
    "led":      (0x5F, 0xD8, 0xCC, 255),
    "cable":    (0x0D, 0x0A, 0x16, 255),
    # props
    "mug":      (0xA8, 0x4E, 0x52, 255),
    "mug_hi":   (0xB9, 0x60, 0x63, 255),
    "coffee":   (0x3A, 0x24, 0x18, 255),
    "steam":    (0xB8, 0xC2, 0xE0, 255),
    "lamp":     (0x30, 0x2B, 0x45, 255),
    "light":    (0xE8, 0xC0, 0x78, 255),
    "leaf":     (0x3A, 0x75, 0x48, 255),
    "leaf_dk":  (0x28, 0x54, 0x36, 255),
    "leaf_hi":  (0x4C, 0x91, 0x59, 255),
    "pot":      (0x8E, 0x4A, 0x34, 255),
    "pot_dk":   (0x6E, 0x38, 0x26, 255),
    "soil":     (0x24, 0x18, 0x12, 255),
    "spk":      (0x19, 0x15, 0x23, 255),
    "spk_rim":  (0x3D, 0x37, 0x57, 255),
    "spk_cone": (0x2B, 0x25, 0x40, 255),
    "spk_dot":  (0x4D, 0x47, 0x70, 255),
    "radio":    (0x2A, 0x23, 0x3A, 255),
    "wire":     (0x3E, 0x38, 0x52, 255),
    "cushion":  (0x5E, 0x3C, 0x56, 255),
    "cush_hi":  (0x76, 0x50, 0x6C, 255),
    "cat":      (0x26, 0x20, 0x33, 255),
    "cat_dk":   (0x1A, 0x16, 0x26, 255),
    "cat_hi":   (0x3A, 0x33, 0x4E, 255),
    "poster_f": (0x15, 0x11, 0x1F, 255),
    "sunset_a": (0xC9, 0x84, 0x5C, 255),
    "sunset_b": (0xA8, 0x4E, 0x52, 255),
    "sunset_c": (0x6E, 0x3F, 0x66, 255),
    "sunset_d": (0x3A, 0x2B, 0x52, 255),
    "st_y":     (0xC9, 0xC0, 0x5F, 255),
    "st_p":     (0xC9, 0x7B, 0xA0, 255),
    "st_c":     (0x5F, 0xB8, 0xCC, 255),
    "vinyl":    (0x14, 0x11, 0x20, 255),
    "cface":    (0xB8, 0xB2, 0xC9, 255),
    "book_r":   (0xA8, 0x4E, 0x52, 255),
    "book_o":   (0xC9, 0x9B, 0x5F, 255),
    "book_g":   (0x5F, 0x8E, 0x5A, 255),
    "book_c":   (0x5F, 0xA8, 0xB8, 255),
    "book_p":   (0x8A, 0x6B, 0xB8, 255),
    "book_y":   (0xC9, 0xC0, 0x5F, 255),
}
C["win_far"] = mix(C["win_lit"], C["city_far"], 0.55)
C["claude_dim"] = mix(C["claude"], C["screen"], 0.45)
C["cloud1"] = mix(C["sky1"], C["star_dim"], 0.16)
C["cloud2"] = mix(C["sky2"], C["star_dim"], 0.16)

buf = [[C["wall"]] * W for _ in range(H)]


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        buf[y][x] = C[c] if isinstance(c, str) else c


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)


def disc(cx, cy, r, c):
    for yy in range(int(cy - r), int(cy + r) + 1):
        for xx in range(int(cx - r), int(cx + r) + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r + r * 0.6:
                px(xx, yy, c)


def tint(x, y, c, t):
    if 0 <= x < W and 0 <= y < H:
        col = C[c] if isinstance(c, str) else c
        buf[y][x] = mix(buf[y][x], col, t)


def tint_rect(x, y, w, h, c, t):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            tint(xx, yy, c, t)


def stamp(x0, y0, art, m):
    lines = art.strip("\n").splitlines()
    wmax = max(map(len, lines))
    for r in lines:
        if len(r) != wmax:
            print(f"warn: stamp row width {len(r)} != {wmax}: {r!r}")
    for dy, row in enumerate(lines):
        for dx, ch in enumerate(row):
            if ch != ".":
                px(x0 + dx, y0 + dy, m[ch])


def hexc(c):
    return "#{:02x}{:02x}{:02x}".format(*(C[c][:3] if isinstance(c, str) else c[:3]))


def hex_at(x, y):
    return "#{:02x}{:02x}{:02x}".format(*buf[y][x][:3])


# ---------------------------------------------------------------- base layers
rect(0, 45, W, 19, "wall_dk")
rect(0, 56, W, 2, "board")
rect(0, 58, W, 6, "floor")
for y in range(58, 64):
    for x in range((y * 7) % 16, W, 16):
        px(x, y, "floor_ln")

# ------------------------------------------------------------------- window
rect(18, 6, 87, 39, "frame")
rect(18, 6, 87, 1, "frame_hi")
for y in range(8, 43):
    band = "sky0" if y <= 15 else ("sky1" if y <= 24 else ("sky2" if y <= 33 else "sky3"))
    rect(20, y, 83, 1, band)
for y, above, below in [(15, "sky0", "sky1"), (24, "sky1", "sky2"), (33, "sky2", "sky3")]:
    for x in range(20, 103):
        if (x + y) % 2:
            px(x, y, below)

# thin clouds
for x in range(28, 40):
    if x % 5 != 2:
        px(x, 13, "cloud1")
for x in range(52, 67):
    if x % 4 != 1:
        px(x, 22, "cloud2")

STARS_BRIGHT = [(26, 11), (38, 9), (58, 13), (70, 10), (98, 11), (30, 21), (66, 19), (94, 22)]
STARS_DIM = [(23, 14), (33, 17), (43, 12), (52, 10), (55, 20), (62, 16), (78, 12),
             (81, 21), (96, 9), (25, 23), (49, 22), (69, 23), (101, 16), (35, 13),
             (60, 9), (88, 24)]
for x, y in STARS_BRIGHT:
    px(x, y, "star")
for x, y in [(38, 9), (94, 22)]:            # cross-shaped sparkles
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        px(x + dx, y + dy, "star_dim")
for x, y in STARS_DIM:
    px(x, y, "star_dim")

# moon with craters and a dithered halo
for r, t in [(6, 0.10), (5, 0.14)]:
    for yy in range(15 - r, 15 + r + 1):
        for xx in range(88 - r, 88 + r + 1):
            d2 = (xx - 88) ** 2 + (yy - 15) ** 2
            if r * r - r < d2 <= r * r + r and (xx + yy) % 2 and 20 <= xx <= 102:
                tint(xx, yy, "moon", t)
disc(88, 15, 4, "moon")
for x, y in [(86, 14), (89, 16), (87, 17)]:
    px(x, y, "moon_sh")
for a in range(-2, 3):                       # shaded lower-right limb
    px(90 - abs(a) // 2, 15 + a + 1, "moon_sh") if a > 0 else None
px(90, 17, "moon_sh")
px(89, 18, "moon_sh")

# city skyline: far layer then near layer, filled down to the sill
for bx, top, bw in [(21, 28, 6), (28, 26, 5), (34, 29, 7), (42, 27, 4), (48, 30, 6),
                    (55, 26, 5), (61, 29, 6), (68, 27, 4), (76, 30, 6), (83, 28, 5),
                    (89, 29, 6), (96, 27, 7)]:
    rect(bx, top, bw, 43 - top, "city_far")
for x, y in [(22, 30), (30, 28), (36, 31), (57, 28), (78, 32), (98, 29)]:
    px(x, y, "win_far")
for bx, top, bw in [(21, 33, 8), (30, 31, 6), (37, 35, 7), (45, 32, 5), (51, 36, 8),
                    (60, 31, 6), (67, 34, 7), (75, 33, 5), (81, 36, 8), (90, 32, 6),
                    (97, 35, 6)]:
    rect(bx, top, bw, 43 - top, "city")
rect(55, 32, 1, 4, "city")                   # antenna masts
rect(85, 31, 1, 5, "city")
CITY_LIT = [(23, 35), (26, 38), (32, 33), (35, 34), (39, 37), (47, 34), (53, 38),
            (56, 37), (63, 33), (70, 36), (77, 35), (83, 38), (92, 34), (99, 37),
            (31, 36), (68, 38)]
for x, y in CITY_LIT:
    px(x, y, "win_lit")

# glass reflections
for i in range(8):
    tint(23 + i, 9 + i, (0xC8, 0xC8, 0xFF, 255), 0.06)
for i in range(6):
    tint(50 + i, 9 + i, (0xC8, 0xC8, 0xFF, 255), 0.05)

# mullions + sill
rect(46, 8, 2, 35, "frame")
rect(74, 8, 2, 35, "frame")
rect(20, 24, 83, 2, "frame")
rect(15, 43, 93, 2, "sill")
rect(15, 43, 93, 1, "frame_hi")

# cactus on the sill
rect(27, 40, 4, 3, "pot_dk")
rect(28, 36, 2, 4, "leaf")
px(30, 37, "leaf")
px(30, 36, "leaf_hi")
px(28, 36, "leaf_hi")

# moonlight pooling on the floor under the window
for y in range(58, 64):
    x0 = 30 - (y - 58) * 2
    for x in range(x0, x0 + 48):
        edge = x < x0 + 3 or x > x0 + 44
        if not edge or (x + y) % 2:
            tint(x, y, "star_dim", 0.10)

# ---------------------------------------------------------- string lights
BULBS = []
for x in range(0, W):
    p = x % 16
    off = 0 if p in (0, 15) else (1 if p in (1, 2, 13, 14) else (2 if p in (3, 4, 11, 12) else 3))
    px(x, 1 + off, "wire")
    if p == 8:
        bc = ["light", "mug", "code_c"][(x // 16) % 3]
        BULBS.append((x, 1 + off + 2, bc))
for x, y, bc in BULBS:
    px(x, y - 1, "wire")
    px(x, y, bc)
    for dx, dy, t in [(-1, 0, 0.22), (1, 0, 0.22), (0, 1, 0.22), (-1, 1, 0.10), (1, 1, 0.10)]:
        tint(x + dx, y + dy, bc, t)

# ----------------------------------------------------------------- left wall
# sunset print
stamp(3, 7, """
fffffffffff
faaaaaaaaaf
faaaaLLaaaf
fbbbbLLbbbf
fbbbbbbbbbf
fcccccccccf
fcccccccccf
fdddddddddf
fdd.d.d.ddf
fdddddddddf
fffffffffff
""", {"f": "poster_f", "a": "sunset_a", "b": "sunset_b", "c": "sunset_c",
      "d": "sunset_d", "L": "light"})

# hanging trailing plant on a bracket shelf
rect(4, 24, 8, 1, "shelf")
rect(6, 22, 4, 2, "pot_dk")
for x, y in [(5, 21), (7, 21), (9, 21), (6, 20), (8, 20), (10, 21)]:
    px(x, y, "leaf")
VINE_L = [(5, 25), (4, 26), (5, 27), (4, 28), (5, 29), (4, 30), (5, 31)]
VINE_R = [(10, 25), (11, 26), (10, 27), (11, 28), (10, 29), (11, 30), (10, 31), (11, 32), (10, 33)]
for i, (x, y) in enumerate(VINE_L + VINE_R):
    px(x, y, "leaf_dk" if i % 2 else "leaf")

# floor speaker
rect(3, 40, 11, 18, "spk")
rect(3, 40, 11, 1, "spk_rim")
rect(3, 40, 1, 18, "spk_rim")
disc(8, 45, 1.6, "spk_cone")
px(8, 45, "spk_dot")
disc(8, 52, 3.2, "spk_rim")
disc(8, 52, 2.4, "spk_cone")
px(8, 52, "spk_dot")

# crate of records under the window
rect(24, 50, 21, 8, "desk_sh")
rect(25, 51, 19, 6, "vinyl")
for i, (vx, vc) in enumerate([(26, "book_r"), (28, "book_o"), (30, "book_g"),
                              (32, "book_c"), (34, "book_p"), (36, "book_y"),
                              (38, "book_r"), (40, "book_c"), (42, "book_p")]):
    rect(vx, 51 + (i % 3), 2, 1, vc)
    rect(vx, 52 + (i % 3), 2, 5 - (i % 3), "vinyl")
disc(49, 54, 3.2, "vinyl")                   # record leaning against the crate
px(49, 54, "mug")

# --------------------------------------------------- cat on a cushion
rect(75, 53, 24, 5, "cushion")
rect(76, 52, 22, 1, "cush_hi")
px(75, 53, "wall_dk")
px(98, 53, "wall_dk")
px(75, 57, "floor")
px(98, 57, "floor")
stamp(79, 44, """
..........d..d.
.........ccccc.
..ccccc..ccccc.
.ccccccccccccc.
ccccccccccdEcc.
ccdccccdcccccc.
ccccccccccccccc
.ccccccccccccc.
""", {"c": "cat", "d": "cat_dk", "E": "cat_dk", "h": "cat_hi"})
px(90, 48, "cat_dk")                          # closed eye
for x, y in [(78, 51), (77, 50), (77, 49)]:   # tail wrapping around the front
    px(x, y, "cat")
px(77, 48, "cat_hi")                          # tail tip (animated)
# moonlight from the window rims the cat's back
cat_cols = {C["cat"], C["cat_dk"]}
for x in range(79, 94):
    for y in range(43, 53):
        if buf[y][x] in cat_cols:
            buf[y][x] = mix(buf[y][x], C["star_dim"], 0.55)
            break

# --------------------------------------------------------- bookcase + clock
rect(108, 16, 15, 41, "case")
rect(108, 16, 15, 1, "case_ln")
rect(108, 16, 1, 41, "case_dk")
rect(122, 16, 1, 41, "case_dk")
for sy in (26, 36, 46):
    rect(109, sy, 13, 1, "case_ln")
for bx, bh, bw, bc in [(110, 7, 2, "book_r"), (112, 8, 1, "book_c"), (113, 6, 2, "book_o"),
                       (115, 8, 2, "book_p"), (117, 7, 1, "book_g"), (118, 8, 2, "book_y"),
                       (120, 6, 2, "book_c")]:
    rect(bx, 26 - bh, bw, bh, bc)
for bx, bh, bw, bc in [(110, 8, 2, "book_g"), (112, 7, 2, "book_y"), (114, 8, 1, "book_r"),
                       (115, 6, 2, "book_c"), (117, 8, 2, "book_o"), (119, 7, 2, "book_p")]:
    rect(bx, 36 - bh, bw, bh, bc)
for bx, bh, bw, bc in [(110, 7, 2, "book_p"), (112, 8, 2, "book_o"), (114, 7, 1, "book_g"),
                       (116, 8, 2, "book_r")]:
    rect(bx, 46 - bh, bw, bh, bc)
for x, y in [(119, 44), (120, 43), (120, 44), (121, 44)]:  # trinket plant
    px(x, y, "leaf")
rect(109, 47, 13, 10, "case_dk")             # cabinet doors
rect(115, 47, 1, 10, "case")
px(113, 51, "case_ln")
px(117, 51, "case_ln")
# radio on top with an antenna
rect(110, 12, 10, 4, "radio")
rect(111, 13, 4, 2, "spk_cone")
px(117, 13, "light")
px(118, 14, "case_ln")
for x, y in [(120, 11), (121, 10), (122, 9)]:
    px(x, y, "wire")
# wall clock
disc(114, 6, 3.4, "wire")
disc(114, 6, 2.2, "cface")
px(114, 5, "case_dk")
px(115, 6, "case_dk")
px(114, 6, "case_dk")

# ---------------------------------------------------------------- desk setup
rect(120, 45, 118, 1, "desk_hi")
rect(120, 46, 118, 1, "desk")
rect(120, 47, 118, 1, "desk_sh")
for x in range(126, 236, 9):
    px(x, 46, "desk_gr")
rect(122, 48, 3, 10, "leg")
rect(232, 48, 3, 10, "leg")

# rug under the desk area
rect(116, 58, 129, 5, "rug")
rect(117, 58, 127, 1, "rug_hi")
rect(117, 62, 127, 1, "rug_hi")
for x in range(126, 240, 14):
    px(x, 60, "rug_hi")

# power socket + cable creeping up to the desk
px(204, 56, "case_ln")
px(205, 56, "case_ln")
for x, y in [(204, 55), (203, 54), (203, 53), (202, 52), (202, 51), (202, 50), (202, 49), (202, 48)]:
    px(x, y, "cable")

# PC tower under the desk (LED animated)
rect(214, 48, 14, 9, "tower")
rect(214, 48, 14, 1, "case_ln")
for vy in (51, 53, 55):
    rect(217, vy, 9, 1, "vent")
px(215, 49, "vent")

# empty office chair, pushed up to the desk (its owner stepped away)
rect(126, 22, 6, 2, "chair")
rect(126, 24, 5, 19, "chair")
rect(126, 26, 1, 15, "chair_dk")
rect(128, 28, 1, 12, "chair_dk")
rect(127, 42, 14, 2, "chair")
rect(127, 44, 14, 1, "chair_dk")
rect(134, 38, 7, 1, "chair_dk")
rect(139, 39, 2, 3, "chair_dk")
rect(133, 48, 3, 6, "chair_dk")
rect(128, 54, 13, 2, "chair")
px(128, 56, "chair_dk")
px(140, 56, "chair_dk")
# screen glow catches the chair's edge
tint_rect(129, 22, 3, 2, "code_c", 0.14)
tint_rect(130, 24, 1, 19, "code_c", 0.18)
tint_rect(138, 42, 3, 2, "code_c", 0.14)

# ------------------------------------------------------- keyboard, mouse
rect(155, 44, 30, 1, "keyb")                 # deskpad
rect(157, 42, 18, 2, "keyb_hi")
for x in range(158, 174, 2):
    px(x, 42, "keyb")
px(180, 43, "keyb_hi")
px(180, 44, "keyb")

# ------------------------------------- the monitor: cmux running Claude
rect(158, 18, 49, 23, "mon")
rect(160, 20, 45, 19, "screen")
rect(160, 20, 45, 2, "titlebar")
px(162, 20, "code_r")
px(164, 20, "code_o")
px(166, 20, "code_g")
rect(172, 20, 12, 1, "comment")              # "cmux" window title
# sidebar: session list, one per workspace
rect(160, 22, 10, 15, "panel")
rect(170, 22, 1, 15, "mon")
rect(160, 26, 10, 1, "titlebar")             # selected session highlight
for dy, (dot, dw) in zip((23, 26, 29, 32), [("code_g", 5), ("claude", 4),
                                            ("code_g", 6), ("comment", 4)]):
    px(161, dy, dot)
    rect(163, dy, dw, 1, "comment")
# pane divider
rect(187, 22, 1, 15, "mon")
# left pane: Claude thinking, prompt box below
rect(172, 23, 8, 1, "comment")
rect(181, 23, 4, 1, "comment")
rect(172, 25, 11, 1, "comment")
rect(172, 27, 6, 1, "code_g")
rect(172, 29, 2, 2, "claude_dim")            # spinner (pulses via overlay)
rect(175, 30, 8, 1, "claude_dim")            # "Thinking…"
rect(172, 33, 13, 3, "comment")              # prompt box
rect(173, 34, 11, 1, "screen")
px(174, 34, "claude")
# right pane: another session applying a diff
rect(189, 23, 9, 1, "comment")
rect(189, 25, 7, 1, "code_g")
rect(189, 26, 9, 1, "code_g")
rect(189, 27, 6, 1, "code_r")
rect(189, 29, 10, 1, "comment")
px(189, 31, "claude")                        # ✻
rect(191, 31, 7, 1, "claude_dim")
px(189, 33, "code_g")                        # ✓ done
rect(191, 33, 6, 1, "comment")
# status bar: coral cmux segment + session dots
rect(160, 37, 45, 2, "status")
rect(160, 37, 8, 2, "claude")
rect(170, 38, 8, 1, "comment")
rect(190, 38, 10, 1, "comment")
px(200, 37, "code_g")
px(202, 37, "claude")
rect(180, 41, 4, 3, "mon")                   # stand
rect(170, 44, 24, 1, "mon")

# sticky notes on the wall right of the monitor
for sx, sy, sc in [(210, 20, "st_y"), (215, 23, "st_p"), (210, 25, "st_c")]:
    rect(sx, sy, 3, 3, sc)
    px(sx + 1, sy + 1, "case_dk")

# --------------------------------------------------------- laptop and mug
rect(212, 32, 15, 9, "laptop")
rect(213, 33, 13, 7, "lap_scr")
for lx, ly, lw in [(214, 34, 6), (214, 36, 8), (214, 38, 5)]:
    rect(lx, ly, lw, 1, "lap_g")
rect(210, 41, 18, 1, "laptop")
rect(209, 42, 20, 1, "laptop")
rect(208, 43, 22, 2, "laptop")
for x in range(211, 227, 2):
    px(x, 43, "keyb")

rect(196, 38, 6, 7, "mug")
rect(196, 38, 1, 7, "mug_hi")
rect(197, 38, 4, 1, "coffee")
px(202, 40, "mug")
px(203, 40, "mug")
px(203, 41, "mug")
px(202, 42, "mug")

# ------------------------------------------------------------------ the lamp
rect(229, 38, 1, 5, "lamp")
px(229, 37, "case_ln")
rect(224, 36, 6, 1, "lamp")
rect(222, 37, 3, 2, "lamp")
px(222, 39, "light")
px(223, 39, "light")
rect(226, 43, 8, 2, "lamp")
tint_rect(214, 45, 22, 1, "light", 0.30)
tint_rect(216, 46, 18, 1, "light", 0.12)
for yy in range(38, 45):                     # cone of lamplight
    half = (44 - yy)
    for xx in range(222 - half, 225 + half):
        if (xx + yy) % 2:
            tint(xx, yy, "light", 0.10)
tint_rect(156, 45, 40, 1, "code_c", 0.10)
tint_rect(150, 24, 8, 20, "code_c", 0.05)    # screen glow spilling on the wall
tint_rect(207, 19, 3, 22, "code_c", 0.05)    # ...and past the monitor's edge

# --------------------------------------------------------- shelf above desk
rect(150, 10, 64, 2, "shelf")
px(152, 12, "leg")
px(211, 12, "leg")
for bx, bh, bw, bc in [(153, 5, 2, "book_r"), (155, 4, 1, "book_c"), (156, 6, 2, "book_o"),
                       (158, 5, 2, "book_p"), (160, 4, 1, "book_g"), (161, 6, 2, "book_y"),
                       (164, 5, 2, "book_c"), (166, 6, 1, "book_r"), (167, 4, 2, "book_g"),
                       (170, 6, 2, "book_p"), (172, 5, 1, "book_o"), (174, 6, 2, "book_c"),
                       (177, 4, 2, "book_y"), (179, 6, 2, "book_r")]:
    rect(bx, 10 - bh, bw, bh, bc)
rect(183, 8, 4, 2, "radio")                  # bookend
for x, y in [(196, 8), (197, 7), (198, 8), (199, 9), (200, 8), (201, 9)]:
    px(x, y, "leaf")
rect(197, 9, 3, 1, "pot_dk")
for i, (x, y) in enumerate([(196, 12), (195, 13), (196, 14), (202, 12), (203, 13)]):
    px(x, y, "leaf_dk" if i % 2 else "leaf")

# --------------------------------------------------------------- right plant
rect(242, 46, 12, 2, "pot")
rect(242, 46, 12, 1, "pot_dk")
rect(243, 48, 10, 6, "pot")
rect(243, 48, 2, 6, "pot_dk")
rect(244, 54, 8, 3, "pot_dk")
rect(244, 47, 8, 1, "soil")
for x, y in [(247, 45), (248, 44), (247, 43), (248, 42), (247, 41), (248, 40),
             (247, 39), (248, 38), (247, 37), (248, 36), (247, 35), (248, 34),
             (247, 33), (248, 32), (247, 31)]:
    px(x, y, "leaf_dk")
LEAVES = [(243, 29), (249, 27), (245, 24), (249, 33), (243, 35), (249, 39), (243, 41)]
for i, (lx, ly) in enumerate(LEAVES):
    stamp(lx, ly, """
.LL.
LLLL
.Lh.
""", {"L": "leaf" if i % 2 else "leaf_hi", "h": "leaf_dk"})

# ------------------------------------------------- shadows, then vignette
for y in range(48, 58):
    for x in range(121, 236):
        tint(x, y, (0x08, 0x06, 0x12, 255), 0.28 if y > 49 else 0.14)
cx, cy = W / 2, H * 0.45
for y in range(H):
    for x in range(W):
        dx = (x - cx) / (W * 0.62)
        dy = (y - cy) / (H * 0.80)
        d = (dx * dx + dy * dy) ** 0.5
        t = (d - 0.62) * 0.55
        if t > 0:
            buf[y][x] = mix(buf[y][x], (0x06, 0x05, 0x0E, 255), min(t, 0.40))


# ------------------------------------------------------------------ png + svg
def png():
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    raw = b"".join(b"\x00" + b"".join(bytes(c) for c in row) for row in buf)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def overlays():
    parts = []

    def r(x, y, color, cls, w=1, h=1, opacity=None):
        op = f' opacity="{opacity}"' if opacity is not None else ""
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" class="{cls}"{op}/>')

    # star twinkle: scene-colored px fades in over a bright star
    for i, (x, y) in enumerate([(26, 11), (58, 13), (98, 11), (30, 21), (66, 19), (94, 22)]):
        r(x, y, hex_at(x, y), f"tw d{i % 5}", opacity=0)
    # red antenna beacons
    for i, (x, y) in enumerate([(55, 31), (85, 30)]):
        r(x, y, hexc("beacon"), f"bcn d{i * 2}", opacity=0)
    # city windows going dark now and then
    for i, (x, y) in enumerate([(32, 33), (70, 36), (99, 37)]):
        r(x, y, hex_at(x, y), f"fl d{i}", opacity=0)
    # string-light bulbs breathing (scene-colored px dims them)
    for i, (x, y, _) in enumerate(BULBS):
        if i % 2 == 0:
            r(x, y, hex_at(x, y), f"bulb d{i % 4}", opacity=0)
    # cursor in the cmux prompt box, and the pulsing Claude spinner
    r(176, 34, hexc("cursor"), "cur")
    r(172, 29, hexc("claude"), "spin", w=2, h=2)
    # a line "printing" on the laptop
    r(214, 38, hexc("lap_g"), "lap", w=5)
    # steam over the mug
    for i, (x, y) in enumerate([(197, 36), (199, 34), (200, 37), (198, 32)]):
        r(x, y, hexc("steam"), f"steam d{i}", opacity=0)
    # music notes drifting from the radio
    for i, (x, y) in enumerate([(113, 9), (117, 11)]):
        parts.append(f'<g class="note d{i * 2}" opacity="0">'
                     f'<rect x="{x}" y="{y}" width="2" height="2" fill="{hexc("star_dim")}"/>'
                     f'<rect x="{x + 2}" y="{y - 2}" width="1" height="3" fill="{hexc("star_dim")}"/></g>')
    # Zzz above the cat
    for i, (x, y) in enumerate([(96, 41), (100, 38)]):
        parts.append(f'<g class="zz d{i * 2 + 1}" opacity="0">'
                     f'<rect x="{x}" y="{y}" width="3" height="1" fill="{hexc("star_dim")}"/>'
                     f'<rect x="{x + 1}" y="{y + 1}" width="1" height="1" fill="{hexc("star_dim")}"/>'
                     f'<rect x="{x}" y="{y + 2}" width="3" height="1" fill="{hexc("star_dim")}"/></g>')
    # PC tower LED breathing
    r(215, 49, hexc("led"), "led", opacity=0)
    # cat tail flick: hide the resting tip, show it one pixel up
    parts.append(f'<g class="tail" opacity="0">'
                 f'<rect x="77" y="48" width="1" height="1" fill="{hex_at(77, 49)}"/>'
                 f'<rect x="77" y="47" width="1" height="1" fill="{hexc("cat_hi")}"/></g>')
    return "\n  ".join(parts)


CSS = """
    .tw{animation:twinkle 3.4s ease-in-out infinite}
    .bcn{animation:beacon 2.6s ease-in-out infinite}
    .fl{animation:flicker 11s steps(1) infinite}
    .bulb{animation:pulse 5s ease-in-out infinite}
    .cur{animation:blink 1.1s steps(1) infinite}
    .spin{animation:breathe 1.6s ease-in-out infinite}
    .lap{animation:flicker 6s steps(1) infinite}
    .steam{animation:rise 3.4s steps(8) infinite}
    .note{animation:floatnote 6s steps(11) infinite}
    .zz{animation:floatnote 7s steps(9) infinite}
    .led{animation:breathe 3.2s ease-in-out infinite}
    .tail{animation:flick 7s steps(1) infinite}
    .d1{animation-delay:.9s}.d2{animation-delay:1.8s}.d3{animation-delay:2.9s}.d4{animation-delay:3.8s}
    @keyframes twinkle{0%,100%{opacity:0}50%{opacity:.95}}
    @keyframes beacon{0%,42%,100%{opacity:0}50%,58%{opacity:.95}}
    @keyframes flicker{0%,88%,96%,100%{opacity:0}92%{opacity:1}}
    @keyframes pulse{0%,100%{opacity:0}50%{opacity:.45}}
    @keyframes blink{0%,55%{opacity:1}56%,100%{opacity:0}}
    @keyframes rise{0%{transform:translateY(0);opacity:0}12%{opacity:.75}100%{transform:translateY(-10px);opacity:0}}
    @keyframes floatnote{0%{transform:translateY(0);opacity:0}15%{opacity:.85}100%{transform:translateY(-12px);opacity:0}}
    @keyframes breathe{0%,100%{opacity:.15}50%{opacity:.9}}
    @keyframes flick{0%,90%,100%{opacity:0}92%,98%{opacity:1}}
    @media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def main():
    b64 = base64.b64encode(png()).decode()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W * SCALE}" height="{H * SCALE}" viewBox="0 0 {W} {H}">
  <title>Quietly coding at night — lofi pixel art</title>
  <style>
    image{{image-rendering:crisp-edges;image-rendering:pixelated}}
    rect{{shape-rendering:crispEdges}}
{CSS}  </style>
  <image href="data:image/png;base64,{b64}" width="{W}" height="{H}"/>
  {overlays()}
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
