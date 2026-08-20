# -*- coding: utf-8 -*-
"""Speech-bubble phrases. Pure IO / parsing, no Qt dependency.

An external ``dialogues.txt`` may be edited by the user (one phrase per line,
``#`` starts a comment). When missing or empty, built-in defaults are used.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

DEFAULT_DIALOGUES: tuple[str, ...] = (
    "别戳我啦！(≧▽≦)",
    "嘿嘿，好痒～",
    "今天也要加油鸭！",
    "喵？有什么事吗？",
    "再戳我就要生气啦！",
    "呼～好舒服～",
    "我在盯着你哦 (｡•̀ᴗ-)✧",
    "作业写完了吗？",
    "来陪我玩嘛～",
    "叮！获得一枚摸头杀！",
    "有我在，不孤单哦～",
    "略略略，抓不到我～",
    "你的摸头杀已到账～",
    "认真学习了吗？（严肃脸）",
    "累了就歇会儿吧～",
    "今天天气不错，出去走走？",
    "我有小情绪了！",
    "卖萌中，请勿打扰～",
    "本喵超乖的！",
    "戳我干嘛，想我啦？",
)


def parse_dialogues(text: str) -> list[str]:
    """Strip comments and blank lines from a dialogues file's text."""
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def default_dialogues() -> list[str]:
    return list(DEFAULT_DIALOGUES)


def dialogues_path() -> Path:
    """Where an editable dialogues.txt is looked for.

    Frozen (PyInstaller) builds look next to the executable; source runs look
    inside the package so ``python -m pet`` finds it without extra config.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "dialogues.txt"
    return Path(__file__).resolve().parent / "dialogues.txt"


def load_dialogues(path: Path | str | None = None) -> list[str]:
    """Return phrases from ``path`` if non-empty, else the built-in defaults."""
    p = Path(path) if path is not None else dialogues_path()
    try:
        lines = parse_dialogues(p.read_text(encoding="utf-8"))
        if lines:
            return lines
    except OSError:
        pass
    return default_dialogues()


def write_dialogues(phrases: Iterable[str], path: Path | str) -> None:
    """Write phrases (one per line) to a file — used by tests."""
    Path(path).write_text("\n".join(phrases) + "\n", encoding="utf-8")
