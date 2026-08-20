# -*- coding: utf-8 -*-
"""Character rendering.

Two sources for the pet sprite:

* ``make_default_pixmap`` — a cute round creature drawn entirely with QPainter.
  There is no bundled art, so the project is self-contained and free of any
  image-licensing worries. This is what a fresh clone shows out of the box.
* ``load_pixmap`` / ``create_pixmap`` — loads a user-supplied PNG (preferably
  with an alpha channel), e.g. ``desktop-pet --image my_character.png``.

All drawing is vector QPainter calls; no asset files are touched.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

DEFAULT_BASE_H = 260            # logical height of the drawn character
CANVAS_W, CANVAS_H = 300, 260   # drawing coordinate space
SUPER = 3                       # supersample factor for crisp edges
OUTLINE_W = 2.5

# --- palette ---
BODY = QColor(255, 184, 92)
BODY_OUTLINE = QColor(217, 129, 47)
BELLY = QColor(255, 241, 220)
EAR_INNER = QColor(255, 159, 176)
EYE = QColor(61, 43, 36)
BLUSH = QColor(255, 159, 176, 200)
GLOSS = QColor(255, 255, 255, 90)
WHITE = QColor(255, 255, 255)


def _ellipse(
    p: QPainter,
    x: float, y: float, w: float, h: float,
    fill: QColor,
    outline: QColor | None = None,
) -> None:
    """Filled ellipse, optionally with a rounded outline."""
    p.setPen(Qt.NoPen)
    if outline is not None:
        p.setPen(QPen(outline, OUTLINE_W, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(fill)
    p.drawEllipse(QRectF(x, y, w, h))


def _stroke(p: QPainter, path: QPainterPath, width: float, color: QColor) -> None:
    p.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)


def _draw_character(p: QPainter, s: float) -> None:
    """Draw the default round creature in a 300x260 space, scaled by ``s``."""
    # ---- tail (behind the body, curling up on the right) ----
    tail = QPainterPath()
    tail.moveTo(238 * s, 205 * s)
    tail.cubicTo(274 * s, 176 * s, 262 * s, 138 * s, 240 * s, 120 * s)
    _stroke(p, tail, 26 * s, BODY_OUTLINE)  # outline ring
    _stroke(p, tail, 21 * s, BODY)

    # ---- ears (peek above the body) ----
    _ellipse(p, 72 * s, 52 * s, 44 * s, 44 * s, BODY, BODY_OUTLINE)
    _ellipse(p, 184 * s, 52 * s, 44 * s, 44 * s, BODY, BODY_OUTLINE)
    _ellipse(p, 84 * s, 64 * s, 20 * s, 20 * s, EAR_INNER)
    _ellipse(p, 196 * s, 64 * s, 20 * s, 20 * s, EAR_INNER)

    # ---- body ----
    _ellipse(p, 55 * s, 105 * s, 190 * s, 155 * s, BODY, BODY_OUTLINE)

    # ---- belly patch ----
    _ellipse(p, 96 * s, 196 * s, 108 * s, 60 * s, BELLY)

    # ---- paws (front) ----
    _ellipse(p, 64 * s, 218 * s, 30 * s, 30 * s, BODY, BODY_OUTLINE)
    _ellipse(p, 206 * s, 218 * s, 30 * s, 30 * s, BODY, BODY_OUTLINE)

    # ---- glossy highlight on the head ----
    _ellipse(p, 96 * s, 116 * s, 62 * s, 26 * s, GLOSS)

    # ---- eyes ----
    _ellipse(p, 108 * s, 132 * s, 22 * s, 30 * s, EYE)
    _ellipse(p, 170 * s, 132 * s, 22 * s, 30 * s, EYE)
    _ellipse(p, 113 * s, 139 * s, 8 * s, 8 * s, WHITE)
    _ellipse(p, 175 * s, 139 * s, 8 * s, 8 * s, WHITE)

    # ---- blush ----
    _ellipse(p, 88 * s, 170 * s, 24 * s, 12 * s, BLUSH)
    _ellipse(p, 188 * s, 170 * s, 24 * s, 12 * s, BLUSH)

    # ---- nose ----
    nose = QPainterPath()
    nose.moveTo(150 * s, 160 * s)
    nose.lineTo(145 * s, 168 * s)
    nose.lineTo(155 * s, 168 * s)
    nose.closeSubpath()
    p.setPen(Qt.NoPen)
    p.setBrush(EYE)
    p.drawPath(nose)

    # ---- "ω" smile ----
    p.setPen(QPen(EYE, 3 * s, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(136 * s, 168 * s, 14 * s, 12 * s), 180 * 16, 180 * 16)
    p.drawArc(QRectF(150 * s, 168 * s, 14 * s, 12 * s), 180 * 16, 180 * 16)


def make_default_pixmap(base_h: int = DEFAULT_BASE_H) -> QPixmap:
    """Render the default character to a transparent QPixmap of height ``base_h``."""
    w = int(round(CANVAS_W / CANVAS_H * base_h))
    internal_h = base_h * SUPER
    internal_w = int(round(CANVAS_W / CANVAS_H * internal_h))

    pm = QPixmap(internal_w, internal_h)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_character(p, internal_h / CANVAS_H)
    p.end()

    return pm.scaled(w, base_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def load_pixmap(path: Path | str) -> QPixmap:
    """Load a user-supplied character image (preferably a transparent PNG)."""
    pm = QPixmap(str(path))
    if pm.isNull():
        raise FileNotFoundError(f"无法加载角色图：{path}")
    return pm


def create_pixmap(image_path: Path | str | None = None, base_h: int = DEFAULT_BASE_H) -> QPixmap:
    """Return the user image if given, otherwise the drawn default character."""
    if image_path:
        return load_pixmap(image_path)
    return make_default_pixmap(base_h)
