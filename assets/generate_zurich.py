#!/usr/bin/env python3
"""Generate assets/zurich-day.svg and assets/zurich-night.svg.

An ultrawide (256x64, rendered 1024x256) pixel-art panorama of Zurich seen
across the Limmat: the left bank with its quay terraces and clock tower,
Fraumünster's needle spire, St. Peter's giant clock, the Münsterbrücke in
the distance, the Grossmünster twin towers, and the lit Limmatquai with its
marina in the foreground. The same scene is drawn twice — a bright daytime
palette for light GitHub themes and a deep night palette for dark themes —
and animated touches are layered on top as CSS-driven SVG rects.

Edit palettes / draw calls and re-run:  python3 assets/generate_zurich.py

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


NIGHT = {
    "sky0": (0x0A, 0x0A, 0x1E), "sky1": (0x10, 0x10, 0x31),
    "sky2": (0x16, 0x17, 0x41), "sky3": (0x1D, 0x1E, 0x4C),
    "star": (0xD9, 0xD7, 0xF2), "star_dim": (0x7B, 0x7C, 0xB0),
    "moon": (0xE8, 0xE0, 0xBC), "moon_sh": (0xC4, 0xB9, 0x8E),
    "hill": (0x11, 0x14, 0x2C),
    "fac_a": (0x2E, 0x29, 0x46), "fac_b": (0x36, 0x30, 0x50),
    "fac_c": (0x40, 0x36, 0x59), "fac_sh": (0x26, 0x22, 0x38),
    "trim": (0x4A, 0x44, 0x68),
    "roof": (0x1E, 0x1E, 0x30), "roof_b": (0x2A, 0x23, 0x38),
    "grossm": (0x52, 0x44, 0x60), "tower": (0x45, 0x3B, 0x54),
    "spire_t": (0x2A, 0x58, 0x50), "spire_t_hi": (0x38, 0x6E, 0x62),
    "spire_r": (0x6E, 0x3A, 0x34),
    "gold": (0xC9, 0xA4, 0x4E), "clockf": (0xE8, 0xDF, 0xC0),
    "hands": (0x2E, 0x2A, 0x20),
    "win": (0x23, 0x23, 0x38), "win_lit": (0xE8, 0xB3, 0x66),
    "lamp_w": (0xFF, 0xE2, 0xA0),
    "tree_c": (0x16, 0x24, 0x1C),
    "tree_a": (0x6A, 0x4C, 0x26), "tree_b": (0x86, 0x62, 0x2F),
    "umb": (0x8A, 0x84, 0x9E),
    "quay": (0x34, 0x34, 0x4C), "quay_hi": (0x45, 0x45, 0x5F),
    "boat": (0x2A, 0x2A, 0x40), "tarp": (0x2E, 0x3A, 0x55),
    "tarp2": (0x3A, 0x46, 0x60), "shed": (0x4A, 0x44, 0x58),
    "shed_r": (0x5A, 0x54, 0x68), "cruise": (0x8A, 0x8A, 0xA0),
    "water0": (0x18, 0x22, 0x38), "water1": (0x0F, 0x17, 0x2C),
    "water2": (0x0A, 0x10, 0x1E),
    "refl_gold": (0xE8, 0xB3, 0x66), "refl_warm": (0xC9, 0x92, 0x4E),
    "refl_red": (0xC9, 0x57, 0x57), "refl_pale": (0xB8, 0xB2, 0xD9),
    "refl_dark": (0x0B, 0x12, 0x26), "refl_teal": (0x2E, 0x5E, 0x56),
    "buoy": (0xFF, 0x5F, 0x5F),
    "vig": (0x05, 0x05, 0x0D),
    "sparkle": (0xF8, 0xFC, 0xFE),
    "cloud": (0x2A, 0x2B, 0x58), "cloud_sh": (0x22, 0x23, 0x4E),
    "sun": (0xE8, 0xE0, 0xBC),
}
DAY = {
    "sky0": (0x6F, 0xA8, 0xD4), "sky1": (0x8C, 0xBE, 0xE2),
    "sky2": (0xA9, 0xD2, 0xEC), "sky3": (0xC9, 0xE6, 0xF5),
    "star": (0xFF, 0xFF, 0xFF), "star_dim": (0xE8, 0xF2, 0xFA),
    "moon": (0xF6, 0xFB, 0xFE), "moon_sh": (0xD6, 0xE9, 0xF4),
    "hill": (0x8A, 0x9E, 0x78),
    "fac_a": (0xE8, 0xDC, 0xC2), "fac_b": (0xDC, 0xC9, 0xA4),
    "fac_c": (0xEA, 0xD8, 0xC8), "fac_sh": (0xC6, 0xB3, 0x93),
    "trim": (0xF4, 0xEE, 0xDE),
    "roof": (0x66, 0x78, 0x8A), "roof_b": (0xA0, 0x64, 0x50),
    "grossm": (0xD9, 0xCC, 0xAE), "tower": (0xCC, 0xC0, 0xA8),
    "spire_t": (0x4F, 0xAE, 0x96), "spire_t_hi": (0x72, 0xC8, 0xB0),
    "spire_r": (0xA0, 0x56, 0x48),
    "gold": (0xC9, 0xA4, 0x4E), "clockf": (0xF6, 0xF0, 0xDC),
    "hands": (0x33, 0x33, 0x33),
    "win": (0x56, 0x62, 0x74), "win_lit": (0x8A, 0xA3, 0xBC),
    "lamp_w": (0x3A, 0x44, 0x48),
    "tree_c": (0x2E, 0x5E, 0x40),
    "tree_a": (0xD9, 0xA6, 0x4E), "tree_b": (0xB8, 0x7F, 0x35),
    "umb": (0xF4, 0xEE, 0xDE),
    "quay": (0xC4, 0xBC, 0xAA), "quay_hi": (0xDC, 0xD5, 0xC2),
    "boat": (0x4A, 0x6E, 0x8A), "tarp": (0x6E, 0x88, 0xA0),
    "tarp2": (0x8A, 0xA3, 0xBC), "shed": (0xF0, 0xEA, 0xD8),
    "shed_r": (0xA0, 0x88, 0x74), "cruise": (0xFA, 0xF7, 0xEE),
    "water0": (0xAE, 0xD4, 0xE2), "water1": (0x8C, 0xB8, 0xCC),
    "water2": (0x70, 0xA0, 0xB6),
    "refl_gold": (0xE8, 0xDC, 0xC2), "refl_warm": (0xDC, 0xC9, 0xA4),
    "refl_red": (0xC9, 0x57, 0x57), "refl_pale": (0xF6, 0xFB, 0xFE),
    "refl_dark": (0x5E, 0x88, 0x9E), "refl_teal": (0x4F, 0xAE, 0x96),
    "buoy": (0xE0, 0x50, 0x50),
    "vig": (0x5E, 0x78, 0x92),
    "sparkle": (0xF8, 0xFC, 0xFE),
    "cloud": (0xF6, 0xFB, 0xFE), "cloud_sh": (0xD6, 0xE9, 0xF4),
    "sun": (0xFF, 0xF4, 0xCE),
}


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
        band = "sky0" if y <= 9 else ("sky1" if y <= 17 else ("sky2" if y <= 25 else "sky3"))
        rect(0, y, W, 1, band)
    for y, below in [(9, "sky1"), (17, "sky2"), (25, "sky3")]:
        for x in range(W):
            if (x + y) % 2:
                px(x, y, below)

    if night:
        for x, y in [(12, 6), (40, 4), (96, 7), (122, 5), (200, 4), (232, 7), (88, 14), (170, 6)]:
            px(x, y, "star")
        for x, y in [(40, 4), (232, 7)]:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                px(x + dx, y + dy, "star_dim")
        for x, y in [(8, 12), (22, 9), (34, 15), (66, 5), (78, 9), (104, 12), (112, 4),
                     (130, 10), (140, 15), (164, 12), (196, 10), (216, 12), (226, 4),
                     (246, 10), (252, 15), (184, 6)]:
            px(x, y, "star_dim")
        for r, t in [(6, 0.10), (5, 0.15)]:      # moon halo
            for yy in range(8 - r, 8 + r + 1):
                for xx in range(150 - r, 150 + r + 1):
                    d2 = (xx - 150) ** 2 + (yy - 8) ** 2
                    if r * r - r < d2 <= r * r + r and (xx + yy) % 2:
                        tint(xx, yy, "moon", t)
        for yy in range(5, 12):
            for xx in range(147, 154):
                if (xx - 150) ** 2 + (yy - 8) ** 2 <= 11:
                    px(xx, yy, "moon")
        px(149, 7, "moon_sh")
        px(151, 9, "moon_sh")
        px(148, 9, "moon_sh")
    else:
        for yy in range(2, 12):                  # sun with a soft halo
            for xx in range(20, 30):
                d2 = (xx - 25) ** 2 + (yy - 7) ** 2
                if d2 <= 8:
                    px(xx, yy, "sun")
                elif d2 <= 20 and (xx + yy) % 2:
                    tint(xx, yy, "sun", 0.30)
        for cx0, cy0, cw in [(56, 5, 16), (138, 8, 20), (214, 4, 14)]:
            rect(cx0 + 2, cy0, cw - 4, 1, "cloud")
            rect(cx0 + 5, cy0 - 1, cw - 10, 1, "cloud")
            rect(cx0, cy0 + 1, cw, 1, "cloud_sh")

    # wooded hill peeking out on the far right
    for x in range(236, 256):
        top = 17 + ((x * 3) // 7) % 3
        rect(x, top, 1, 24 - top, "hill")

    # ------------------------------------------------- left bank buildings
    rect(0, 15, 25, 3, "roof")
    rect(0, 18, 25, 22, "fac_a")
    for wy in (21, 25, 29):
        for wx in range(2, 23, 4):
            rect(wx, wy, 1, 2, "win_lit" if night and (wx + wy) % 3 == 0 else "win")
    if night:                                    # quay-side restaurants aglow
        for wx in range(2, 23, 5):
            rect(wx, 35, 3, 3, "win_lit")
    else:
        for wx in range(2, 23, 5):
            rect(wx, 35, 3, 3, "fac_sh")

    # squat clock tower
    rect(26, 12, 11, 28, "fac_b")
    rect(26, 12, 11, 1, "trim")
    rect(28, 8, 7, 4, "roof_b")
    px(31, 7, "roof_b")
    rect(29, 14, 5, 5, "fac_sh")
    rect(30, 15, 3, 3, "clockf")
    px(31, 16, "hands")
    px(31, 15, "hands")
    for wy in (22, 27, 32):
        for wx in (28, 31, 34):
            rect(wx, wy, 1, 2, "win_lit" if night and wy == 27 else "win")

    # gabled house
    rect(38, 18, 11, 22, "fac_c")
    for i, gw in enumerate([9, 7, 5, 3, 1]):
        rect(43 - gw // 2, 17 - i, gw, 1, "roof_b")
    for wy in (22, 26, 30, 34):
        for wx in (40, 43, 46):
            rect(wx, wy, 1, 2, "win_lit" if night and (wx * wy) % 5 == 0 else "win")

    # Fraumünster: tower, needle spire, nave
    rect(52, 16, 9, 24, "tower")
    rect(53, 17, 7, 4, "spire_t")
    rect(54, 22, 5, 4, "fac_sh")
    rect(55, 23, 3, 3, "gold" if night else "clockf")
    px(56, 24, "hands")
    for i, sw in enumerate([7, 5, 5, 3, 3]):
        rect(56 - sw // 2, 15 - i, sw, 1, "spire_t")
        if sw >= 5:
            px(56 - sw // 2, 15 - i, "spire_t_hi")
    rect(56, 3, 1, 8, "spire_t")                 # the needle
    px(56, 2, "gold")
    rect(50, 28, 16, 4, "roof")
    rect(48, 32, 18, 8, "fac_b")
    for wx in (50, 54, 62):
        rect(wx, 34, 1, 3, "win")

    # St. Peter: broad tower, giant clock, steep spire
    rect(68, 12, 11, 20, "fac_a")
    rect(68, 12, 11, 1, "trim")
    rect(70, 14, 7, 7, "fac_sh")
    rect(71, 15, 5, 5, "clockf")
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        px(73 + dx, 17 + dy, "gold")
    rect(73, 16, 1, 2, "hands")
    rect(73, 17, 2, 1, "hands")
    for i, sw in enumerate([11, 9, 7, 5, 3, 3, 1, 1]):
        rect(73 - sw // 2, 11 - i, sw, 1, "roof")
    px(73, 3, "gold")
    for wx in (70, 73, 76):
        rect(wx, 24, 1, 3, "win")
    rect(64, 30, 22, 10, "fac_a")
    rect(64, 28, 22, 2, "roof")
    for wx in range(66, 84, 4):
        rect(wx, 33, 1, 3, "win_lit" if night and wx % 3 == 0 else "win")

    # --------------------------------- distant Limmatquai row + bridge
    seed = 0
    x = 86
    for fw, fc, rh in [(9, "fac_b", 3), (7, "fac_c", 2), (10, "fac_a", 3), (8, "fac_b", 2),
                       (9, "fac_c", 3), (7, "fac_a", 2), (10, "fac_b", 3), (9, "fac_c", 2),
                       (9, "fac_a", 3), (8, "fac_b", 2)]:
        rect(x, 26, fw, 10, fc)
        rect(x, 26 - rh, fw, rh, "roof" if seed % 2 else "roof_b")
        for wx in range(x + 1, x + fw - 1, 3):
            px(wx, 29, "win_lit" if night and (wx + seed) % 2 else "win")
            px(wx, 32, "win_lit" if night and (wx + seed) % 3 == 0 else "win")
        seed += 1
        x += fw
    # Münsterbrücke: low deck, balustrade, arches, lamps
    rect(88, 36, 84, 2, "quay")
    rect(88, 35, 84, 1, "quay_hi")
    for ax in range(92, 168, 12):
        rect(ax, 38, 8, 3, "fac_sh")
        rect(ax + 1, 39, 6, 2, "water0" if night else "water1")
        rect(ax + 2, 38, 4, 1, "water0" if night else "water1")
        tint(ax + 4, 39, "sky3", 0.3)
    for lx in range(94, 168, 10):
        px(lx, 34, "lamp_w")
        px(lx, 33, "lamp_w")
        if night:
            tint(lx - 1, 33, "lamp_w", 0.3)
            tint(lx + 1, 33, "lamp_w", 0.3)
            tint(lx, 32, "lamp_w", 0.2)

    # riverside conifer + Wasserkirche
    for i, tw in enumerate([3, 5, 7, 7, 9, 9, 11, 11, 11, 9, 9]):
        rect(153 - tw // 2, 21 + i, tw, 1, "tree_c")
    rect(152, 32, 3, 8, "tree_c")
    rect(160, 26, 12, 14, "fac_a")
    rect(160, 24, 12, 2, "roof")
    rect(163, 18, 3, 4, "fac_a")
    for i, sw in enumerate([3, 1]):
        rect(164 - sw // 2, 17 - i, sw, 1, "roof")
    for wx in (162, 166, 169):
        rect(wx, 29, 1, 4, "win")

    # ------------------------------------------- Grossmünster twin towers
    for tx in (176, 186):
        rect(tx, 14, 7, 22, "grossm")
        rect(tx, 14, 1, 22, "fac_sh")
        for wy in (17, 22, 27):
            rect(tx + 2, wy, 1, 3, "win")
            rect(tx + 4, wy, 1, 3, "win")
        for i, dw in enumerate([7, 7, 5, 3, 1]):
            rect(tx + 3 - dw // 2, 13 - i, dw, 1, "roof")
        px(tx + 3, 8, "gold")
        if night:                                # floodlighting
            for yy in range(14, 34):
                tint(tx + 3, yy, "win_lit", 0.10)
                tint(tx + 5, yy, "win_lit", 0.07)
    rect(183, 24, 3, 12, "grossm")
    rect(172, 30, 26, 10, "fac_b")
    rect(172, 28, 26, 2, "roof")

    # ------------------------------------------------- right bank facades
    x = 198
    for fw, fc, top in [(8, "fac_a", 22), (7, "fac_c", 20), (9, "fac_b", 23),
                        (8, "fac_a", 21), (9, "fac_c", 22), (8, "fac_b", 20),
                        (9, "fac_a", 22)]:
        rect(x, top, fw, 40 - top, fc)
        rect(x, top - 2, fw, 2, "roof" if x % 2 else "roof_b")
        for wy in range(top + 3, 36, 4):
            for wx in range(x + 1, x + fw - 1, 3):
                px(wx, wy, "win_lit" if night and (wx + wy) % 2 else "win")
        x += fw
    # red spire (Predigerkirche) behind the row
    rect(208, 12, 3, 8, "fac_a")
    for i, sw in enumerate([5, 3, 3, 1, 1]):
        rect(209 - sw // 2, 11 - i, sw, 1, "spire_r")
    px(209, 6, "gold")
    # bright shore lights + autumn trees along the quay
    if night:
        for lx in range(200, 254, 7):
            px(lx, 31, "lamp_w")
            tint(lx - 1, 31, "lamp_w", 0.35)
            tint(lx + 1, 31, "lamp_w", 0.35)
            tint(lx, 30, "lamp_w", 0.25)
        for wx in range(199, 253, 4):
            rect(wx, 35, 2, 3, "win_lit")
    for cx0, cw in [(200, 10), (216, 12), (234, 10)]:
        for x in range(cx0, cx0 + cw):
            top = 30 + ((x * 5) // 3) % 3
            for y in range(top, 36 - (1 if x % 4 == 0 else 0)):
                px(x, y, "tree_a" if (x + y) % 2 else "tree_b")
        rect(cx0 + cw // 2, 36, 1, 4, "shed_r" if not night else "fac_sh")

    # ------------------------------------------------------------- water
    for y in range(41, H):
        band = "water0" if y <= 47 else ("water1" if y <= 55 else "water2")
        rect(0, y, W, 1, band)
    for y, below in [(47, "water1"), (55, "water2")]:
        for x in range(W):
            if (x + y) % 2:
                px(x, y, below)
    for y in range(41, 52):                      # sky glow mirrored mid-river
        for x in range(90, 150):
            if (x + y) % 2:
                tint(x, y, "sky3", max(0.0, 0.25 - (y - 41) * 0.02))

    # quay walls: left bank and the right bank / Limmatquai tip
    rect(0, 40, 88, 4, "quay")
    rect(0, 40, 88, 1, "quay_hi")
    rect(146, 40, 110, 4, "quay")
    rect(146, 40, 110, 1, "quay_hi")

    # terrace umbrellas + moored boats along the left quay
    for ux in (8, 16, 24):
        rect(ux - 2, 36, 5, 1, "umb")
        rect(ux - 1, 35, 3, 1, "umb")
        rect(ux, 37, 1, 3, "fac_sh")
    for bx, bw in [(28, 7), (37, 6), (45, 7)]:
        rect(bx, 45, bw, 2, "boat")
        rect(bx + 1, 44, bw - 2, 1, "tarp")

    # -------------------------------------------------------- reflections
    def streak(x, y0, y1, c, t):
        for y in range(y0, min(y1, H)):
            if (x + (y // 3) % 2 + y) % 2 == 0:
                tint(x + (y // 4) % 2, y, c, t)

    for x0, x1, ln in [(0, 26, 8), (50, 84, 7), (176, 194, 7)]:
        for x in range(x0, x1, 2):
            streak(x, 44, 44 + ln + (x % 3), "refl_dark", 0.35 if night else 0.20)
    for x in range(88, 146, 2):                  # bridge & quai silhouettes
        streak(x, 42, 47 + (x % 3), "refl_dark", 0.30 if night else 0.15)
    for x in (55, 56, 57):
        streak(x, 44, 54, "refl_teal", 0.30)
    if night:
        for lx in range(94, 146, 10):            # bridge lamps
            streak(lx, 42, 54, "refl_gold", 0.45)
        for lx in range(200, 254, 7):            # blazing right bank
            streak(lx, 44, 60, "refl_gold", 0.50)
            streak(lx + 1, 44, 52, "refl_warm", 0.30)
        for lx in (6, 12, 18):                   # left restaurants
            streak(lx, 45, 54, "refl_warm", 0.35)
        for x in (149, 150, 151):                # moon glint
            streak(x, 44, 52, "refl_pale", 0.30)
        for tx in (179, 189):                    # floodlit Grossmünster
            streak(tx, 44, 50, "refl_warm", 0.25)
    else:
        for lx in range(200, 254, 9):
            streak(lx, 44, 54, "refl_warm", 0.25)
        for lx in range(94, 146, 14):
            streak(lx, 42, 50, "refl_pale", 0.20)
    if not night:
        px(120, 46, "buoy")                      # buoy (blinks at night)
    streak(120, 47, 52, "refl_red", 0.35 if night else 0.30)

    # --------------------------------------------- foreground marina (right)
    rect(168, 46, 26, 2, "cruise")               # river cruise boat
    rect(170, 44, 20, 2, "cruise")
    rect(167, 47, 1, 1, "cruise")
    for wx in range(172, 189, 3):
        px(wx, 45, "win_lit" if night else "win")
    rect(168, 48, 26, 1, "refl_dark" if night else "fac_sh")
    for sx in (224, 236):                        # boat sheds
        rect(sx, 43, 9, 5, "shed")
        rect(sx - 1, 42, 11, 1, "shed_r")
        rect(sx + 3, 45, 2, 3, "win_lit" if night else "win")
    rect(198, 52, 58, 1, "quay_hi" if night else "quay")
    rect(210, 57, 46, 1, "quay_hi" if night else "quay")
    for bx, bw, tc in [(198, 8, "tarp"), (208, 7, "tarp2"), (217, 6, "tarp"),
                       (226, 8, "tarp2"), (236, 7, "tarp"), (245, 8, "tarp2")]:
        rect(bx, 49, bw, 2, "boat")
        rect(bx + 1, 48, bw - 2, 1, tc)
    for bx, bw, tc in [(214, 12, "tarp2"), (230, 10, "tarp"), (244, 11, "tarp2")]:
        rect(bx, 53, bw, 3, "boat")
        rect(bx + 1, 52, bw - 2, 1, tc)
    for mx in (220, 240):                        # masts with tip lights
        rect(mx, 44, 1, 8, "quay_hi" if night else "fac_sh")
        px(mx, 43, "lamp_w" if night else "fac_sh")
    if not night:                                # swans on calm water
        for sx, sy in [(102, 52), (134, 55)]:
            px(sx, sy, "cloud")
            px(sx + 1, sy, "cloud")
            px(sx + 1, sy - 1, "cloud")

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
        for i, (x, y) in enumerate([(12, 6), (96, 7), (200, 4), (88, 14), (122, 5), (232, 7)]):
            orect(x, y, hex_at(x, y), f"tw d{i % 5}", opacity=0)
        orect(120, 46, hexc("buoy"), "bcn", opacity=0)            # buoy blink
        orect(120, 48, hexc("refl_red"), "bcn d2", opacity=0)
        for i, lx in enumerate((114, 214, 235)):                  # lamp halos
            orect(lx, 33 if lx < 170 else 31, hexc("lamp_w"), f"bulb d{i}", opacity=0)
        for i, (x, y) in enumerate([(7, 35), (219, 35), (243, 35)]):
            orect(x, y, hex_at(x, y), f"fl d{i}", opacity=0)      # windows off
        for i, (x, y) in enumerate([(94, 46), (204, 50), (228, 47), (150, 46), (120, 50)]):
            orect(x, y, hexc("refl_gold"), f"shim d{i % 4}", opacity=0)
        orect(178, 45, hexc("win_lit"), "fl d3", opacity=0)       # cruise cabin
    else:
        for i, (x, y) in enumerate([(70, 8), (110, 5), (186, 7)]):
            parts.append(f'<g class="fly d{i * 2}" opacity="0">'
                         f'<rect x="{x}" y="{y}" width="1" height="1" fill="{hexc("lamp_w")}"/>'
                         f'<rect x="{x + 1}" y="{y + 1}" width="1" height="1" fill="{hexc("lamp_w")}"/>'
                         f'<rect x="{x + 2}" y="{y}" width="1" height="1" fill="{hexc("lamp_w")}"/></g>')
        parts.append(f'<g class="drift" opacity="0">'
                     f'<rect x="176" y="12" width="10" height="1" fill="{hexc("cloud")}"/>'
                     f'<rect x="178" y="11" width="5" height="1" fill="{hexc("cloud")}"/></g>')
        for i, (x, y) in enumerate([(100, 44), (140, 48), (180, 53), (60, 50), (220, 58), (30, 46)]):
            orect(x, y, hexc("sparkle"), f"tw d{i % 5}", opacity=0)
        parts.append(f'<g class="glide" opacity="0">'
                     f'<rect x="88" y="57" width="2" height="1" fill="{hexc("cloud")}"/>'
                     f'<rect x="89" y="56" width="1" height="1" fill="{hexc("cloud")}"/></g>')

    css = """
    .tw{animation:twinkle 3.4s ease-in-out infinite}
    .bcn{animation:beacon 2.4s steps(1) infinite}
    .fl{animation:flicker 11s steps(1) infinite}
    .bulb{animation:pulse 5s ease-in-out infinite}
    .shim{animation:twinkle 2.6s ease-in-out infinite}
    .fly{animation:fly 26s steps(48) infinite}
    .drift{animation:drift 70s steps(40) infinite}
    .glide{animation:glide 34s steps(56) infinite}
    .d1{animation-delay:.9s}.d2{animation-delay:1.8s}.d3{animation-delay:2.9s}.d4{animation-delay:3.8s}
    @keyframes twinkle{0%,100%{opacity:0}50%{opacity:.95}}
    @keyframes beacon{0%,45%,100%{opacity:0}50%,90%{opacity:.95}}
    @keyframes flicker{0%,88%,96%,100%{opacity:0}92%{opacity:1}}
    @keyframes pulse{0%,100%{opacity:0}50%{opacity:.5}}
    @keyframes fly{0%{transform:translate(0,0);opacity:0}6%{opacity:.8}94%{opacity:.8}100%{transform:translate(-48px,2px);opacity:0}}
    @keyframes drift{0%{transform:translateX(0);opacity:0}6%{opacity:.9}94%{opacity:.9}100%{transform:translateX(-40px);opacity:0}}
    @keyframes glide{0%{transform:translateX(0);opacity:0}8%{opacity:.9}92%{opacity:.9}100%{transform:translateX(56px);opacity:0}}
    @media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
    title = ("Zurich by night — lofi pixel art" if night
             else "Zurich by day — lofi pixel art")
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
        out = HERE / f"zurich-{mode}.svg"
        svg = build(night)
        out.write_text(svg)
        print(f"wrote {out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
