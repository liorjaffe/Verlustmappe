"""Architecture rules (AGENTS.md). Each rule here replaces a rule that would otherwise only
live in text and decay."""
import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "verlustmappe"

TOP_LEVEL = {
    "AGENTS.md", "CLAUDE.md", "CONTRACT.md", "LICENSE", "README.md", "START.md",
    "pyproject.toml", "data", "decisions", "plant", "src", "tests", "tools",
}
PACKAGES = {"accounting", "devices", "hydrogen", "loaders", "physics", "scenarios"}


def _visible(path):
    return sorted(p.name for p in path.iterdir()
                  if not p.name.startswith(".") and p.name != "__pycache__")


def test_top_level_stays_small():
    assert set(_visible(ROOT)) <= TOP_LEVEL, set(_visible(ROOT)) - TOP_LEVEL


def test_package_has_only_the_named_subpackages():
    dirs = {n for n in _visible(PKG) if (PKG / n).is_dir()}
    assert dirs == PACKAGES, dirs


def test_every_device_model_has_a_plant_file_of_the_same_name():
    models = {p.stem for p in (PKG / "devices").glob("*.py") if not p.stem.startswith("_")}
    plant = {p.stem for p in (ROOT / "plant").glob("*.toml")}
    assert models - plant == set(), models - plant


def test_plant_files_carry_their_own_name():
    for path in (ROOT / "plant").glob("*.toml"):
        with path.open("rb") as fh:
            assert tomllib.load(fh)["device"]["name"] == path.stem, path.name


def test_physics_is_the_lowest_layer():
    for path in (PKG / "physics").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.level:
                assert node.level == 1, f"{path.name} imports from outside physics/"
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("verlustmappe"), path.name
            if isinstance(node, ast.Import):
                assert not any(a.name.startswith("verlustmappe") for a in node.names), path.name


def test_entry_files_stay_short():
    assert len((ROOT / "START.md").read_text(encoding="utf-8").splitlines()) <= 60
    # Owner decision 2026-11-13: fixed size and line-length budget for AGENTS.md.
    # Owner 2026-11-20: raised 8_200 -> 8_400 to allow a few more lines.
    agents_max_characters = 8_400
    agents_max_line_characters = 100
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert len(agents_text) <= agents_max_characters
    assert all(len(line) <= agents_max_line_characters for line in agents_text.splitlines())
