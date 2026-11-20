"""List plant parameters whose uncertainty is open, for a later detailed review.

Read-only, manual, stdout only (owner 2026-11-19,
decisions/2026-11-19-uncertainty-open-register.md). Reads plant/*.toml with tomllib;
does not import the simulation and prints no parameter values or uncertainties.

Two groups, each with its own count and denominator:
1. Parameters with an `uncertainty_open` text (registered open item).
2. Parameters with uncertainty 0.0 but no `uncertainty_open` text: not yet reviewed;
   0.0 can mean NOT ASSESSED, a bound, a constant or an exact definition.

Usage: python tools/list_open_uncertainties.py [--markdown]
"""
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect(plant_dir=ROOT / "plant"):
    registered, unreviewed, total = [], [], 0
    for path in sorted(plant_dir.glob("*.toml")):
        with path.open("rb") as fh:
            params = tomllib.load(fh).get("param", {})
        for key, p in params.items():
            total += 1
            row = (path.name, key, p.get("status", ""), p.get("source", ""))
            text = p.get("uncertainty_open")
            if text is not None:
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"{path.name}: {key}: uncertainty_open must be non-empty text")
                registered.append(row + (text,))
            elif p.get("uncertainty") == 0.0:
                unreviewed.append(row)
    return registered, unreviewed, total


def main(argv):
    md = "--markdown" in argv
    registered, unreviewed, total = collect()
    print(f"# Open uncertainties ({total} plant parameters)\n" if md
          else f"Open uncertainties - {total} plant parameters")
    print(f"\n{'## ' if md else ''}1. Registered open items: {len(registered)} of {total}\n")
    for f, key, status, source, text in registered:
        print(f"- {key} [{status}] ({f})" if md else f"{key}  [{status}]  {f}")
        print(f"  open: {text}")
        print(f"  source: {source}\n")
    print(f"{'## ' if md else ''}2. Uncertainty 0.0 without an open-item text "
          f"(not yet reviewed): {len(unreviewed)} of {total}\n")
    for f, key, status, _ in unreviewed:
        print(f"- {key} [{status}] ({f})" if md else f"{key}  [{status}]  {f}")
    print("\nDisplay only: not a review, assessment or validation.")


if __name__ == "__main__":
    main(sys.argv[1:])
