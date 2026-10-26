# P03 - Restore the tank-volume override in two legacy tests

**Status:** Complete (tests commit `1afd616`, docs commit `b705ae3`, merge `8bd06ef`; owner acceptance executed locally on the branch before merge)
**Reference:** ROADMAP.md, M0; docs/94_known_defects_legacy.md, C9;
AGENTS.md, rules 4 and 6.
**Patch base:** `d3a16bab51875d0d77f274d835958f01d23cde72`.
**Preconditions:** Owner approval to edit the two protected test files.
Tests are outside D2's src/ freeze; rule 4 requires a dedicated tests-only
commit with the reason in the commit message. No src/ file is changed.

## Goal

In `test_02` and `test_03`, restore
`R.REGISTRY["stor.volume_L"]["value"]` to its value on entry to `main()`,
after both normal execution and exceptions. Do not hard-code 800 in the
wrapper: it is the baseline registry value, not necessarily the caller's
value. No other test behavior is changed.

## Write-Scope

- `tests/test_02_hydrogen_routes.py`: rename main to _body; add main wrapper.
- `tests/test_03_full_chain.py`: the same minimal change.
- `docs/94_known_defects_legacy.md`: introductory paragraph, C9 entry,
  and C9 row of the AC8 table only.
- `tasks/P03_c9_registry_leak_fix.md`: this task and its acceptance evidence.

## Do not touch

Do not edit src/, registry values, other tests, tools/, README.md, SPEC.md,
AGENTS.md, DECISIONS.md, ROADMAP.md or SOURCES.md. Leave all original test
bodies, assertions, tolerances, imports, printouts and script entry points
unchanged. In particular, do not repair the known C4 tautology.
HANDOFF.md is a separate follow-up after acceptance, with real commit hashes.

## Work items

1. Before editing, list failure modes: failure before restoration, restoring
   800 instead of the entry value, swallowed exceptions, unintended edits to
   assertions, and collision with an existing untracked task draft.
2. In each test, rename `def main():` to `def _body():`. Keep the entire body
   unchanged and insert this wrapper immediately before the existing script
   entry point:

```python
def main():
    _orig = R.REGISTRY["stor.volume_L"]["value"]
    try:
        _body()
    finally:
        R.REGISTRY["stor.volume_L"]["value"] = _orig
```

3. Keep `if __name__ == "__main__": main()` unchanged.
4. Document C9 as a historical baseline defect, fixed in the P03 working
   version. Distinguish the protected tests correction from D2's src/ freeze.
   Keep the baseline tag unchanged; C11 text cleanup remains planned.
5. Use two separate commits: first only the two test files; then docs/94 and
   this task. Stage explicit filenames, never whole directories.
6. After local owner acceptance, update this task's status and HANDOFF.md in
   a separate follow-up; do not insert a commit's own hash into that commit.

## Acceptance

Run from the repository root. If a patch hunk or any check fails, stop: do not
continue to the next commit or merge. Preserve an existing untracked task
before applying the patch; git apply does not silently overwrite it.

After the tests-only commit, run all three gates below. Repeat them after the
documentation commit and run the Python check below before any merge.
The guard compares committed HEAD with the pinned base, so a dirty-working-
tree-only check is not sufficient evidence for its diff-based rules.

```bash
python3 tests/run_all.py
BASE_REF=d3a16bab51875d0d77f274d835958f01d23cde72 python3 tools/ci_guard.py
python3 tools/make_readme_demo.py --check
```

All commands must exit 0; the first must end with ALL PASS.
This check proves the exact permitted edits, then executes both modules in
one process and checks restoration on normal and exceptional paths. The
exception must propagate; replaced bodies and the initial value are restored.
Copy the complete block, including the unindented closing PY line.

```bash
python3 - <<'PY'
import subprocess
import sys
from pathlib import Path

if not __debug__:
    raise RuntimeError("Run this check without Python optimisation (-O).")

base = "d3a16bab51875d0d77f274d835958f01d23cde72"
paths = ("tests/test_02_hydrogen_routes.py", "tests/test_03_full_chain.py")
wrapper = (
    'def main():\n'
    '    _orig = R.REGISTRY["stor.volume_L"]["value"]\n'
    '    try:\n'
    '        _body()\n'
    '    finally:\n'
    '        R.REGISTRY["stor.volume_L"]["value"] = _orig\n\n'
)
entry = 'if __name__ == "__main__": main()'
for path in paths:
    old = subprocess.check_output(["git", "show", f"{base}:{path}"])
    assert old.count(b"def main():\n") == 1, path
    assert old.count(entry.encode()) == 1, path
    expected = old.replace(b"def main():\n", b"def _body():\n", 1)
    expected = expected.replace(entry.encode(), wrapper.encode() + entry.encode(), 1)
    assert Path(path).read_bytes() == expected, f"Unexpected edit: {path}"
print("EXACT TEST EDIT CHECK PASS (original bodies and assertions unchanged)")

sys.path[:0] = ["tests", "src"]
import _path
import test_02_hydrogen_routes as t02
import test_03_full_chain as t03
from verlustmappe import registry as R

key = "stor.volume_L"
initial = R.REGISTRY[key]["value"]
assert initial == 800, f"Unexpected baseline registry value: {initial}"

class DeliberateFailure(Exception):
    pass

try:
    # 777 is a test-only sentinel, not an approved physical parameter.
    for prior in (initial, 777):
        R.REGISTRY[key]["value"] = prior
        for module in (t02, t03):
            module.main()
            assert R.REGISTRY[key]["value"] == prior, module.__name__
            original_body = module._body
            failure = DeliberateFailure(module.__name__)

            def failing_body():
                R.REGISTRY[key]["value"] = 1000.0
                raise failure

            module._body = failing_body
            try:
                try:
                    module.main()
                except DeliberateFailure as caught:
                    assert caught is failure
                else:
                    raise AssertionError(f"Exception swallowed: {module.__name__}")
                assert R.REGISTRY[key]["value"] == prior, module.__name__
            finally:
                module._body = original_body
            print(f"{module.__name__}: normal and failure paths restore {prior}")
finally:
    R.REGISTRY[key]["value"] = initial
print("SAME-PROCESS AND FAILURE-PATH CHECK PASS (both modules)")
PY
```

Required: exit 0, EXACT TEST EDIT CHECK PASS and
SAME-PROCESS AND FAILURE-PATH CHECK PASS. This is stronger than counting
removed assert lines; a zero-match grep also exits 1 and is not a gate here.

Inspect the full branch diff and commit split:

```bash
git --no-pager diff --stat d3a16bab51875d0d77f274d835958f01d23cde72..HEAD
git --no-pager diff d3a16bab51875d0d77f274d835958f01d23cde72..HEAD -- tests/test_02_hydrogen_routes.py tests/test_03_full_chain.py
git --no-pager log --stat d3a16bab51875d0d77f274d835958f01d23cde72..HEAD
```

On the pinned base, exactly the four Write-Scope paths change. If the branch
contains unrelated work, review the actual base before proceeding; do not
fold that work into P03. Do not merge or push main before the owner review.

## Completion evidence

Record actual commit hashes, all gate outputs, the Python check output,
changed paths and commit separation in the AGENTS.md report format.
List UNVERIFIED items explicitly; do not predeclare that there are none.
The baseline tag and frozen model behavior are not changed or validated
physically by this state-isolation fix.
