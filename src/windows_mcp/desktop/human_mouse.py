"""Human-like cursor paths (windows-mcp-ko).

Instead of teleporting or sliding along a ruler-straight line at constant
speed, the cursor follows a gently curved path, accelerates and decelerates
like a hand (minimum-jerk profile), wobbles slightly, varies its pace along
the way, and on long moves sometimes overshoots and corrects.

Disable with the environment variable WINDOWS_MCP_HUMAN_MOUSE=0.
"""

from __future__ import annotations

import math
import os
import random
from collections.abc import Callable
from time import sleep

Point = tuple[int, int]
Step = tuple[int, int, float]  # x, y, seconds to wait after moving there

_STEP_SECONDS = 0.008
_MAX_SECONDS = 1.2


def enabled() -> bool:
    return os.environ.get("WINDOWS_MCP_HUMAN_MOUSE", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def _min_jerk(t: float) -> float:
    return 10 * t**3 - 15 * t**4 + 6 * t**5


def _bezier(p0, p1, p2, p3, u: float) -> tuple[float, float]:
    a = (1 - u) ** 3
    b = 3 * (1 - u) ** 2 * u
    c = 3 * (1 - u) * u**2
    d = u**3
    return (
        a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
        a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
    )


def default_duration(distance: float, rng: random.Random) -> float:
    """Fitts-like: longer moves take longer, but not proportionally."""
    seconds = (0.12 + 0.11 * math.log2(1 + distance / 40)) * rng.uniform(0.85, 1.25)
    return min(seconds, _MAX_SECONDS)


def _segment(
    start: Point, end: Point, duration: float, rng: random.Random, curve: float
) -> list[Step]:
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy)
    if dist < 2:
        return [(ex, ey, 0.0)]
    nx, ny = -dy / dist, dx / dist
    bend = dist * curve * rng.choice((-1, 1))
    c1 = (
        sx + dx * rng.uniform(0.2, 0.4) + nx * bend * rng.uniform(0.6, 1.2),
        sy + dy * rng.uniform(0.2, 0.4) + ny * bend * rng.uniform(0.6, 1.2),
    )
    c2 = (
        sx + dx * rng.uniform(0.6, 0.8) + nx * bend * rng.uniform(0.3, 0.9),
        sy + dy * rng.uniform(0.6, 0.8) + ny * bend * rng.uniform(0.3, 0.9),
    )
    steps = max(6, min(150, round(duration / _STEP_SECONDS)))
    # A small, smooth wobble in pace so speed is not a perfect bell curve.
    pace_amp = rng.uniform(0.0, 0.06)
    pace_freq = rng.uniform(1.5, 3.5)
    pace_phase = rng.uniform(0, 2 * math.pi)
    tremor = min(1.5, 0.4 + dist / 800)
    out: list[Step] = []
    last_u = 0.0
    for i in range(1, steps + 1):
        t = i / steps
        u = _min_jerk(t) + pace_amp * t * (1 - t) * math.sin(2 * math.pi * pace_freq * t + pace_phase)
        u = min(1.0, max(last_u, u))  # never move backwards along the curve
        last_u = u
        px, py = _bezier((sx, sy), c1, c2, (ex, ey), u)
        if i < steps:
            wobble = tremor * math.sin(math.pi * t)
            px += rng.gauss(0, wobble)
            py += rng.gauss(0, wobble)
        out.append((round(px), round(py), duration / steps * rng.uniform(0.7, 1.3)))
    out[-1] = (ex, ey, out[-1][2])
    return out


def plan(
    start: Point,
    end: Point,
    *,
    duration: float | None = None,
    rng: random.Random | None = None,
    allow_overshoot: bool = True,
) -> list[Step]:
    """Return cursor positions (ending exactly at *end*) with per-step waits."""
    rng = rng or random.Random()
    dist = math.hypot(end[0] - start[0], end[1] - start[1])
    if dist < 2:
        return [(end[0], end[1], 0.0)]
    total = default_duration(dist, rng) if duration is None else max(0.0, duration)
    curve = rng.uniform(0.03, 0.12)
    if allow_overshoot and dist > 300 and rng.random() < 0.3:
        ux = (end[0] - start[0]) / dist
        uy = (end[1] - start[1]) / dist
        over = rng.uniform(4, min(18, dist * 0.03))
        mid = (
            round(end[0] + ux * over + rng.uniform(-3, 3)),
            round(end[1] + uy * over + rng.uniform(-3, 3)),
        )
        main = _segment(start, mid, total * 0.85, rng, curve)
        fix = _segment(mid, end, total * 0.15 + rng.uniform(0.04, 0.09), rng, 0.0)
        return main + fix
    return _segment(start, end, total, rng, curve)


def glide(
    start: Point,
    end: Point,
    set_pos: Callable[[int, int], object],
    *,
    before_step: Callable[[], object] | None = None,
    after_step: Callable[[], object] | None = None,
    duration: float | None = None,
    allow_overshoot: bool = True,
    sleeper: Callable[[float], object] = sleep,
) -> None:
    """Drive the cursor along a human-like path from *start* to *end*."""
    for x, y, wait in plan(start, end, duration=duration, allow_overshoot=allow_overshoot):
        if before_step:
            before_step()
        set_pos(x, y)
        if after_step:
            after_step()
        if wait > 0:
            sleeper(wait)
