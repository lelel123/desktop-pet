# Desktop Pet 🐾

A cute, transparent, **always-on-top** desktop pet built with [PySide6](https://pypi.org/project/PySide6/). Drag it around, poke it for a reaction, scroll to resize — leave it alone and it gets sleepy. No external art is required: the default character is drawn entirely with QPainter, so the project ships self-contained with zero licensing worries.

![preview](docs/screenshot.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![CI](https://github.com/lelel123/desktop-pet/actions/workflows/ci.yml/badge.svg)](https://github.com/lelel123/desktop-pet/actions/workflows/ci.yml)

## Features

- ✨ **Program-drawn default character** — no copyrighted image shipped with the repo
- 🖱️ **Drag / click / wheel** — move it, poke it for reactions, scroll to resize (0.3×–3×)
- 🎭 **Interaction animations** — jump, squash-and-stretch, shake, walk
- 😴 **Auto states** — idle (swaying) after 15 s, sleep (breathing + "Zzz…") after 45 s
- 💬 **Speech bubbles** — editable phrases, one per line
- 📌 **System tray icon** — toggle visibility, size, always-on-top, follow-mouse, quit
- 🧠 **Remembers settings** — position / size / topmost / follow-mouse, stored in `~/.desktop_pet.json`
- 🖼️ **Custom character** — bring your own transparent PNG with `--image`

## Install & run

Requires **Python ≥ 3.10**.

```bash
# install (editable) and run
pip install -e .
desktop-pet

# or run without installing, from the repo root
python -m pet

# bring your own character image
desktop-pet --image path/to/character.png
```

Windows users can instead build a single-file `.exe` (see [Packaging](#packaging)).

## Controls

| Action        | Result                                  |
|---------------|-----------------------------------------|
| Left-drag     | Move the pet                            |
| Left-click    | Random interaction + a speech bubble    |
| Mouse wheel   | Resize (0.3×–3×)                        |
| Right-click   | Menu: size / topmost / follow mouse / quit |
| Tray icon     | Click: toggle visible · Right-click: menu |

## Customize

**Phrases** — edit `dialogues.txt` (one per line, `#` starts a comment). When packaged, put the file next to the `.exe`.

**Character** — run with `--image path/to/character.png`. A transparent background looks best; opaque images will render as a rectangle.

## Tests

```bash
pip install -e .[dev]
QT_QPA_PLATFORM=offscreen pytest
```

The suite runs headless, so it works in CI and on machines without a display.

## Packaging

Build a single-file Windows executable with PyInstaller:

```bash
pip install -e .[dev]
python -m PyInstaller --noconfirm --clean --onefile --noconsole \
  --name DesktopPet \
  --exclude-module PySide6.QtQml \
  --exclude-module PySide6.QtQuick \
  --exclude-module PySide6.QtWebEngineCore \
  --exclude-module PySide6.QtWebEngineWidgets \
  --exclude-module PySide6.QtMultimedia \
  --exclude-module PySide6.QtNetwork \
  --add-data "src/pet/dialogues.txt;pet" \
  src/pet/__main__.py
```

The exclusions drop Qt modules the pet doesn't use — a one-file build is ~46 MB instead of ~400 MB. The `.exe` lands in `dist/`; rename it freely (the filename doesn't affect behavior). Run `DesktopPet.exe --smoke` for a headless self-check.

## Project structure

```
desktop-pet/
├── src/pet/
│   ├── main.py        # CLI entry point
│   ├── widget.py      # window, drag, tray, menus, idle/sleep timers
│   ├── animation.py   # pure animation transforms
│   ├── state.py       # awake → idle → sleep state machine
│   ├── render.py      # QPainter default character + image loading
│   ├── config.py      # ~/.desktop_pet.json persistence
│   ├── dialogue.py    # speech-bubble phrases
│   └── platform.py    # Windows taskbar tweaks
├── tests/             # pytest suite
├── docs/              # screenshot for the README
└── pyproject.toml
```

## License

[MIT](LICENSE)

---

## 中文简介

一个用 PySide6 写的桌面宠物：透明无边框、始终置顶，可以拖动、点击互动、滚轮缩放，放着不动会发呆、睡着。默认角色是程序用 QPainter 画的原创小动物，**仓库里不携带任何有版权的图片**，开箱即用。安装运行：

```bash
pip install -e .
desktop-pet
```

换角色图用 `desktop-pet --image 你的图.png`（建议透明背景 PNG）。
