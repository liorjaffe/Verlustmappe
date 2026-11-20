"""Observer summary row (decisions/2026-11-19-observer-project-summary.md)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("overview_gen", ROOT / "tools/project_observer/overview_gen.py")
ov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ov)


def test_repository_summary_has_three_fields_in_fixed_order():
    s = ov.load_summary(ROOT / "tools/project_observer/summary.toml")
    assert s["found"] and s["error"] is None
    assert [i["label"] for i in s["items"]] == ["My goal", "What I have to do", "Where I am at"]


def test_text_is_shown_verbatim(tmp_path):
    p = tmp_path / "summary.toml"
    p.write_text('status = "  Now: linking devices; no measurements yet.  "\ngoal = "G"\n', encoding="utf-8")
    s = ov.load_summary(p)
    assert s["items"] == [{"label": "My goal", "text": "G"},
                          {"label": "Where I am at", "text": "Now: linking devices; no measurements yet."}]


def test_missing_file_shows_no_row(tmp_path):
    assert ov.load_summary(tmp_path / "none.toml") == {"found": False, "items": [], "error": None}


def test_read_errors_and_unknown_keys_are_reported(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("goal = ", encoding="utf-8")
    assert ov.load_summary(bad)["error"]
    odd = tmp_path / "odd.toml"
    odd.write_text('goal = "G"\nextra = "x"\n', encoding="utf-8")
    assert "extra" in ov.load_summary(odd)["error"]


def test_header_renders_the_summary_row():
    assert "D.summary.items" in ov.TEMPLATE
