"""Enforce repository rules that the agent instructions delegate to CI."""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "tests"
REGISTRY = "src/verlustmappe/registry.py"
SOURCES = ROOT / "SOURCES.md"
TEST_SKIP = re.compile(
    r"pytest\.mark\.(?:skip|skipif|xfail)\b"
    r"|@unittest\.(?:skip|skipIf|skipUnless|expectedFailure)\b"
    r"|(?:pytest\.)?(?:skip|xfail)\s*\("
    r"|\.skipTest\s*\("
)
REGISTRY_KEY = re.compile(r"""^\s*["']([^"']+)["']\s*:\s*P\(""", re.MULTILINE)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def base_ref() -> str | None:
    supplied = os.environ.get("BASE_REF")
    if supplied:
        return supplied
    try:
        git("rev-parse", "--verify", "origin/main")
    except subprocess.CalledProcessError:
        return None
    return "origin/main"


def base_tests(base: str) -> set[str]:
    names = git("ls-tree", "-r", "--name-only", base, "--", "tests").splitlines()
    return {
        name for name in names
        if Path(name).parent == Path("tests")
        and Path(name).name.startswith("test_")
        and Path(name).suffix == ".py"
    }


def registry_keys(source: str) -> set[str]:
    return set(REGISTRY_KEY.findall(source))


def main() -> int:
    errors: list[str] = []
    tests = sorted(TEST_DIR.glob("test_*.py"))

    for test in tests:
        if TEST_SKIP.search(test.read_text(encoding="utf-8")):
            errors.append(f"skip/xfail marker found in {test.relative_to(ROOT)}")

    base = base_ref()
    changed: set[str] = set()
    if base:
        try:
            changed = set(git("diff", "--name-only", f"{base}...HEAD").splitlines())
            prior_tests = base_tests(base)
            current_tests = {
                path.relative_to(ROOT).as_posix() for path in tests
            }
            removed_tests = sorted(prior_tests - current_tests)
            if removed_tests:
                errors.append(
                    "test files removed: " + ", ".join(removed_tests)
                )
            if len(tests) < len(prior_tests):
                errors.append(
                    f"test-file count decreased from {len(prior_tests)} to {len(tests)}"
                )
            if REGISTRY in changed and not any(path.startswith("tests/") for path in changed):
                errors.append(f"{REGISTRY} changed without a corresponding tests/ change")

            if REGISTRY in changed:
                old_registry = git("show", f"{base}:{REGISTRY}")
                new_registry = (ROOT / REGISTRY).read_text(encoding="utf-8")
                new_keys = registry_keys(new_registry) - registry_keys(old_registry)
                if new_keys:
                    if not SOURCES.is_file():
                        errors.append("SOURCES.md is required for new registry entries")
                    else:
                        sources_text = SOURCES.read_text(encoding="utf-8")
                        missing = sorted(key for key in new_keys if f"`{key}`" not in sources_text)
                        if missing:
                            errors.append(
                                "new registry keys missing from SOURCES.md: "
                                + ", ".join(missing)
                            )
        except subprocess.CalledProcessError as exc:
            errors.append(f"could not inspect base revision {base}: {exc.stderr.strip()}")
    else:
        print("No base ref available; skipping diff-based registry/test guards.")

    if errors:
        print("CI guard failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"CI guard passed: {len(tests)} test files; no skip/xfail markers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
