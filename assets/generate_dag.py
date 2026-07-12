#!/usr/bin/env python3
"""Generate dag-light.svg / dag-dark.svg — an animated DAG showing a
computation flowing from sources to sink.

Self-contained SVGs animated with pure CSS (works inside GitHub's <img>
proxy, honors prefers-reduced-motion). Pulses travel along edges at
constant speed; a node activates when its last input arrives, stays lit
while the computation completes, then everything fades back to idle.
"""

import math
import os

W, H = 1024, 256
R = 9            # node radius
R_SINK = 12
GAP = 4          # gap between node rim and edge endpoint
SPEED = 300.0    # pulse speed, viewBox px/s
PROC = 0.22      # per-node processing delay before emitting
FLASH = 0.12     # activation flash duration
SETTLE = 0.30    # flash -> steady lit
RIPPLE = 0.7     # ripple ring lifetime
HOLD = 1.3       # steady-lit time after the sink activates
FADE = 0.8       # global fade back to idle
REST = 0.6       # idle time before the cycle restarts

NODES = [
    (55, 80), (55, 176),                    # 0-1 sources
    (190, 48), (190, 128), (190, 208),      # 2-4
    (330, 88), (330, 168),                  # 5-6
    (470, 40), (470, 128), (470, 216),      # 7-9
    (610, 80), (610, 176),                  # 10-11
    (750, 48), (750, 128), (750, 208),      # 12-14
    (940, 128),                             # 15 sink
]
SINK = 15
SOURCES = {0: 0.0, 1: 0.3}

EDGES = [
    (0, 2), (0, 3), (1, 3), (1, 4),
    (2, 5), (3, 5), (3, 6), (4, 6),
    (2, 7), (5, 7), (5, 8), (6, 8), (6, 9), (4, 9),
    (7, 10), (8, 10), (8, 11), (9, 11),
    (10, 12), (10, 13), (11, 13), (11, 14),
    (7, 12), (9, 14),
    (12, 15), (13, 15), (14, 15),
]

THEMES = {
    "light": dict(
        base="#8a95a3",    # idle node ring
        edge="#b9c2ce",    # edge lines
        accent="#d97757",  # pulses + activation flash
        lit="#c9633f",     # steady lit ring
        hi=0.45, lo=0.14,  # disc opacity: flash, steady
    ),
    "dark": dict(
        base="#6b7684",
        edge="#3a434f",
        accent="#e08a63",
        lit="#d97757",
        hi=0.6, lo=0.3,
    ),
}


def radius(n):
    return R_SINK if n == SINK else R


def geometry():
    """Trimmed edge segments: (x0, y0, dx, dy, length)."""
    segs = []
    for a, b in EDGES:
        ax, ay = NODES[a]
        bx, by = NODES[b]
        d = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / d, (by - ay) / d
        ta, tb = radius(a) + GAP, radius(b) + GAP
        x0, y0 = ax + ux * ta, ay + uy * ta
        x1, y1 = bx - ux * tb, by - uy * tb
        segs.append((x0, y0, x1 - x0, y1 - y0, d - ta - tb))
    return segs


def schedule(segs):
    """Activation time per node, (depart, arrive) per edge."""
    act = dict(SOURCES)
    order = sorted(range(len(NODES)), key=lambda n: NODES[n][0])
    times = [None] * len(EDGES)
    for n in order:
        if n not in act:
            act[n] = max(t[1] for e, t in zip(EDGES, times) if t and e[1] == n)
        for i, (a, b) in enumerate(EDGES):
            if a == n:
                dep = act[n] + PROC
                times[i] = (dep, dep + segs[i][4] / SPEED)
    return act, times


def build(theme):
    c = THEMES[theme]
    segs = geometry()
    act, times = schedule(segs)
    t_end = act[SINK] + HOLD          # global fade start
    T = t_end + FADE + REST           # cycle length

    def pct(t):
        return f"{t / T * 100:.3f}%"

    css = [
        f".ring{{fill:none;stroke:{c['base']};stroke-width:2}}",
        f".edge{{stroke:{c['edge']};stroke-width:1.6;stroke-linecap:round}}",
        ".pulse{opacity:0}",
        ".disc{opacity:0}",
        ".ripl{opacity:0;transform-box:fill-box;transform-origin:center}",
        "@media (prefers-reduced-motion: reduce){*{animation:none !important}}",
    ]
    anim = []

    # pulses
    for i, (x0, y0, dx, dy, _) in enumerate(segs):
        dep, arr = times[i]
        css.append(f".p{i}{{animation:p{i} {T:.3f}s linear infinite}}")
        anim.append(
            f"@keyframes p{i}{{"
            f"0%,{pct(dep)}{{transform:translate(0,0);opacity:0}}"
            f"{pct(dep + 0.06)}{{opacity:1}}"
            f"{pct(arr - 0.06)}{{opacity:1}}"
            f"{pct(arr)},100%{{transform:translate({dx:.1f}px,{dy:.1f}px);opacity:0}}"
            f"}}"
        )

    # node activation: ring color, inner disc, ripple
    for n in range(len(NODES)):
        t = act[n]
        css.append(
            f".r{n}{{animation:r{n} {T:.3f}s linear infinite}}"
            f".d{n}{{animation:d{n} {T:.3f}s linear infinite}}"
            f".w{n}{{animation:w{n} {T:.3f}s linear infinite}}"
        )
        anim.append(
            f"@keyframes r{n}{{"
            f"0%,{pct(t)}{{stroke:{c['base']}}}"
            f"{pct(t + FLASH)}{{stroke:{c['accent']}}}"
            f"{pct(t + FLASH + SETTLE)},{pct(t_end)}{{stroke:{c['lit']}}}"
            f"{pct(t_end + FADE)},100%{{stroke:{c['base']}}}"
            f"}}"
        )
        hi, lo = (c["hi"], c["lo"])
        if n == SINK:
            hi, lo = min(hi + 0.1, 1), lo + 0.1
        anim.append(
            f"@keyframes d{n}{{"
            f"0%,{pct(t)}{{opacity:0}}"
            f"{pct(t + FLASH)}{{opacity:{hi}}}"
            f"{pct(t + FLASH + SETTLE)},{pct(t_end)}{{opacity:{lo}}}"
            f"{pct(t_end + FADE)},100%{{opacity:0}}"
            f"}}"
        )
        sc = 2.8 if n == SINK else 2.3
        anim.append(
            f"@keyframes w{n}{{"
            f"0%,{pct(max(t - 0.001, 0))}{{transform:scale(1);opacity:0}}"
            f"{pct(t + 0.05)}{{opacity:.5}}"
            f"{pct(t + RIPPLE)},100%{{transform:scale({sc});opacity:0}}"
            f"}}"
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="Animated directed acyclic graph: a computation flows from two source nodes through the graph to a single sink">',
        f"<style>{''.join(css)}{''.join(anim)}</style>",
    ]

    for i, (x0, y0, dx, dy, _) in enumerate(segs):
        parts.append(
            f'<line class="edge" x1="{x0:.1f}" y1="{y0:.1f}" '
            f'x2="{x0 + dx:.1f}" y2="{y0 + dy:.1f}"/>'
        )

    for i, (x0, y0, _, _, _) in enumerate(segs):
        parts.append(
            f'<g class="pulse p{i}">'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="6.5" fill="{c["accent"]}" fill-opacity=".22"/>'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="3.2" fill="{c["accent"]}"/>'
            f"</g>"
        )

    for n, (x, y) in enumerate(NODES):
        r = radius(n)
        parts.append(
            f'<circle class="ripl w{n}" cx="{x}" cy="{y}" r="{r}" '
            f'fill="none" stroke="{c["accent"]}" stroke-width="1.5"/>'
            f'<circle class="disc d{n}" cx="{x}" cy="{y}" r="{r - 3}" fill="{c["accent"]}"/>'
            f'<circle class="ring r{n}" cx="{x}" cy="{y}" r="{r}"/>'
        )

    parts.append("</svg>")
    return "".join(parts)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for theme in THEMES:
        path = os.path.join(here, f"dag-{theme}.svg")
        svg = build(theme)
        with open(path, "w") as f:
            f.write(svg)
        print(f"{path}: {len(svg)} bytes")


if __name__ == "__main__":
    main()
