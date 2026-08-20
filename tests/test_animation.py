# -*- coding: utf-8 -*-
from pet import animation


def _close(a, b, tol=1e-6):
    return abs(a - b) < tol


def test_jump_identity_at_ends():
    assert _close(animation.jump_transform(0.0)[1], 0.0)
    assert _close(animation.jump_transform(1.0)[1], 0.0)


def test_jump_peak_at_midpoint():
    assert _close(animation.jump_transform(0.5)[1], -62.0)


def test_jump_scales_with_zoom():
    assert _close(animation.jump_transform(0.5, zoom=2.0)[1], -124.0)


def test_jump_never_scales():
    assert animation.jump_transform(0.3)[2:] == (1.0, 1.0)


def test_jump_is_symmetric():
    for t in (0.1, 0.25, 0.4):
        assert _close(animation.jump_transform(t)[1], animation.jump_transform(1 - t)[1])


def test_squash_identity_at_ends():
    assert animation.squash_transform(0.0)[2:] == (1.0, 1.0)
    assert animation.squash_transform(1.0)[2:] == (1.0, 1.0)


def test_squash_midpoint_wide_and_short():
    assert _close(animation.squash_transform(0.5)[2], 1.30)
    assert _close(animation.squash_transform(0.5)[3], 0.72)


def test_shake_zero_at_ends():
    assert _close(animation.shake_transform(0.0)[0], 0.0)
    assert _close(animation.shake_transform(1.0)[0], 0.0)


def test_shake_scales_with_zoom():
    assert _close(animation.shake_transform(0.5, zoom=2.0)[0], 2 * animation.shake_transform(0.5)[0])


def test_idle_sway_rocks_horizontally():
    assert _close(animation.idle_transform(0.25, "sway")[0], 7.0)
    assert animation.idle_transform(0.25, "sway")[2:] == (1.0, 1.0)


def test_idle_breath_scales():
    assert _close(animation.idle_transform(0.25, "breath")[2], 1.035)
    assert _close(animation.idle_transform(0.25, "breath")[3], 0.965)


def test_walk_bounce_starts_flat_and_stays_negative():
    assert _close(animation.walk_bounce(0), 0.0)
    for step in (1, 2, 5, 10):
        assert animation.walk_bounce(step) <= 0.0
