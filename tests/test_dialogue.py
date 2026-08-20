# -*- coding: utf-8 -*-
from pet import dialogue


def test_parse_skips_comments_and_blank_lines():
    text = "# comment\n\nhello\nworld\n\n# another\n"
    assert dialogue.parse_dialogues(text) == ["hello", "world"]


def test_load_from_file(tmp_path):
    p = tmp_path / "dialogues.txt"
    p.write_text("# c\nline1\nline2\n", encoding="utf-8")
    assert dialogue.load_dialogues(p) == ["line1", "line2"]


def test_load_missing_file_returns_defaults(tmp_path):
    assert dialogue.load_dialogues(tmp_path / "nope.txt") == dialogue.default_dialogues()


def test_load_all_comments_returns_defaults(tmp_path):
    p = tmp_path / "comments-only.txt"
    p.write_text("# just a comment\n# another\n", encoding="utf-8")
    assert dialogue.load_dialogues(p) == dialogue.default_dialogues()


def test_defaults_are_nonempty_and_comment_free():
    defaults = dialogue.default_dialogues()
    assert len(defaults) > 0
    assert all(not line.startswith("#") for line in defaults)
