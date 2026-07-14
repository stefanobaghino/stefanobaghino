#!/usr/bin/env python3
"""Generate dag-light.svg / dag-dark.svg — an animated DAG showing a
computation flowing from sources to sink.

Self-contained SVGs animated with pure CSS (works inside GitHub's <img>
proxy, honors prefers-reduced-motion). Pulses travel along edges at
constant speed; a node activates when its last input arrives, stays lit
while the computation completes, then everything fades back to idle.

The graph is grown from a seeded RNG: quasi-layers with jittered
positions and radii, 1-3 parents per node, occasional layer-skipping
edges, all subject to a node-clearance check so no edge grazes an
unrelated node. Accents are sampled from a three-stop gradient by
horizontal position, so the wave shifts hue as it advances.
"""

import math
import os
import random

PHI = (1 + math.sqrt(5)) / 2
W = 1024
H = round(W / PHI)
GAP = 4          # gap between node rim and edge endpoint
SPEED = 340.0    # pulse speed, viewBox px/s
PROC = 0.18      # per-node processing delay before emitting
FLASH = 0.12     # activation flash duration
SETTLE = 0.30    # flash -> steady lit
RIPPLE = 0.7     # ripple ring lifetime
HOLD = 1.3       # steady-lit time after the sink activates
FADE = 0.8       # global fade back to idle
REST = 0.6       # idle time before the cycle restarts

LAYER_X = [55, 162, 280, 395, 508, 624, 740, 854, 965]
LAYER_N = [3, 4, 5, 5, 4, 5, 4, 3, 1]
Y0, Y1 = 48, H - 48

THEMES = {
    "light": dict(
        base="#8a95a3",    # idle node ring
        edge="#b9c2ce",    # edge lines
        stops=["#0969da", "#8250df", "#bf3989"],  # accent gradient
        hi=0.45, lo=0.14,  # disc opacity: flash, steady
    ),
    "dark": dict(
        base="#6b7684",
        edge="#3a434f",
        stops=["#58a6ff", "#a371f7", "#f778ba"],
        hi=0.6, lo=0.36,
    ),
}


def make_graph(rng):
    nodes, radii, layers = [], [], []
    last = len(LAYER_X) - 1
    for li, (bx, cnt) in enumerate(zip(LAYER_X, LAYER_N)):
        idxs = []
        slot = (Y1 - Y0) / cnt
        for k in range(cnt):
            if li == last:
                x, y, r = bx, (Y0 + Y1) / 2, 13.0
            else:
                jx = 6 if li == 0 else 24
                x = bx + rng.uniform(-jx, jx)
                y = Y0 + slot * (k + 0.5) + rng.uniform(-0.32, 0.32) * slot
                r = rng.uniform(7.2, 10.8)
            idxs.append(len(nodes))
            nodes.append((x, y))
            radii.append(r)
        layers.append(idxs)

    def clear_ok(a, b, margin=19):
        ax, ay = nodes[a]
        bx, by = nodes[b]
        for j, (px, py) in enumerate(nodes):
            if j in (a, b):
                continue
            t = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / (
                (bx - ax) ** 2 + (by - ay) ** 2
            )
            if 0 < t < 1:
                if math.hypot(ax + t * (bx - ax) - px, ay + t * (by - ay) - py) < margin:
                    return False
        return True

    edges = set()
    for li in range(len(layers) - 1):
        cur, nxt = layers[li], layers[li + 1]
        for c in nxt:
            cands = sorted(cur, key=lambda p: abs(nodes[p][1] - nodes[c][1]))
            p0 = next((p for p in cands if clear_ok(p, c)), cands[0])
            edges.add((p0, c))
            for p in cands[1:3]:
                if (
                    rng.random() < 0.4
                    and sum(1 for e in edges if e[1] == c) < 3
                    and clear_ok(p, c)
                ):
                    edges.add((p, c))
        for p in cur:
            if not any(e[0] == p for e in edges):
                c = min(nxt, key=lambda q: abs(nodes[q][1] - nodes[p][1]))
                edges.add((p, c))
    for li in range(len(layers) - 2):
        for _ in range(3):
            p = rng.choice(layers[li])
            c = rng.choice(layers[li + 2])
            if (
                rng.random() < 0.5
                and abs(nodes[p][1] - nodes[c][1]) < 140
                and clear_ok(p, c)
            ):
                edges.add((p, c))

    return nodes, radii, layers, sorted(edges)


def _crossings(nodes, edges):
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 0) - (v < 0)

    count = 0
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1:]:
            if len({a, b, c, d}) < 4:
                continue
            p1, p2, p3, p4 = nodes[a], nodes[b], nodes[c], nodes[d]
            if (
                orient(p1, p2, p3) != orient(p1, p2, p4)
                and orient(p3, p4, p1) != orient(p3, p4, p2)
            ):
                count += 1
    return count


def _min_dist(nodes):
    return min(
        math.hypot(ax - bx, ay - by)
        for i, (ax, ay) in enumerate(nodes)
        for bx, by in nodes[i + 1:]
    )


def pick_graph():
    """Search seeds for a well-separated layout with few edge crossings."""
    best = None
    for seed in range(200):
        g = make_graph(random.Random(seed))
        nodes, _, _, edges = g
        if _min_dist(nodes) < 36:
            continue
        score = _crossings(nodes, edges)
        if best is None or score < best[0]:
            best = (score, seed, g)
    return best


_SCORE, _SEED, (NODES, RADII, LAYERS, EDGES) = pick_graph()
SINK = LAYERS[-1][0]
SOURCES = {n: 0.25 * i for i, n in enumerate(LAYERS[0])}


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def grad(stops, t):
    t = min(max(t, 0), 1) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    a, b = hexrgb(stops[i]), hexrgb(stops[i + 1])
    f = t - i
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def accent_at(stops, x):
    return grad(stops, (x - LAYER_X[0]) / (LAYER_X[-1] - LAYER_X[0]))


def geometry():
    """Trimmed edge segments: (x0, y0, dx, dy, length)."""
    segs = []
    for a, b in EDGES:
        ax, ay = NODES[a]
        bx, by = NODES[b]
        d = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / d, (by - ay) / d
        ta, tb = RADII[a] + GAP, RADII[b] + GAP
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
        acc = accent_at(c["stops"], NODES[n][0])
        css.append(
            f".r{n}{{animation:r{n} {T:.3f}s linear infinite}}"
            f".d{n}{{animation:d{n} {T:.3f}s linear infinite}}"
            f".w{n}{{animation:w{n} {T:.3f}s linear infinite}}"
        )
        anim.append(
            f"@keyframes r{n}{{"
            f"0%,{pct(t)}{{stroke:{c['base']}}}"
            f"{pct(t + FLASH)},{pct(t_end)}{{stroke:{acc}}}"
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
        f'aria-label="Animated directed acyclic graph: a computation flows from three source nodes through an uneven graph to a single sink">',
        f"<style>{''.join(css)}{''.join(anim)}</style>",
    ]

    for i, (x0, y0, dx, dy, _) in enumerate(segs):
        parts.append(
            f'<line class="edge" x1="{x0:.1f}" y1="{y0:.1f}" '
            f'x2="{x0 + dx:.1f}" y2="{y0 + dy:.1f}"/>'
        )

    for i, (x0, y0, dx, dy, _) in enumerate(segs):
        mid = accent_at(c["stops"], NODES[EDGES[i][0]][0] + dx / 2)
        parts.append(
            f'<g class="pulse p{i}">'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="6.5" fill="{mid}" fill-opacity=".22"/>'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="3.2" fill="{mid}"/>'
            f"</g>"
        )

    for n, (x, y) in enumerate(NODES):
        r = RADII[n]
        acc = accent_at(c["stops"], x)
        parts.append(
            f'<circle class="ripl w{n}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
            f'fill="none" stroke="{acc}" stroke-width="1.5"/>'
            f'<circle class="disc d{n}" cx="{x:.1f}" cy="{y:.1f}" r="{r - 3:.1f}" fill="{acc}"/>'
            f'<circle class="ring r{n}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
        )

    parts.append("</svg>")
    return "".join(parts)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    segs = geometry()
    act, _ = schedule(segs)
    print(f"seed {_SEED} ({_SCORE} crossings), {len(NODES)} nodes, {len(EDGES)} edges, "
          f"sink at {act[SINK]:.2f}s, cycle {act[SINK] + HOLD + FADE + REST:.2f}s")
    for theme in THEMES:
        path = os.path.join(here, f"dag-{theme}.svg")
        svg = build(theme)
        with open(path, "w") as f:
            f.write(svg)
        print(f"{path}: {len(svg)} bytes")


if __name__ == "__main__":
    main()
