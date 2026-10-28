"""Enforce repository rules that the agent instructions delegate to CI."""

import ast
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


def registry_entries(source: str) -> dict[str, tuple[str, ...]]:
    """Map key -> (value, unit, status, uncertainty) of every REGISTRY entry.

    Comments, source text and effect text are not part of the entry.
    """
    entries: dict[str, tuple[str, ...]] = {}
    for node in ast.parse(source).body:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(t, ast.Name) and t.id == "REGISTRY" for t in node.targets)):
            continue
        for key, call in zip(node.value.keys, node.value.values):
            name = ast.literal_eval(key)
            if isinstance(call, ast.Call) and len(call.args) >= 5 and not call.keywords:
                fields = (call.args[0], call.args[1], call.args[3], call.args[4])
                entries[name] = tuple(ast.dump(field) for field in fields)
            else:
                entries[name] = (ast.dump(call),)
    return entries


def changed_entries(old_source: str, new_source: str) -> list[str]:
    old, new = registry_entries(old_source), registry_entries(new_source)
    return sorted(key for key in old.keys() | new.keys() if old.get(key) != new.get(key))


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
            if REGISTRY in changed:
                old_registry = git("show", f"{base}:{REGISTRY}")
                new_registry = (ROOT / REGISTRY).read_text(encoding="utf-8")
                entry_changes = changed_entries(old_registry, new_registry)
                if entry_changes and not any(path.startswith("tests/") for path in changed):
                    errors.append(
                        f"{REGISTRY} entries changed without a corresponding tests/ change: "
                        + ", ".join(entry_changes)
                    )
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
