# -*- coding: utf-8 -*-
"""The pet widget: a transparent, frameless, always-on-top desktop creature.

Window + interaction logic (drag, click, wheel, tray, menus, idle/sleep
timers). Pure math lives in :mod:`pet.animation`, the behaviour state machine
in :mod:`pet.state`, settings in :mod:`pet.config` and the sprite in
:mod:`pet.render`.
"""

from __future__ import annotations

import random

from PySide6.QtCore import (
    Qt, QEasingCurve, QPoint, QRect, QRectF, QTimer, QVariantAnimation,
)
from PySide6.QtGui import (
    QColor, QCursor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath,
    QPen, QPolygonF,
)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from pet import animation, config, dialogue, render
from pet.platform import hide_from_taskbar
from pet.state import PetStateMachine

# ---- tunables ----
BASE_HEIGHT = render.DEFAULT_BASE_H
BUBBLE_RESERVE = 130        # transparent area reserved above the pet for the bubble
MIN_ZOOM, MAX_ZOOM = 0.3, 3.0
DRAG_THRESHOLD = 6          # px moved before a press becomes a drag
BUBBLE_SHOW_MS = 2600       # bubble display duration (non-persistent)
MAX_BUBBLE_W = 320          # bubble wraps beyond this width
BUBBLE_PAD_X, BUBBLE_PAD_Y = 14, 10
IDLE_AFTER_MS = 15000       # no interaction → idle
SLEEP_AFTER_MS = 45000      # idling → sleep
SIZES_PCT = (50, 75, 100, 125, 150, 200)


class PetWidget(QWidget):
    def __init__(self, image_path: str | None = None):
        super().__init__()
        self.pixmap = render.create_pixmap(image_path, BASE_HEIGHT)
        self.dialogues = dialogue.load_dialogues()

        # ---- persisted settings ----
        cfg = config.load_config()
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, float(cfg.get("zoom", 1.0))))
        self._topmost = bool(cfg.get("topmost", True))
        self._follow_mouse = bool(cfg.get("follow_mouse", False))
        self._saved_pos = cfg.get("pos", None)

        # base display size (keeps aspect ratio of the sprite)
        self.base_h = BASE_HEIGHT
        self.base_w = int(self.pixmap.width() * BASE_HEIGHT / self.pixmap.height())

        # ---- interaction animation state ----
        self._dx = self._dy = 0.0
        self._sx = self._sy = 1.0
        self._anim = None

        # ---- idle / sleep animation state ----
        self._idle_dx = self._idle_dy = 0.0
        self._idle_sx = self._idle_sy = 1.0
        self._idle_anim = None
        self._idle_mode = "sway"
        self.states = PetStateMachine()

        # ---- speech bubble ----
        self._bubble_text = ""
        self._bubble_visible = False
        self._bubble_persistent = False
        self._bubble_font = QFont("Microsoft YaHei", 11)
        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self.hide_bubble)

        # ---- drag / walk ----
        self._press_global = QPoint()
        self._win_pos = QPoint()
        self._dragging = False
        self._walking = False
        self._walk_steps = self._walk_step = 0
        self._walk_dir = 1

        self._geo_ready = False

        # ---- timers ----
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self.enter_idle)
        self._sleep_timer = QTimer(self)
        self._sleep_timer.setSingleShot(True)
        self._sleep_timer.timeout.connect(self.enter_sleep)
        self._walk_timer = QTimer(self)
        self._walk_timer.timeout.connect(self._walk_tick)
        self._follow_timer = QTimer(self)
        self._follow_timer.timeout.connect(self._follow_tick)

        # Frameless + (optionally) topmost. Do NOT add Qt.Tool here — a
        # parentless tool window stays hidden on Windows while unfocused.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._apply_topmost_flag()
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._update_geometry()
        self.show()
        hide_from_taskbar(self)
        self._setup_tray()

        if self._follow_mouse:
            self._follow_timer.start(40)
        self._reset_idle_timer()

    # ------------------------------------------------------------------
    # geometry / size
    # ------------------------------------------------------------------
    def _disp_w(self) -> int:
        return int(self.base_w * self.zoom)

    def _disp_h(self) -> int:
        return int(self.base_h * self.zoom)

    def _bubble_size(self) -> tuple[int, int]:
        if not (self._bubble_visible and self._bubble_text):
            return 0, 0
        fm = QFontMetrics(self._bubble_font)
        max_text_w = MAX_BUBBLE_W - 2 * BUBBLE_PAD_X
        br = fm.boundingRect(QRect(0, 0, max_text_w, 500),
                             Qt.TextWordWrap, self._bubble_text)
        return br.width() + 2 * BUBBLE_PAD_X, br.height() + 2 * BUBBLE_PAD_Y

    def _pet_anchor_global(self) -> QPoint:
        local = QPoint(self.width() // 2, BUBBLE_RESERVE + self._disp_h())
        return self.mapToGlobal(local)

    def _update_geometry(self) -> None:
        """Resize to fit sprite + bubble, keeping the pet's base center fixed."""
        dw, dh = self._disp_w(), self._disp_h()
        bw, _ = self._bubble_size()
        w = max(dw, bw)
        h = BUBBLE_RESERVE + dh

        anchor = self._pet_anchor_global() if self._geo_ready else None
        self.setFixedSize(w, h)

        if anchor is None:
            if self._saved_pos and len(self._saved_pos) == 2:
                x, y = self._clamp_to_screen(int(self._saved_pos[0]),
                                             int(self._saved_pos[1]), w, h)
                self.move(x, y)
            else:
                self._place_initial()
        else:
            new_local = QPoint(w // 2, BUBBLE_RESERVE + dh)
            self.move(anchor.x() - new_local.x(), anchor.y() - new_local.y())
        self._geo_ready = True

    @staticmethod
    def _clamp_to_screen(x: int, y: int, w: int, h: int) -> tuple[int, int]:
        screen = QApplication.primaryScreen().availableGeometry()
        x = max(screen.left(), min(x, screen.right() - w))
        y = max(screen.top(), min(y, screen.bottom() - h))
        return x, y

    def _place_initial(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.center().x() - self.width() // 2
        y = screen.bottom() - self.height() - 40
        self.move(x, y)

    def _apply_topmost_flag(self) -> None:
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self._topmost)

    # ------------------------------------------------------------------
    # system tray
    # ------------------------------------------------------------------
    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(self.pixmap.scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.tray.setToolTip("桌宠")

        menu = QMenu()
        menu.addAction("显示 / 隐藏宠物", self.toggle_visible)
        menu.addMenu(self._size_menu("调整大小"))
        topmost = menu.addAction("置顶显示")
        topmost.setCheckable(True)
        topmost.setChecked(self._topmost)
        topmost.triggered.connect(self.toggle_topmost)
        follow = menu.addAction("跟随鼠标")
        follow.setCheckable(True)
        follow.setChecked(self._follow_mouse)
        follow.triggered.connect(self.toggle_follow)
        menu.addSeparator()
        menu.addAction("退出", self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _size_menu(self, title: str) -> QMenu:
        menu = QMenu(title)
        for pct in SIZES_PCT:
            act = menu.addAction(f"{pct}%")
            act.triggered.connect(lambda _=False, p=pct: self.set_zoom(p / 100))
        return menu

    def _tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_visible()

    def toggle_visible(self) -> None:
        self.setVisible(not self.isVisible())

    def _quit(self) -> None:
        self._save_config()
        QApplication.instance().quit()

    # ------------------------------------------------------------------
    # settings
    # ------------------------------------------------------------------
    def _save_config(self) -> None:
        config.save_config({
            "pos": [self.x(), self.y()],
            "zoom": self.zoom,
            "topmost": self._topmost,
            "follow_mouse": self._follow_mouse,
        })

    # ------------------------------------------------------------------
    # painting
    # ------------------------------------------------------------------
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        if self._bubble_visible and self._bubble_text:
            self._draw_bubble(p)

        dw, dh = self._disp_w(), self._disp_h()
        dx = self._dx + self._idle_dx
        dy = self._dy + self._idle_dy
        sx = self._sx * self._idle_sx
        sy = self._sy * self._idle_sy

        px0 = (self.width() - dw) / 2.0 + dx
        py0 = BUBBLE_RESERVE + dy
        cx, cy = px0 + dw / 2.0, py0 + dh / 2.0

        p.save()
        p.translate(cx, cy)
        p.scale(sx, sy)
        p.translate(-cx, -cy)
        p.drawPixmap(QRectF(px0, py0, dw, dh), self.pixmap,
                     QRectF(self.pixmap.rect()))
        p.restore()

    def _draw_bubble(self, p: QPainter) -> None:
        fm = QFontMetrics(self._bubble_font)
        bw, bh = self._bubble_size()
        bx = (self.width() - bw) / 2.0
        by = BUBBLE_RESERVE - bh - 14

        tail_w, tail_h = 16.0, 9.0
        tail_top = by + bh - 1
        cx = self.width() / 2.0
        tail = QPolygonF([
            QPoint(int(cx - tail_w / 2), int(tail_top)),
            QPoint(int(cx + tail_w / 2), int(tail_top)),
            QPoint(int(cx), int(tail_top + tail_h)),
        ])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255))
        p.drawPolygon(tail)

        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, bw, bh), 12, 12)
        p.fillPath(path, QColor(255, 255, 255))
        p.setPen(QPen(QColor(214, 214, 214), 1.5))
        p.drawPath(path)

        p.setPen(QColor(45, 45, 45))
        p.setFont(self._bubble_font)
        text_rect = QRectF(bx + BUBBLE_PAD_X, by + BUBBLE_PAD_Y,
                           bw - 2 * BUBBLE_PAD_X, bh - 2 * BUBBLE_PAD_Y)
        p.drawText(text_rect, Qt.TextWordWrap | Qt.AlignCenter, self._bubble_text)

    # ------------------------------------------------------------------
    # speech bubble
    # ------------------------------------------------------------------
    def show_bubble(self, text: str, persistent: bool = False) -> None:
        self._bubble_text = text
        self._bubble_visible = True
        self._bubble_persistent = persistent
        self._update_geometry()
        self.update()
        if not persistent:
            self._bubble_timer.start(BUBBLE_SHOW_MS)

    def hide_bubble(self) -> None:
        self._bubble_visible = False
        self._bubble_text = ""
        self._bubble_persistent = False
        self._update_geometry()
        self.update()

    # ------------------------------------------------------------------
    # behaviour state machine: awake → idle → sleep
    # ------------------------------------------------------------------
    def _reset_idle_timer(self) -> None:
        self._idle_timer.start(IDLE_AFTER_MS)

    def enter_idle(self) -> None:
        if not self.states.enter_idle():
            return
        self.show_bubble("……")
        self._set_idle_anim("sway")
        self._sleep_timer.start(SLEEP_AFTER_MS)

    def enter_sleep(self) -> None:
        if not self.states.enter_sleep():
            return
        self._set_idle_anim("breath")
        self.show_bubble("Zzz…", persistent=True)

    def wake(self) -> None:
        self.states.wake()
        if self._idle_anim is not None:
            self._idle_anim.stop()
            self._idle_anim = None
        self._idle_dx = self._idle_dy = 0.0
        self._idle_sx = self._idle_sy = 1.0
        self._sleep_timer.stop()
        self.hide_bubble()
        self._reset_idle_timer()
        self.update()

    def _set_idle_anim(self, mode: str) -> None:
        if self._idle_anim is not None:
            self._idle_anim.stop()
        self._idle_mode = mode
        self._idle_anim = QVariantAnimation(self)
        self._idle_anim.setStartValue(0.0)
        self._idle_anim.setEndValue(1.0)
        self._idle_anim.setDuration(3000 if mode == "breath" else 2600)
        self._idle_anim.setLoopCount(-1)
        self._idle_anim.valueChanged.connect(self._idle_tick)
        self._idle_anim.start()

    def _idle_tick(self, t: float) -> None:
        (self._idle_dx, self._idle_dy,
         self._idle_sx, self._idle_sy) = animation.idle_transform(t, self._idle_mode)
        self.update()

    # ------------------------------------------------------------------
    # interaction animations
    # ------------------------------------------------------------------
    def trigger_interaction(self) -> None:
        """Random reaction on click: jump / squash / shake / walk + a phrase."""
        self.wake()
        kind = random.choice(["jump", "squash", "shake", "walk"])
        self.show_bubble(random.choice(self.dialogues))
        if kind == "walk":
            self._start_walk()
        elif kind == "jump":
            self._play(lambda t: animation.jump_transform(t, self.zoom), 460, QEasingCurve.OutQuad)
        elif kind == "squash":
            self._play(lambda t: animation.squash_transform(t), 440, None)
        else:
            self._play(lambda t: animation.shake_transform(t, self.zoom), 520, None)

    def _play(self, tfunc, duration: int, easing) -> None:
        if self._anim is not None:
            self._anim.stop()
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(duration)
        if easing is not None:
            self._anim.setEasingCurve(easing)
        self._anim.valueChanged.connect(lambda t: self._apply(tfunc(t)))
        self._anim.finished.connect(self._anim_finished)
        self._anim.start()

    def _apply(self, tr) -> None:
        self._dx, self._dy, self._sx, self._sy = tr
        self.update()

    def _anim_finished(self) -> None:
        if self.sender() is not self._anim:
            return
        self._reset_interaction_transform()

    def _reset_interaction_transform(self) -> None:
        self._dx = self._dy = 0.0
        self._sx = self._sy = 1.0
        self.update()

    # ------------------------------------------------------------------
    # walking
    # ------------------------------------------------------------------
    def _start_walk(self) -> None:
        if self._anim is not None:
            self._anim.stop()
            self._anim = None
        self._reset_interaction_transform()
        self._walking = True
        self._walk_steps = random.randint(10, 18)
        self._walk_step = 0
        self._walk_dir = random.choice([-1, 1])
        self._walk_timer.start(32)

    def _walk_tick(self) -> None:
        self._walk_step += 1
        if self._walk_step > self._walk_steps:
            self._walk_timer.stop()
            self._walking = False
            self._reset_interaction_transform()
            return
        step = 7 * self.zoom
        nx = self.x() + self._walk_dir * step
        screen = QApplication.primaryScreen().availableGeometry()
        if nx < screen.left():
            nx = screen.left()
            self._walk_dir = 1
        elif nx + self.width() > screen.right():
            nx = screen.right() - self.width()
            self._walk_dir = -1
        self.move(int(nx), self.y())
        self._dy = animation.walk_bounce(self._walk_step, self.zoom)
        self.update()

    # ------------------------------------------------------------------
    # follow mouse
    # ------------------------------------------------------------------
    def _follow_tick(self) -> None:
        if self._dragging or self._walking:
            return
        cur = QCursor.pos()
        target_x = cur.x() - self.width() // 2
        target_y = cur.y() - (BUBBLE_RESERVE + self._disp_h() // 2)
        dx = target_x - self.x()
        dy = target_y - self.y()
        if abs(dx) <= 2 and abs(dy) <= 2:
            return
        self.move(self.x() + int(dx * 0.18), self.y() + int(dy * 0.18))

    # ------------------------------------------------------------------
    # mouse interaction
    # ------------------------------------------------------------------
    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton:
            self._press_global = e.globalPosition().toPoint()
            self._win_pos = self.pos()
            self._dragging = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:
        if e.buttons() & Qt.LeftButton:
            delta = e.globalPosition().toPoint() - self._press_global
            if not self._dragging and (abs(delta.x()) + abs(delta.y())) > DRAG_THRESHOLD:
                self._dragging = True
            if self._dragging:
                self.move(self._win_pos + delta)

    def mouseReleaseEvent(self, e) -> None:
        if e.button() == Qt.LeftButton and not self._dragging:
            self.trigger_interaction()
        self._dragging = False
        super().mouseReleaseEvent(e)

    def wheelEvent(self, e) -> None:
        delta = e.angleDelta().y()
        factor = 1.1 if delta > 0 else 1 / 1.1
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom * factor))
        if abs(new_zoom - self.zoom) < 1e-6:
            return
        self.zoom = new_zoom
        self._update_geometry()
        self.update()
        e.accept()

    # ------------------------------------------------------------------
    # right-click menu
    # ------------------------------------------------------------------
    def contextMenuEvent(self, e) -> None:
        menu = QMenu(self)
        menu.addMenu(self._size_menu("调整大小"))
        menu.addSeparator()
        topmost = menu.addAction("置顶显示")
        topmost.setCheckable(True)
        topmost.setChecked(self._topmost)
        topmost.triggered.connect(self.toggle_topmost)
        follow = menu.addAction("跟随鼠标")
        follow.setCheckable(True)
        follow.setChecked(self._follow_mouse)
        follow.triggered.connect(self.toggle_follow)
        menu.addSeparator()
        menu.addAction("退出", self._quit)
        menu.exec(e.globalPos())

    def set_zoom(self, value: float) -> None:
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, value))
        self._update_geometry()
        self.update()

    def toggle_topmost(self, checked: bool | None = None) -> None:
        if checked is None:
            checked = not self._topmost
        self._topmost = bool(checked)
        self._apply_topmost_flag()
        self.show()

    def toggle_follow(self, checked: bool | None = None) -> None:
        if checked is None:
            checked = not self._follow_mouse
        self._follow_mouse = bool(checked)
        if self._follow_mouse:
            self._follow_timer.start(40)
        else:
            self._follow_timer.stop()
