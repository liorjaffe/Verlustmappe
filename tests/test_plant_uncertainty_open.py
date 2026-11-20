"""`uncertainty_open` field (owner 2026-11-19, decisions/2026-11-19-uncertainty-open-register.md).

Schema guard only: where present the field is non-empty text, and the listing tool
finds exactly those parameters. Not a check of any uncertainty value.
"""
import importlib.util
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "list_open_uncertainties.py"


def _tool():
    spec = importlib.util.spec_from_file_location("list_open_uncertainties", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _declared():
    keys = set()
    for path in (ROOT / "plant").glob("*.toml"):
        with path.open("rb") as fh:
            for key, p in tomllib.load(fh).get("param", {}).items():
                if "uncertainty_open" in p:
                    text = p["uncertainty_open"]
                    assert isinstance(text, str) and text.strip(), key
                    keys.add(key)
    return keys


def test_field_is_nonempty_text_and_tool_lists_exactly_those_keys():
    registered, unreviewed, total = _tool().collect()
    assert {row[1] for row in registered} == _declared()
    assert not {row[1] for row in registered} & {row[1] for row in unreviewed}
    assert len(registered) + len(unreviewed) <= total


def test_el_open_items_registered():
    # owner 2026-11-19: all ten EL parameters carry an open uncertainty item
    with (ROOT / "plant/el.toml").open("rb") as fh:
        params = tomllib.load(fh)["param"]
    assert all("uncertainty_open" in p for p in params.values())
    assert len(params) == 10
