from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from . import __version__
from .errors import SignoffError, ValidationError
from .runtime import RESTARTABLE_PHASES, Runtime
from .state import mission_dir, read_mission_state, read_root_state
from .web_proof import JsonObject, JsonValue, ProofSummary, integer, json_object, proof_summary_for, text


class CourtAction(TypedDict, total=False):
    id: str
    label: str
    tone: str
    requiresNote: bool


class MissionSummaryRequired(TypedDict):
    missionId: str
    goal: str
    phase: str
    active: bool


class MissionSummary(MissionSummaryRequired, total=False):
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
    canStartMission: bool
    blockedByIntegrity: bool
    integrityStatus: str
    integrityMessage: str
    actions: list[CourtAction]
    editablePaths: list[str]
    missions: list[MissionSummary]
    proofSummary: ProofSummary | None
    inspectedMission: MissionSummary | None


def allowed_actions(phase: str) -> list[CourtAction]:
    actions: dict[str, list[CourtAction]] = {
        "IDLE": [],
        "DRAFT": [
            {"id": "prepare_push", "label": "Send to Push", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "PUSH": [
            {"id": "lock", "label": "Lock decision", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "LOCKED": [
            {"id": "prepare_slice", "label": "Create next slice", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
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
        "VERIFIED": [{"id": "prepare_roast", "label": "Prepare independent review", "tone": "primary"}],
        "REVIEWING": [{"id": "roast", "label": "Seal review", "tone": "primary"}],
        "REVIEWED": [
            {"id": "finish_done", "label": "Sign off", "tone": "primary"},
            {"id": "finish_accepted", "label": "Accept slice", "tone": "neutral"},
            {"id": "finish_rework", "label": "Rework", "tone": "danger", "requiresNote": True},
        ],
        "PUSH_REVIEW": [
            {"id": "pivot", "label": "Authorize pivot", "tone": "primary", "requiresNote": True},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "DONE": [],
        "STOPPED": [],
        "PIVOT": [],
        "BLOCKED": [],
    }
    return actions.get(phase, [])


def editable_paths(project: Path, state: JsonObject) -> set[str]:
    mission_id = str(state["mission_id"])
    base = mission_dir(project, mission_id)
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


def mission_summaries(project: Path) -> list[MissionSummary]:
    root = read_root_state(project)
    summaries: list[MissionSummary] = []
    for mission_id in reversed(root.get("missions", [])):
        try:
            state = read_mission_state(project, mission_id)
            goal_path = mission_dir(project, mission_id) / "GOAL.txt"
            goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.is_file() else ""
            summary: MissionSummary = {
                "missionId": mission_id,
                "goal": goal,
                "phase": text(state.get("phase"), "UNKNOWN"),
                "active": mission_id == root.get("active_mission_id"),
            }
            _add_int(summary, "revision", state.get("revision"))
            _add_int(summary, "iteration", state.get("iteration"))
            updated_at = state.get("updated_at")
            if isinstance(updated_at, str):
                summary["updatedAt"] = updated_at
            summaries.append(summary)
        except SignoffError as exc:
            summaries.append(
                {
                    "missionId": mission_id,
                    "goal": "",
                    "phase": "INVALID",
                    "error": str(exc),
                    "active": mission_id == root.get("active_mission_id"),
                }
            )
    return summaries


def build_overview(project: Path, runtime: Runtime, inspect_mission_id: str | None = None) -> OverviewPayload:
    status = runtime.status()
    phase = text(status.get("phase"), "IDLE")
    mission_id = status.get("mission_id")
    proof_mission_id = require_known_mission(project, inspect_mission_id) if inspect_mission_id else mission_id
    integrity = json_object(status.get("integrity"))
    blocked_by_integrity = integrity is not None and integrity.get("status") == "fail"
    goal = ""
    editable: set[str] = set()
    if isinstance(mission_id, str) and mission_id:
        state = read_mission_state(project, mission_id)
        goal_path = mission_dir(project, mission_id) / "GOAL.txt"
        goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.is_file() else ""
        editable = editable_paths(project, state)
    actions = _legal_actions(phase, status, blocked_by_integrity)
    next_instruction = _next_instruction(status, blocked_by_integrity)
    missions = mission_summaries(project)
    return {
        "product": "Signoff",
        "version": __version__,
        "project": str(project),
        "goal": goal,
        "status": status,
        "next": next_instruction,
        "canStartMission": phase in RESTARTABLE_PHASES and not blocked_by_integrity,
        "blockedByIntegrity": blocked_by_integrity,
        "integrityStatus": _integrity_status(integrity, blocked_by_integrity),
        "integrityMessage": _integrity_message(integrity, blocked_by_integrity),
        "actions": actions,
        "editablePaths": sorted(editable),
        "missions": missions,
        "proofSummary": proof_summary_for(project, str(proof_mission_id)) if proof_mission_id else None,
        "inspectedMission": next((mission for mission in missions if mission["missionId"] == proof_mission_id), None) if proof_mission_id else None,
    }


def require_known_mission(project: Path, mission_id: str) -> str:
    root = read_root_state(project)
    if mission_id not in root.get("missions", []):
        raise ValidationError(f"unknown mission: {mission_id}")
    return mission_id


def _add_int(summary: MissionSummary, key: Literal["revision", "iteration"], value: JsonValue | None) -> None:
    int_value = integer(value)
    if int_value is not None:
        summary[key] = int_value


def _legal_actions(phase: str, status: JsonObject, blocked_by_integrity: bool) -> list[CourtAction]:
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
        return "No active mission."
    message = str(integrity.get("error", "Integrity checks passed."))
    return "Inspect and repair integrity: " + message if blocked_by_integrity else message
