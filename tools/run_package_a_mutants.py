"""Reproduce the bounded P14 Package A mutation checks in isolated copies."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = "tests/test_40_static_ledger.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    source: str
    old: str
    new: str
    selector: str
    selected_cases: int
    approval_reference: str
    option: str | None = None


MUTATIONS = (
    # Package A approvals are recorded in bfdaf38 (HANDOFF.md).
    Mutation(
        "M1_faraday_operating_time",
        "src/verlustmappe/models/static_map.py",
        '* values["operating_time_s"]\n                         / (2 * F_C_PER_MOL)',
        '* 2700\n                         / (2 * F_C_PER_MOL)',
        "test_doubled_operating_time_doubles_electrical_and_faraday_results or "
        "test_zero_operating_time_zeros_electrical_and_faraday_results",
        2,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "M2_electrical_operating_time",
        "src/verlustmappe/models/static_map.py",
        'value = values["el_ac_input_power_W"] * values["operating_time_s"] / J_PER_KWH',
        'value = values["el_ac_input_power_W"] * 2700 / J_PER_KWH',
        "test_doubled_operating_time_doubles_electrical_and_faraday_results or "
        "test_zero_operating_time_zeros_electrical_and_faraday_results",
        2,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "M4_negative_registry_gate",
        "src/verlustmappe/models/static_map.py",
        "elif not check_nonnegative(parameter.value, key):",
        "elif False:",
        "test_negative_registry_parameter_has_exact_domain_cause_and_propagates",
        1,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "M14_report_scope_guard",
        "src/verlustmappe/models/ledger.py",
        'if self.scope not in ("bounded", "full"):',
        "if False:",
        "test_report_rejects_invalid_scope_with_complete_results",
        1,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "M6_aggregate_finite_guard",
        "src/verlustmappe/models/ledger.py",
        '    check_nonnegative(total, "aggregate")',
        "    pass",
        "test_aggregate_rejects_overflow_from_finite_results",
        1,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "MB_silent_status_default",
        "src/verlustmappe/models/status.py",
        (
            "    if not ranked:\n"
            "        raise ValueError(\"no evidence status among the inputs (empty or "
            "OWNER_DECISION only); \"\n"
            "                         \"D26 defines no default, classification needs a "
            "DECISIONS entry\")"
        ),
        '    if not ranked:\n        return "GUESS"',
        "test_computed_requires_evidence_status_before_sign_handling",
        4,
        "bfdaf38: HANDOFF.md, Package A owner approval",
    ),
    Mutation(
        "M_items_key_uniqueness",
        "src/verlustmappe/models/ledger.py",
        "BOUNDED_KEYS = tuple(item.key for item in ITEMS[:5])",
        "ITEMS = ITEMS + (ITEMS[0],)\n"
        "BOUNDED_KEYS = tuple(item.key for item in ITEMS[:5])",
        "test_inventory_item_keys_are_unique",
        1,
        "owner-chat 2026-10-30: explicit opt-in scope agreement; separate from bfdaf38",
        "include_inventory_uniqueness",
    ),
)

SUMMARY_DURATION_RE = re.compile(r"^(?P<body>.+) in (?P<duration>\d+(?:\.\d+)?s)$")
NO_TESTS_RE = re.compile(r"^no tests ran in \d+(?:\.\d+)?s$")
SUMMARY_OUTCOME_RE = re.compile(
    r"^(?P<count>\d+) "
    r"(?P<outcome>passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?)$"
)


@dataclass(frozen=True)
class TestSummary:
    outcomes: dict[str, int]
    line: str
    no_tests_ran: bool = False

    @property
    def selected_cases(self) -> int:
        return sum(
            self.outcomes.get(key, 0)
            for key in ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
        )


class EvidenceError(RuntimeError):
    """A test run did not satisfy the mutation evidence contract."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _expect_evidence_error(
    expected_reason: str,
    action: Callable[[], object],
    context: str,
) -> None:
    try:
        action()
    except EvidenceError as error:
        if error.reason != expected_reason:
            raise EvidenceError(
                "self_check_failed",
                f"{context} was rejected for {error.reason}, "
                f"expected {expected_reason}",
            ) from error
    else:
        raise EvidenceError(
            "self_check_failed",
            f"{context} was accepted; expected {expected_reason}",
        )


def _parse_summary(output: str) -> TestSummary:
    summaries: list[TestSummary] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if NO_TESTS_RE.fullmatch(line):
            summaries.append(TestSummary({}, line, no_tests_ran=True))
            continue
        duration_match = SUMMARY_DURATION_RE.fullmatch(line)
        if duration_match is None:
            continue
        body = duration_match.group("body")
        outcomes: dict[str, int] = {}
        for token in body.split(", "):
            match = SUMMARY_OUTCOME_RE.fullmatch(token)
            if match is None:
                outcomes = {}
                break
            outcome = match.group("outcome")
            key = "error" if outcome.startswith("error") else (
                "warning" if outcome.startswith("warning") else outcome
            )
            if key in outcomes:
                raise EvidenceError(
                    "summary_invalid",
                    f"duplicate pytest summary category {key!r}: {line}",
                )
            outcomes[key] = int(match.group("count"))
        if outcomes:
            summaries.append(TestSummary(outcomes, line))

    if not summaries:
        raise EvidenceError(
            "summary_missing",
            "pytest output did not contain a recognized complete summary line",
        )
    if len(summaries) != 1:
        raise EvidenceError(
            "summary_ambiguous",
            f"pytest output contained {len(summaries)} recognized summary lines",
        )
    return summaries[0]


def _validate_baseline(
    returncode: int, summary: TestSummary, expected_cases: int,
) -> None:
    if returncode == 5 and summary.selected_cases == 0:
        raise EvidenceError(
            "no_selected_tests",
            f"pytest selected no tests (exit=5, summary={summary.line!r})",
        )
    if (
        returncode != 0
        or summary.outcomes.get("passed") != expected_cases
        or summary.selected_cases != expected_cases
    ):
        raise EvidenceError(
            "baseline_invalid",
            f"baseline must pass exactly {expected_cases} selected cases "
            f"(exit={returncode}, summary={summary.line!r})",
        )


def _validate_mutant(
    returncode: int, summary: TestSummary, expected_cases: int,
) -> None:
    if returncode == 5 and summary.selected_cases == 0:
        raise EvidenceError(
            "no_selected_tests",
            f"mutant selector selected no tests (exit=5, summary={summary.line!r})",
        )
    if (
        returncode != 1
        or summary.outcomes.get("failed") != expected_cases
        or summary.selected_cases != expected_cases
    ):
        raise EvidenceError(
            "mutant_invalid",
            f"mutant kill requires pytest exit 1 and exactly {expected_cases} "
            f"failed selected cases (exit={returncode}, summary={summary.line!r})",
        )


def _run_pytest(
    python: str,
    cwd: Path,
    test_file: str,
    selector: str | None = None,
) -> subprocess.CompletedProcess[str]:
    arguments = [
        python, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_file,
    ]
    if selector is not None:
        arguments.extend(("-k", selector))
    return subprocess.run(
        arguments,
        cwd=cwd,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=120,
    )


def _run_self_check(python: str, log_dir: Path) -> None:
    with TemporaryDirectory(prefix="verlustmappe-parser-self-check-") as temporary:
        root = Path(temporary)
        passing_file = root / "test_parser_passing.py"
        passing_file.write_text("def test_parser_passes():\n    assert True\n", encoding="utf-8")
        passing = _run_pytest(python, root, passing_file.name)
        passing_output = passing.stdout or ""
        (log_dir / "self-check-passing.log").write_text(
            passing_output, encoding="utf-8",
        )
        passing_summary = _parse_summary(passing_output)
        _validate_baseline(passing.returncode, passing_summary, 1)

        failing_file = root / "test_parser_failing.py"
        failing_file.write_text(
            "def test_parser_fails():\n    assert False\n", encoding="utf-8",
        )
        failing = _run_pytest(python, root, failing_file.name)
        failing_output = failing.stdout or ""
        (log_dir / "self-check-failing.log").write_text(
            failing_output, encoding="utf-8",
        )
        failing_summary = _parse_summary(failing_output)
        _validate_mutant(failing.returncode, failing_summary, 1)
        warning_appended_summary = _parse_summary(
            failing_output + "\nwarning: emitted in /tmp/pytest-warning.txt\n",
        )
        if warning_appended_summary != failing_summary:
            raise EvidenceError(
                "self_check_failed",
                "a trailing warning changed the recognized pytest summary",
            )
        for invalid_output, expected_reason, description in (
            ("traceback in /tmp/collection.py", "summary_missing", "missing summary"),
            (passing_output + failing_output, "summary_ambiguous", "multiple summaries"),
            ("1 failed, 1 failed in 0.01s", "summary_invalid", "duplicate category"),
        ):
            _expect_evidence_error(
                expected_reason,
                lambda output=invalid_output: _parse_summary(output),
                description,
            )

        invalid_mutants = (
            (
                0,
                TestSummary({"passed": 2}, "2 passed in 0.01s"),
                "mutant_invalid",
                "non-failing mutant",
            ),
            (
                1,
                TestSummary({"failed": 1, "error": 1}, "1 failed, 1 error in 0.01s"),
                "mutant_invalid",
                "mutant with an error",
            ),
            (
                1,
                TestSummary({"failed": 3}, "3 failed in 0.01s"),
                "mutant_invalid",
                "mutant with too many failures",
            ),
            (
                1,
                TestSummary({"failed": 1}, "1 failed in 0.01s"),
                "mutant_invalid",
                "mutant with too few failures",
            ),
            (
                5,
                TestSummary({}, "80 deselected in 0.01s"),
                "no_selected_tests",
                "mutant with no selected tests",
            ),
        )
        for returncode, summary, expected_reason, description in invalid_mutants:
            _expect_evidence_error(
                expected_reason,
                lambda returncode=returncode, summary=summary: _validate_mutant(
                    returncode, summary, 2,
                ),
                description,
            )

        no_selection = _run_pytest(python, root, passing_file.name, "no_test_matches")
        no_selection_output = no_selection.stdout or ""
        (log_dir / "self-check-no-selection.log").write_text(
            no_selection_output, encoding="utf-8",
        )
        no_selection_summary = _parse_summary(no_selection_output)
        try:
            _validate_baseline(no_selection.returncode, no_selection_summary, 1)
        except EvidenceError as error:
            if error.reason != "no_selected_tests":
                raise EvidenceError(
                    "self_check_failed",
                    f"no-selection run was rejected for {error.reason}, not "
                    "'no_selected_tests'",
                ) from error
        else:
            raise EvidenceError(
                "self_check_failed",
                "no-selection run was accepted as a valid baseline",
            )

        empty_file = root / "test_empty.py"
        empty_file.write_text("", encoding="utf-8")
        empty_run = _run_pytest(python, root, empty_file.name)
        empty_output = empty_run.stdout or ""
        (log_dir / "self-check-empty-suite.log").write_text(
            empty_output, encoding="utf-8",
        )
        empty_summary = _parse_summary(empty_output)
        if empty_run.returncode != 5 or not empty_summary.no_tests_ran:
            raise EvidenceError(
                "self_check_failed",
                "empty-suite output was not recognized as pytest's 'no tests ran' case",
            )
        try:
            _validate_baseline(empty_run.returncode, empty_summary, 1)
        except EvidenceError as error:
            if error.reason != "no_selected_tests":
                raise EvidenceError(
                    "self_check_failed",
                    f"empty-suite output was rejected for {error.reason}, not "
                    "'no_selected_tests'",
                ) from error
        else:
            raise EvidenceError(
                "self_check_failed",
                "empty-suite output was accepted as a valid baseline",
            )


def _run_pytest_mutation(
    python: str, cwd: Path, selector: str,
) -> subprocess.CompletedProcess[str]:
    return _run_pytest(python, cwd, TEST_FILE, selector)


def _copy_test_environment(destination: Path) -> None:
    shutil.copytree(
        REPO_ROOT / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    tests = destination / "tests"
    tests.mkdir()
    shutil.copy2(REPO_ROOT / TEST_FILE, tests / "test_40_static_ledger.py")
    shutil.copy2(REPO_ROOT / "pyproject.toml", destination / "pyproject.toml")


def _apply_mutation(root: Path, mutation: Mutation) -> int:
    path = root / mutation.source
    source = path.read_text(encoding="utf-8")
    occurrences = source.count(mutation.old)
    if occurrences != 1:
        raise EvidenceError(
            "mutation_anchor_invalid",
            f"{mutation.name}: expected one mutation anchor in {mutation.source}, "
            f"found {occurrences}",
        )
    path.write_text(source.replace(mutation.old, mutation.new, 1), encoding="utf-8")
    return occurrences


def _run_one(
    python: str,
    log_dir: Path,
    mutation: Mutation,
    record: dict[str, object],
    persist_manifest,
) -> None:
    with TemporaryDirectory(prefix=f"verlustmappe-{mutation.name}-") as temporary:
        root = Path(temporary)
        _copy_test_environment(root)
        source_text = (root / mutation.source).read_text(encoding="utf-8")
        record["anchor_occurrences"] = source_text.count(mutation.old)
        persist_manifest()

        baseline = _run_pytest_mutation(python, root, mutation.selector)
        baseline_log = baseline.stdout or ""
        (log_dir / f"{mutation.name}.baseline.log").write_text(
            baseline_log, encoding="utf-8",
        )
        baseline_summary = _parse_summary(baseline_log)
        record["baseline"] = {
            "exit_code": baseline.returncode,
            "summary": baseline_summary.line,
            "outcomes": baseline_summary.outcomes,
            "selected_cases": baseline_summary.selected_cases,
        }
        persist_manifest()
        _validate_baseline(baseline.returncode, baseline_summary, mutation.selected_cases)

        record["anchor_occurrences"] = _apply_mutation(root, mutation)
        mutated = _run_pytest_mutation(python, root, mutation.selector)
        mutant_log = mutated.stdout or ""
        (log_dir / f"{mutation.name}.mutant.log").write_text(
            mutant_log, encoding="utf-8",
        )
        mutant_summary = _parse_summary(mutant_log)
        record["mutant"] = {
            "exit_code": mutated.returncode,
            "summary": mutant_summary.line,
            "outcomes": mutant_summary.outcomes,
            "selected_cases": mutant_summary.selected_cases,
        }
        persist_manifest()
        _validate_mutant(mutated.returncode, mutant_summary, mutation.selected_cases)

        record["status"] = "passed"
        persist_manifest()
        print(
            f"{mutation.name}: baseline {mutation.selected_cases} passed "
            f"(exit=0); mutant {mutation.selected_cases} failed "
            f"(exit=1); selector={mutation.selector}"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise EvidenceError("manifest_git_failed", "could not resolve repository HEAD")
    return result.stdout.strip()


def _python_info(python: str) -> dict[str, str]:
    result = subprocess.run(
        (
            python, "-c",
            "import json, sys; print(json.dumps({"
            "'executable': sys.executable, 'prefix': sys.prefix, 'version': sys.version"
            "}))",
        ),
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise EvidenceError("manifest_python_failed", "could not inspect selected Python")
    return json.loads(result.stdout)


def _write_manifest(path: Path, manifest: dict[str, object]) -> None:
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _source_hashes(mutations: tuple[Mutation, ...]) -> dict[str, str]:
    paths = {REPO_ROOT / TEST_FILE, Path(__file__).resolve()}
    paths.update(REPO_ROOT / mutation.source for mutation in mutations)
    return {
        str(path.relative_to(REPO_ROOT)): _sha256(path)
        for path in sorted(paths)
    }


def _pytest_version(python: str) -> str:
    version = subprocess.run(
        (python, "-m", "pytest", "--version"),
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
    )
    if version.returncode != 0:
        raise EvidenceError(
            "pytest_preflight_failed",
            f"pytest preflight failed for {python!r}: {version.stdout.strip()}",
        )
    return version.stdout.strip()


def main() -> int:
    project_python = REPO_ROOT / ".venv" / "bin" / "python"
    parser = argparse.ArgumentParser(
        description=(
            "Run the bounded Package A mutations in temporary copies; this is "
            "development evidence, not a full-suite mutation score."
        )
    )
    parser.add_argument(
        "--log-dir",
        required=True,
        type=Path,
        help="external directory for per-mutant baseline and mutant logs",
    )
    parser.add_argument(
        "--python",
        default=str(project_python if project_python.exists() else sys.executable),
        help="Python executable with pytest installed (default: project .venv if present)",
    )
    parser.add_argument(
        "--include-inventory-uniqueness",
        action="store_true",
        help=(
            "also run the separately scoped ITEMS key-uniqueness mutation; "
            "excluded from the default Package A run"
        ),
    )
    args = parser.parse_args()
    python = Path(args.python).expanduser()
    if not python.is_absolute():
        python = REPO_ROOT / python
    python_command = os.path.abspath(python)
    log_root = args.log_dir.expanduser().resolve()
    if log_root == REPO_ROOT or REPO_ROOT in log_root.parents:
        parser.error("--log-dir must be outside the repository")

    try:
        pytest_version = _pytest_version(python_command)
    except (EvidenceError, OSError, subprocess.SubprocessError) as error:
        print(f"Cannot use pytest with {python_command!r}: {error}", file=sys.stderr)
        return 2

    run_dir = log_root / datetime.now().strftime("%Y%m%dT%H%M%S%f")
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
        manifest_path = run_dir / "run-manifest.json"
        mutations = tuple(
            mutation for mutation in MUTATIONS
            if mutation.option is None
            or (
                mutation.option == "include_inventory_uniqueness"
                and args.include_inventory_uniqueness
            )
        )
        records: list[dict[str, object]] = [
            {
                "name": mutation.name,
                "approval_reference": mutation.approval_reference,
                "source": mutation.source,
                "selector": mutation.selector,
                "expected_selected_cases": mutation.selected_cases,
                "anchor_occurrences": None,
                "status": "pending",
            }
            for mutation in mutations
        ]
        manifest: dict[str, object] = {
            "status": "running",
            "self_check": "running",
            "started_at": datetime.now().astimezone().isoformat(),
            "repo_head": _git_head(),
            "python": _python_info(python_command),
            "pytest_version": pytest_version,
            "source_sha256": _source_hashes(mutations),
            "mutations": records,
        }

        def persist_manifest() -> None:
            _write_manifest(manifest_path, manifest)

        persist_manifest()
        _run_self_check(python_command, run_dir)
        manifest["self_check"] = "passed"
        persist_manifest()
        for mutation, record in zip(mutations, records):
            record["status"] = "running"
            persist_manifest()
            try:
                _run_one(python_command, run_dir, mutation, record, persist_manifest)
            except (EvidenceError, OSError, subprocess.SubprocessError) as error:
                record["status"] = "failed"
                record["error"] = {
                    "reason": error.reason if isinstance(error, EvidenceError) else type(error).__name__,
                    "message": str(error),
                }
                manifest["status"] = "failed"
                manifest["finished_at"] = datetime.now().astimezone().isoformat()
                persist_manifest()
                raise
        manifest["status"] = "passed"
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        persist_manifest()
    except (EvidenceError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"MUTATION EVIDENCE FAILED: {error}", file=sys.stderr)
        if "manifest" in locals():
            manifest["status"] = "failed"
            if manifest.get("self_check") == "running":
                manifest["self_check"] = "failed"
            manifest["finished_at"] = datetime.now().astimezone().isoformat()
            persist_manifest()
        print(f"Logs and manifest (if produced): {run_dir}", file=sys.stderr)
        return 1

    print(f"PACKAGE A MUTANTS OK; logs and manifest: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
