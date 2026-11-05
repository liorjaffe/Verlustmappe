"""Parameterzugriff. Einzige Wertquelle ist plant/<geraet>.toml (seit 2026-11-05).

Die Schnittstelle ist unveraendert: REGISTRY, get, entry, by_status, P. Jeder Eintrag
hat value, unit, source, status, uncertainty, effect. Fehlt 'value' in der TOML-Datei,
ist der Wert MISSING und wird als None gelesen. Werte aendert nur der Owner.
"""
import tomllib
from pathlib import Path

PLANT_DIR = Path(__file__).resolve().parents[2] / "plant"


def P(value, unit, source, status, uncertainty, effect):
    return dict(value=value, unit=unit, source=source, status=status,
                uncertainty=uncertainty, effect=effect)


def _load(plant_dir: Path) -> dict:
    registry = {}
    for path in sorted(plant_dir.glob("*.toml")):
        with path.open("rb") as fh:
            params = tomllib.load(fh).get("param", {})
        for key, p in params.items():
            if key in registry:
                raise ValueError(f"duplicate parameter {key!r} in {path.name}")
            registry[key] = P(p.get("value"), p["unit"], p["source"], p["status"],
                              p["uncertainty"], p["effect"])
    return registry


REGISTRY = _load(PLANT_DIR)


def get(key):
    return REGISTRY[key]["value"]


def entry(key):
    return REGISTRY[key]


def by_status(status):
    return {k: v for k, v in REGISTRY.items() if v["status"] == status}
