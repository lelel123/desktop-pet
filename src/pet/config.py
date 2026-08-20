# -*- coding: utf-8 -*-
"""Settings persistence. Pure IO, no Qt dependency — unit-testable."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Same file the original pet used, so existing configs carry over.
DEFAULT_CONFIG_FILE = "~/.desktop_pet.json"


def config_path() -> Path:
    """Default config location in the user's home directory."""
    return Path(os.path.expanduser(DEFAULT_CONFIG_FILE))


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Read config as a dict. Missing file or corrupt JSON yields an empty dict."""
    p = Path(path) if path is not None else config_path()
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict[str, Any], path: Path | str | None = None) -> None:
    """Write config to disk. Failures (e.g. unwritable home) are swallowed."""
    p = Path(path) if path is not None else config_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
