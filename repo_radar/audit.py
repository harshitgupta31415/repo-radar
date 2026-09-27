from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "dist",
    "build",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class CheckResult:
    key: str
    title: str
    passed: bool
    points: int
    detail: str
    suggestion: str | None = None


@dataclass(frozen=True)
class AuditResult:
    path: str
    score: int
    maximum_score: int
    checks: tuple[CheckResult, ...]

    @property
    def percentage(self) -> int:
        return round((self.score / self.maximum_score) * 100) if self.maximum_score else 0

    @property
    def passed(self) -> int:
        return sum(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "score": self.score,
            "maximum_score": self.maximum_score,
            "percentage": self.percentage,
            "passed_checks": self.passed,
            "total_checks": len(self.checks),
            "checks": [asdict(check) for check in self.checks],
        }


def _exists_any(root: Path, names: Iterable[str]) -> Path | None:
    lowered = {entry.name.lower(): entry for entry in root.iterdir()} if root.is_dir() else {}
    for name in names:
        if match := lowered.get(name.lower()):
            return match
    return None


def _visible_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRECTORIES for part in relative_parts):
            continue
        yield path


def _check(
    key: str,
    title: str,
    points: int,
    evidence: Path | None,
    success_detail: str,
    failure_detail: str,
    suggestion: str,
) -> CheckResult:
    return CheckResult(
        key=key,
        title=title,
        passed=evidence is not None,
        points=points,
        detail=success_detail.format(path=evidence.name) if evidence else failure_detail,
        suggestion=None if evidence else suggestion,
    )


def audit_repository(path: str | Path, max_file_kb: int = 1024) -> AuditResult:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository path does not exist or is not a directory: {root}")
    if max_file_kb < 1:
        raise ValueError("max_file_kb must be at least 1")

    checks: list[CheckResult] = [
        _check(
            "readme",
            "Project documentation",
            20,
            _exists_any(root, ("README.md", "README.rst", "README.txt")),
            "Found {path}",
            "No README found",
            "Add a README with purpose, setup, usage, and verification steps.",
        ),
        _check(
            "license",
            "Open-source licence",
            10,
            _exists_any(root, ("LICENSE", "LICENSE.md", "COPYING")),
            "Found {path}",
            "No licence found",
            "Add a licence so others know how the project may be used.",
        ),
        _check(
            "gitignore",
            "Ignored generated files",
            10,
            _exists_any(root, (".gitignore",)),
            "Found {path}",
            "No .gitignore found",
            "Add a .gitignore suited to the language and tooling.",
        ),
        _check(
            "ci",
            "Continuous integration",
            20,
            _exists_any(root / ".github" / "workflows", tuple(p.name for p in (root / ".github" / "workflows").glob("*.y*ml")))
            if (root / ".github" / "workflows").is_dir()
            else None,
            "Found workflow {path}",
            "No GitHub Actions workflow found",
            "Run tests or validation automatically for pushes and pull requests.",
        ),
    ]

    test_evidence = next(
        (
            candidate
            for candidate in (root / "tests", root / "test", root / "__tests__", root / "spec")
            if candidate.is_dir() and any(candidate.iterdir())
        ),
        None,
    )
    checks.append(
        _check(
            "tests",
            "Automated tests",
            20,
            test_evidence,
            "Found {path}/",
            "No test directory found",
            "Add focused tests for important behaviour and failure cases.",
        )
    )

    dependency_evidence = _exists_any(
        root,
        (
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "uv.lock",
            "poetry.lock",
            "Pipfile.lock",
            "go.sum",
            "Cargo.lock",
            "requirements.txt",
            "pyproject.toml",
        ),
    )
    checks.append(
        _check(
            "dependencies",
            "Reproducible dependencies",
            10,
            dependency_evidence,
            "Found {path}",
            "No dependency manifest or lockfile found",
            "Document or lock project dependencies for reproducible setup.",
        )
    )

    threshold = max_file_kb * 1024
    oversized = sorted(
        ((file.stat().st_size, file.relative_to(root)) for file in _visible_files(root) if file.stat().st_size > threshold),
        reverse=True,
    )
    checks.append(
        CheckResult(
            key="large_files",
            title="Repository file size",
            passed=not oversized,
            points=10,
            detail=(
                f"No files exceed {max_file_kb} KB"
                if not oversized
                else f"{len(oversized)} file(s) exceed {max_file_kb} KB; largest is {oversized[0][1]}"
            ),
            suggestion=None if not oversized else "Move generated or binary assets to release storage and ignore build output.",
        )
    )

    maximum = sum(check.points for check in checks)
    earned = sum(check.points for check in checks if check.passed)
    return AuditResult(str(root), earned, maximum, tuple(checks))
