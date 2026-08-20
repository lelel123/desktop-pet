# -*- coding: utf-8 -*-
"""Pure animation transforms for the pet. No Qt dependency — unit-testable.

Every function returns a ``Transform`` tuple ``(dx, dy, sx, sy)`` describing
an affine offset/scale applied to the pet around its center, given a
normalised time ``t`` in [0, 1].
"""

from __future__ import annotations

import math
from typing import Tuple

Transform = Tuple[float, float, float, float]  # (dx, dy, sx, sy)

# --------------------------------------------------------------------------
# Interaction animations (single shot, t: 0 -> 1)
# --------------------------------------------------------------------------


def jump_transform(t: float, zoom: float = 1.0) -> Transform:
    """A parabolic hop upward. Peak (t=0.5) rises 62 * zoom px."""
    height = 62.0 * zoom
    return (0.0, -4.0 * height * t * (1.0 - t), 1.0, 1.0)


def squash_transform(t: float) -> Transform:
    """Squash & stretch: wider and shorter at t=0.5, back to normal at ends."""
    s = math.sin(math.pi * t)
    return (0.0, 0.0, 1.0 + 0.30 * s, 1.0 - 0.28 * s)


def shake_transform(t: float, zoom: float = 1.0) -> Transform:
    """A fast horizontal shake that decays toward the end (t=1 → 0)."""
    amp = 14.0 * zoom
    dx = amp * math.sin(2.0 * math.pi * 6.0 * t) * (1.0 - t)
    return (dx, 0.0, 1.0, 1.0)


def walk_bounce(step: int, zoom: float = 1.0) -> float:
    """Vertical bob while walking, as an offset ``dy`` (0 when standing)."""
    return -abs(math.sin(step / 2.2)) * 4.0 * zoom


# --------------------------------------------------------------------------
# Idle / sleep animations (looping, t: 0 -> 1 per cycle)
# --------------------------------------------------------------------------


def idle_transform(t: float, mode: str) -> Transform:
    """Looping transform.

    ``mode="sway"`` (idle): rocks left/right by up to 7 px.
    ``mode="breath"`` (sleep): gentle breathing scale (±3.5 %).
    """
    s = math.sin(2.0 * math.pi * t)
    if mode == "breath":
        return (0.0, 0.0, 1.0 + 0.035 * s, 1.0 - 0.035 * s)
    # sway
    return (7.0 * s, 0.0, 1.0, 1.0)
