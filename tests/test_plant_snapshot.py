"""Drift guard against the owner-approved parameter reference, not proof of physics.

Update the reference only for approved changes; Git preserves historical versions.
Runtime loads TOML, never this reference.
"""
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SNAPSHOT = json.loads(
    (ROOT / "tests/reference/plant_parameter_reference.json").read_text(encoding="utf-8"))
FIELDS = ("value", "unit", "source", "status", "uncertainty", "effect")


def _plant():
    data = {}
    for path in sorted((ROOT / "plant").glob("*.toml")):
        with path.open("rb") as fh:
            data[path.stem] = tomllib.load(fh)
    return data


def _params():
    return {k: p for d in _plant().values() for k, p in d.get("param", {}).items()}


def test_registry_keys_identical():
    from verlustmappe import registry as R
    assert set(R.REGISTRY) == set(SNAPSHOT["registry"])
    assert len(R.REGISTRY) == 131


def test_every_field_identical_including_type():
    from verlustmappe import registry as R
    for key, expected in SNAPSHOT["registry"].items():
        actual = R.REGISTRY[key]
        for field in FIELDS:
            assert actual[field] == expected[field], (key, field)
            assert type(actual[field]) is type(expected[field]), (key, field)


def test_sources_entries_identical():
    params = _params()
    assert len(SNAPSHOT["sources"]) == 22
    for key, expected in SNAPSHOT["sources"].items():
        assert params[key]["sources_md"] == expected, key


def test_source_blocks_identical():
    plant = _plant()
    for device, expected in SNAPSHOT["source_blocks"].items():
        assert plant[device]["source_block"] == expected, device


def test_param_tables_have_only_known_fields():
    for key, p in _params().items():
        # uncertainty_open: owner 2026-11-19 (decisions/2026-11-19-uncertainty-open-register.md)
        assert set(p) <= set(FIELDS) | {"sources_md", "uncertainty_open"}, key
