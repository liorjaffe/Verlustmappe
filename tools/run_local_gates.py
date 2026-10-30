"""Run the repository's required local checks and preserve their output."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    name: str
    arguments: tuple[str, ...]
    environment: tuple[tuple[str, str], ...] = ()


CHECKS = (
    Check("legacy", (sys.executable, "tests/run_all.py")),
    Check("pytest", (sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider")),
    Check(
        "ci_guard",
        (sys.executable, "tools/ci_guard.py"),
        (("BASE_REF", "origin/main"),),
    ),
    Check("readme", (sys.executable, "tools/make_readme_demo.py", "--check")),
    Check("diff_check", ("git", "diff", "--check")),
    Check("staged_diff_check", ("git", "diff", "--cached", "--check")),
)


def _last_line(text: str) -> str:
    lines = text.rstrip().splitlines()
    return lines[-1] if lines else "(no output)"


def _run_checks(log_dir: Path, checks: tuple[Check, ...] = CHECKS) -> bool:
    log_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, int, str]] = []

    for check in checks:
        environment = os.environ.copy()
        environment.update(dict(check.environment))
        completed = subprocess.run(
            check.arguments,
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = completed.stdout or ""
        (log_dir / f"{check.name}.log").write_text(output, encoding="utf-8")
        results.append((check.name, completed.returncode, _last_line(output)))

    failed = False
    for name, returncode, last_line in results:
        print(f"{name}: {last_line} exit={returncode}")
        failed = failed or returncode != 0

    if failed:
        print(f"GATES FAILED; full logs: {log_dir}")
        return False
    print(f"GATES OK; full logs: {log_dir}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run required local checks; this helper is not part of CI."
    )
    parser.add_argument(
        "--log-dir",
        required=True,
        type=Path,
        help="directory outside the repository where per-check logs are written",
    )
    args = parser.parse_args()
    log_dir = args.log_dir.expanduser().resolve()
    if log_dir == REPO_ROOT or REPO_ROOT in log_dir.parents:
        parser.error("--log-dir must be outside the repository")
    return 0 if _run_checks(log_dir) else 1


if __name__ == "__main__":
    raise SystemExit(main())
