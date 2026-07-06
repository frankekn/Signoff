from __future__ import annotations

from pathlib import Path
from typing import Final, TypedDict

from .errors import StateError, ValidationError
from .state import run_dir, read_run_state, read_root_state
from .util import ensure_within
from .web_overview import editable_paths

TEXT_ARTIFACT_SUFFIXES: Final = {".json", ".jsonl", ".md", ".txt", ".diff", ".log"}


class ArtifactSummary(TypedDict):
    path: str
    name: str
    size: int
    editable: bool
    kind: str


def list_artifacts(project: Path, run_id: str) -> list[ArtifactSummary]:
    base = run_dir(project, run_id)
    if not base.is_dir():
        raise ValidationError(f"unknown run: {run_id}")
    state = read_run_state(project, run_id)
    root = read_root_state(project)
    editable = editable_paths(project, state) if run_id == root.get("active_run_id") else set()
    artifacts: list[ArtifactSummary] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
            continue
        relative = path.relative_to(project).as_posix()
        artifacts.append(
            {
                "path": relative,
                "name": path.name,
                "size": path.stat().st_size,
                "editable": relative in editable,
                "kind": path.suffix.lower().lstrip("."),
            }
        )
    return artifacts


def safe_artifact_path(project: Path, relative: str) -> Path:
    normalized = relative.strip().replace("\\", "/")
    if not normalized.startswith(".traction/runs/"):
        raise ValidationError("artifact path must stay inside .traction/runs")
    candidate = ensure_within(project, project / normalized)
    runs_root = ensure_within(project, project / ".traction" / "runs")
    try:
        candidate.relative_to(runs_root)
    except ValueError as exc:
        raise ValidationError("artifact path escapes the run directory") from exc
    if candidate.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
        raise ValidationError("unsupported artifact type")
    return candidate


def assert_editable_artifact(project: Path, relative: str) -> None:
    root = read_root_state(project)
    run_id = root.get("active_run_id")
    if not run_id:
        raise StateError("there is no active run")
    state = read_run_state(project, run_id)
    if relative not in editable_paths(project, state):
        raise StateError("this artifact is locked or generated in the current phase")
