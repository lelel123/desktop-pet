# -*- coding: utf-8 -*-
from pet import config


def test_roundtrip(tmp_path):
    p = tmp_path / "cfg.json"
    config.save_config({"zoom": 1.5, "pos": [10, 20], "topmost": False}, p)
    assert config.load_config(p) == {"zoom": 1.5, "pos": [10, 20], "topmost": False}


def test_missing_file_returns_empty(tmp_path):
    assert config.load_config(tmp_path / "nope.json") == {}


def test_corrupt_json_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{this is not json", encoding="utf-8")
    assert config.load_config(p) == {}


def test_non_dict_json_returns_empty(tmp_path):
    p = tmp_path / "list.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert config.load_config(p) == {}


def test_save_creates_parent_dirs(tmp_path):
    p = tmp_path / "a" / "b" / "cfg.json"
    config.save_config({"x": 1}, p)
    assert p.exists()
    assert config.load_config(p) == {"x": 1}
