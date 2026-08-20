# -*- coding: utf-8 -*-
"""Command-line entry point for the desktop pet.

Run with ``desktop-pet``, ``python -m pet`` or ``python -m pet.main``.

Options
-------
--image PATH         Use a custom character PNG instead of the drawn default.
--smoke              Run a short offscreen smoke test and exit.
--export-preview P   Render a preview screenshot (default character + bubble).
"""

from __future__ import annotations

import argparse
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pet.widget import PetWidget


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="desktop-pet",
        description="A cute desktop pet built with PySide6.",
    )
    parser.add_argument(
        "--image", metavar="PATH", default=None,
        help="custom character PNG (a transparent background looks best)",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="run an offscreen smoke test and exit",
    )
    parser.add_argument(
        "--export-preview", metavar="PATH", default=None,
        help="render a preview screenshot (default character + bubble) to PATH and exit",
    )
    return parser.parse_args(argv)


def _export_preview(path: str) -> bool:
    # Renders on the real platform so system CJK fonts are available. The
    # widget is hidden again before any events are pumped, so no window
    # flashes; QWidget.grab() renders hidden widgets just fine.
    widget = PetWidget()
    widget.hide()
    widget.show_bubble("今天也要加油鸭！")
    QApplication.processEvents()
    return bool(widget.grab().save(path))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    # Headless / deterministic runs never open a real window. The preview
    # deliberately stays on the real platform so CJK text renders correctly.
    if args.smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # the tray icon owns the exit

    if args.smoke:
        widget = PetWidget(args.image)
        for _ in range(4):
            widget.trigger_interaction()
        widget.enter_idle()
        widget.enter_sleep()
        widget.wake()
        widget.toggle_follow(True)
        widget.toggle_follow(False)
        QTimer.singleShot(900, widget._save_config)
        QTimer.singleShot(1000, app.quit)
        app.exec()
        print("smoke test OK")
        return 0

    if args.export_preview:
        if not _export_preview(args.export_preview):
            print(f"failed to save preview to {args.export_preview}", file=sys.stderr)
            return 1
        print(f"preview saved to {args.export_preview}")
        return 0

    pet = PetWidget(args.image)
    app.aboutToQuit.connect(pet._save_config)
    sys.exit(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
