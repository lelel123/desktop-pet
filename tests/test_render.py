# -*- coding: utf-8 -*-
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from pet import render


def _alpha(img, x, y):
    """Alpha channel at (x, y), robust to premultiplied formats."""
    return img.pixelColor(x, y).alpha()


def _has_opaque_pixels(pm):
    img = pm.toImage()
    for y in range(img.height()):
        for x in range(0, img.width(), 4):
            if _alpha(img, x, y) > 0:
                return True
    return False


def test_default_pixmap_size(qapp):
    pm = render.make_default_pixmap()
    assert not pm.isNull()
    assert pm.height() == render.DEFAULT_BASE_H
    assert pm.width() > 0


def test_default_pixmap_has_content(qapp):
    assert _has_opaque_pixels(render.make_default_pixmap())


def test_default_pixmap_corners_transparent(qapp):
    pm = render.make_default_pixmap()
    img = pm.toImage()
    assert _alpha(img, 0, 0) == 0
    assert _alpha(img, pm.width() - 1, pm.height() - 1) == 0
    assert _alpha(img, 0, pm.height() - 1) == 0


def test_default_pixmap_scales_to_height(qapp):
    pm = render.make_default_pixmap(120)
    assert pm.height() == 120


def test_create_pixmap_default(qapp):
    assert not render.create_pixmap().isNull()


def test_create_pixmap_loads_image(qapp, tmp_path):
    src = render.make_default_pixmap(120)
    path = tmp_path / "char.png"
    assert src.save(str(path))
    loaded = render.create_pixmap(path, 120)
    assert loaded.height() == 120


def test_load_pixmap_missing_raises(qapp):
    with pytest.raises(FileNotFoundError):
        render.load_pixmap("definitely-not-a-real-file.png")
