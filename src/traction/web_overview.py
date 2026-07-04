from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from . import __version__
from .errors import TractionError, ValidationError
from .runtime import RESTARTABLE_PHASES, Runtime
from .state import run_dir, read_run_state, read_root_state
from .web_proof import JsonObject, JsonValue, ProofSummary, integer, json_object, proof_summary_for, text


class GripAction(TypedDict, total=False):
    id: str
    label: str
    tone: str
    requiresNote: bool


class RunSummaryRequired(TypedDict):
    runId: str
    goal: str
    phase: str
    active: bool


class RunSummary(RunSummaryRequired, total=False):
    revision: int
    iteration: int
    updatedAt: str
    error: str


class OverviewPayload(TypedDict):
    product: str
    version: str
    project: str
    goal: str
    status: JsonObject
    next: str
    canStartRun: bool
    blockedByIntegrity: bool
    integrityStatus: str
    integrityMessage: str
    actions: list[GripAction]
    editablePaths: list[str]
    runs: list[RunSummary]
    proofSummary: ProofSummary | None
    inspectedRun: RunSummary | None


def allowed_actions(phase: str) -> list[GripAction]:
    actions: dict[str, list[GripAction]] = {
        "IDLE": [],
        "DRAFT": [
            {"id": "prepare_push", "label": "Send to Push", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop run", "tone": "danger", "requiresNote": True},
        ],
        "PUSH": [
            {"id": "lock", "label": "Lock decision", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop run", "tone": "danger", "requiresNote": True},
        ],
        "LOCKED": [
            {"id": "prepare_slice", "label": "Create next slice", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop run", "tone": "danger", "requiresNote": True},
        ],
        "SLICE_DRAFT": [{"id": "activate_slice", "label": "Activate slice", "tone": "primary"}],
        "IMPLEMENTING": [
            {"id": "check_scope", "label": "Check scope", "tone": "neutral"},
            {"id": "verify", "label": "Run verification", "tone": "primary"},
        ],
        "VERIFY_FAILED": [
            {"id": "check_scope", "label": "Check scope", "tone": "neutral"},
            {"id": "verify", "label": "Verify again", "tone": "primary"},
        ],
        "VERIFIED": [{"id": "prepare_pull", "label": "Prepare independent review", "tone": "primary"}],
        "REVIEWING": [{"id": "pull", "label": "Seal review", "tone": "primary"}],
        "REVIEWED": [
            {"id": "finish_done", "label": "Sign off", "tone": "primary"},
            {"id": "finish_accepted", "label": "Accept slice", "tone": "neutral"},
            {"id": "finish_rework", "label": "Rework", "tone": "danger", "requiresNote": True},
        ],
        "PUSH_REVIEW": [
            {"id": "pivot", "label": "Authorize pivot", "tone": "primary", "requiresNote": True},
            {"id": "finish_stopped", "label": "Stop run", "tone": "danger", "requiresNote": True},
        ],
        "DONE": [],
        "STOPPED": [],
        "PIVOT": [],
        "BLOCKED": [],
    }
    return actions.get(phase, [])


def editable_paths(project: Path, state: JsonObject) -> set[str]:
    run_id = str(state["run_id"])
    base = run_dir(project, run_id)
    phase = state.get("phase")
    allowed: set[Path] = set()
    if phase == "DRAFT":
        allowed.update({base / "CHARTER.md", base / "SPEC.json"})
    elif phase == "PUSH":
        allowed.add(base / "PUSH.json")
    elif phase in {"SLICE_DRAFT", "REVIEWING"} and state.get("current"):
        current = json_object(state.get("current"))
        iteration = integer(current.get("iteration")) if current else None
        if iteration is not None:
            iteration_dir = base / "iterations" / f"{iteration:04d}"
            allowed.add(iteration_dir / ("CONTRACT.json" if phase == "SLICE_DRAFT" else "JUDGMENT.json"))
            review_dir = iteration_dir / "reviews"
            if phase == "REVIEWING" and review_dir.is_dir():
                allowed.update(path for path in review_dir.glob("review-*.json") if path.is_file())
    return {path.relative_to(project).as_posix() for path in allowed}


def run_summaries(project: Path) -> list[RunSummary]:
    root = read_root_state(project)
    summaries: list[RunSummary] = []
    for run_id in reversed(root.get("runs", [])):
        try:
            state = read_run_state(project, run_id)
            goal_path = run_dir(project, run_id) / "GOAL.txt"
            goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.is_file() else ""
            summary: RunSummary = {
                "runId": run_id,
                "goal": goal,
                "phase": text(state.get("phase"), "UNKNOWN"),
                "active": run_id == root.get("active_run_id"),
            }
            _add_int(summary, "revision", state.get("revision"))
            _add_int(summary, "iteration", state.get("iteration"))
            updated_at = state.get("updated_at")
            if isinstance(updated_at, str):
                summary["updatedAt"] = updated_at
            summaries.append(summary)
        except TractionError as exc:
            summaries.append(
                {
                    "runId": run_id,
                    "goal": "",
                    "phase": "INVALID",
                    "error": str(exc),
                    "active": run_id == root.get("active_run_id"),
                }
            )
    return summaries


def build_overview(project: Path, runtime: Runtime, inspect_run_id: str | None = None) -> OverviewPayload:
    status = runtime.status()
    phase = text(status.get("phase"), "IDLE")
    run_id = status.get("run_id")
    proof_run_id = require_known_run(project, inspect_run_id) if inspect_run_id else run_id
    integrity = json_object(status.get("integrity"))
    blocked_by_integrity = integrity is not None and integrity.get("status") == "fail"
    goal = ""
    editable: set[str] = set()
    if isinstance(run_id, str) and run_id:
        state = read_run_state(project, run_id)
        goal_path = run_dir(project, run_id) / "GOAL.txt"
        goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.is_file() else ""
        editable = editable_paths(project, state)
    actions = _legal_actions(phase, status, blocked_by_integrity)
    next_instruction = _next_instruction(status, blocked_by_integrity)
    runs = run_summaries(project)
    return {
        "product": "Traction",
        "version": __version__,
        "project": str(project),
        "goal": goal,
        "status": status,
        "next": next_instruction,
        "canStartRun": phase in RESTARTABLE_PHASES and not blocked_by_integrity,
        "blockedByIntegrity": blocked_by_integrity,
        "integrityStatus": _integrity_status(integrity, blocked_by_integrity),
        "integrityMessage": _integrity_message(integrity, blocked_by_integrity),
        "actions": actions,
        "editablePaths": sorted(editable),
        "runs": runs,
        "proofSummary": proof_summary_for(project, str(proof_run_id)) if proof_run_id else None,
        "inspectedRun": next((run for run in runs if run["runId"] == proof_run_id), None) if proof_run_id else None,
    }


def require_known_run(project: Path, run_id: str) -> str:
    root = read_root_state(project)
    if run_id not in root.get("runs", []):
        raise ValidationError(f"unknown run: {run_id}")
    return run_id


def _add_int(summary: RunSummary, key: Literal["revision", "iteration"], value: JsonValue | None) -> None:
    int_value = integer(value)
    if int_value is not None:
        summary[key] = int_value


def _legal_actions(phase: str, status: JsonObject, blocked_by_integrity: bool) -> list[GripAction]:
    if blocked_by_integrity:
        return []
    actions = allowed_actions(phase)
    current = json_object(status.get("current"))
    if phase == "REVIEWED" and not bool((current or {}).get("final")):
        return [action for action in actions if action["id"] != "finish_done"]
    return actions


def _next_instruction(status: JsonObject, blocked_by_integrity: bool) -> str:
    if blocked_by_integrity:
        return "Inspect and repair integrity before taking another action."
    return text(status.get("next"), "")


def _integrity_status(integrity: JsonObject | None, blocked_by_integrity: bool) -> str:
    if not integrity:
        return "idle"
    return "fail" if blocked_by_integrity else "pass"


def _integrity_message(integrity: JsonObject | None, blocked_by_integrity: bool) -> str:
    if not integrity:
        return "No active run."
    message = str(integrity.get("error", "Integrity checks passed."))
    return "Inspect and repair integrity: " + message if blocked_by_integrity else message
