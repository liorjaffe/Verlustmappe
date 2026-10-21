"""Generate or check the README demo table from the synthetic full-chain test."""

import argparse
import contextlib
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TEST = ROOT / "tests" / "test_03_full_chain.py"
BEGIN = "<!-- BEGIN GENERATED DEMO TABLE -->"
END = "<!-- END GENERATED DEMO TABLE -->"
BAR_LINE = re.compile(r"^\s{6}(.+?)\s+(-?\d+(?:\.\d+)?) kWh\s+\[([^\]]+)\]$")


def generated_content() -> str:
    sys.path.insert(0, str(TEST.parent))
    try:
        from test_03_full_chain import main as run_full_chain_test
    except ImportError as exc:
        raise RuntimeError(f"could not import the synthetic full-chain test: {exc}") from exc

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        run_full_chain_test()

    summary = next(
        (line.strip() for line in output.getvalue().splitlines()
         if line.startswith("PASS 03 full chain:")),
        None,
    )
    rows = [match.groups() for line in output.getvalue().splitlines()
            if (match := BAR_LINE.match(line))]
    if summary is None or not rows:
        raise RuntimeError("full-chain test output did not contain the expected summary and bars")

    table = [
        "| Stage | kWh | Status |",
        "|---|---:|---|",
        *(f"| {stage.strip()} | {energy} | {status} |" for stage, energy, status in rows),
    ]
    return "\n".join([*table, "", f"**Demo summary:** {summary}"])


def update_or_check(check: bool) -> None:
    text = README.read_text(encoding="utf-8")
    marker = re.compile(
        rf"(?m)^{re.escape(BEGIN)}\n(.*?)\n{re.escape(END)}$",
        re.DOTALL,
    )
    match = marker.search(text)
    if match is None:
        raise RuntimeError(f"README must contain {BEGIN} and {END} on separate lines")

    expected = generated_content()
    actual = match.group(1)
    if check:
        if actual != expected:
            raise RuntimeError(
                "README generated demo is stale; run `python3 tools/make_readme_demo.py`"
            )
        print("README generated demo matches tests/test_03_full_chain.py")
        return

    README.write_text(
        text[:match.start(1)] + expected + text[match.end(1):],
        encoding="utf-8",
    )
    print("Updated README generated demo from tests/test_03_full_chain.py")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the README demo differs from the test output")
    args = parser.parse_args()
    try:
        update_or_check(args.check)
    except (OSError, RuntimeError) as exc:
        print(f"README demo check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
