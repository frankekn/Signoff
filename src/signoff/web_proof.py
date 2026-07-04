from __future__ import annotations

import os
from pathlib import Path
from typing import TypeAlias, TypedDict

from .state import run_dir, read_run_state
from .util import read_json, sha256_file

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class ProofStatusRequired(TypedDict):
    status: str


class ProofStatus(ProofStatusRequired, total=False):
    detail: str
    hash: str
    path: str
    patchHash: str


class ScopeBudgets(TypedDict):
    production_files: int
    changed_lines: int


class ScopeSummary(TypedDict):
    status: str
    changed_files: list[str]
    unmapped_files: list[str]
    forbidden_files: list[str]
    production_files: list[str]
    production_file_count: int
    changed_lines: int
    budgets: ScopeBudgets
    file_budget_overflow: bool
    line_budget_overflow: bool


class CommandSummary(TypedDict):
    id: str
    command: list[str]
    status: str
    exitCode: int | None
    acceptanceIds: list[str]


class ReviewGateSummary(ProofStatus, total=False):
    decision: str
    proofLevel: str


class AcceptedCriteriaSummary(TypedDict):
    count: int
    items: list[str]


class ContractSummary(TypedDict):
    final: bool | None


class ProofSummary(TypedDict):
    runId: str
    phase: str
    iteration: int | None
    commands: list[CommandSummary]
    scope: ScopeSummary | ProofStatus
    evidence: ProofStatus
    patch: ProofStatus
    reviewGate: ReviewGateSummary
    acceptedCriteria: AcceptedCriteriaSummary
    contract: ContractSummary
    finalReceipt: ProofStatus


def json_object(value: JsonValue | None) -> JsonObject | None:
    return value if isinstance(value, dict) else None


def text(value: JsonValue | None, fallback: str) -> str:
    return value if isinstance(value, str) else fallback


def integer(value: JsonValue | None) -> int | None:
    return value if type(value) is int else None


def proof_summary_for(project: Path, run_id: str) -> ProofSummary:
    state = read_run_state(project, run_id)
    iteration = _current_iteration(state)
    iteration_dir = _iteration_dir(project, run_id, iteration)
    record = _latest_record(state)
    current_record = json_object(state.get("current")) or {}
    evidence_path = iteration_dir / "EVIDENCE.json" if iteration_dir else None
    evidence = read_json(evidence_path) if evidence_path and evidence_path.is_file() else None
    evidence_hash = text(current_record.get("evidence_sha256"), text(record.get("evidence_sha256"), "") if record else "")
    patch_hash = text(current_record.get("patch_sha256"), text(record.get("patch_sha256"), "") if record else "")
    patch_path = iteration_dir / "PATCH.diff" if iteration_dir else None
    accepted_items = _string_list(state.get("accepted_criteria"))
    final_receipt_path = run_dir(project, run_id) / "FINAL_RECEIPT.json"
    final_receipt_hash = text(state.get("final_receipt_sha256"), "")
    return {
        "runId": run_id,
        "phase": text(state.get("phase"), "UNKNOWN"),
        "iteration": iteration,
        "commands": _command_summaries(evidence),
        "scope": _scope_summary(evidence.get("scope_after") if evidence else None),
        "evidence": _evidence_summary(project, evidence_path, evidence, evidence_hash, patch_hash),
        "patch": _unknown() if not patch_path else _hash_path(project, patch_path, patch_hash or None),
        "reviewGate": _review_gate_summary(project, iteration_dir, state, record),
        "acceptedCriteria": {"count": len(accepted_items), "items": accepted_items},
        "contract": _contract_summary(iteration_dir),
        "finalReceipt": _hash_path(project, final_receipt_path, final_receipt_hash if isinstance(final_receipt_hash, str) else None),
    }


def _relative(project: Path, path: Path) -> str:
    return str(path.relative_to(project)).replace(os.sep, "/")


def _unknown(detail: str = "not yet produced") -> ProofStatus:
    return {"status": "UNKNOWN", "detail": detail}


def _iteration_dir(project: Path, run_id: str, iteration: int | None) -> Path | None:
    if not iteration:
        return None
    return run_dir(project, run_id) / "iterations" / f"{iteration:04d}"


def _string_list(value: JsonValue | None) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _latest_record(state: JsonObject) -> JsonObject | None:
    history = state.get("history")
    if not isinstance(history, list) or not history:
        return None
    return json_object(history[-1])


def _current_iteration(state: JsonObject) -> int | None:
    current = json_object(state.get("current"))
    if current:
        iteration = integer(current.get("iteration"))
        if iteration is not None:
            return iteration
    latest = _latest_record(state)
    if latest:
        iteration = integer(latest.get("iteration"))
        if iteration is not None:
            return iteration
    iteration = integer(state.get("iteration"))
    return iteration if iteration and iteration > 0 else None


def _hash_path(project: Path, path: Path, expected_hash: str | None = None) -> ProofStatus:
    if not path.is_file():
        return _unknown()
    return {"status": "present", "hash": expected_hash or sha256_file(path), "path": _relative(project, path)}


def _contract_summary(iteration_dir: Path | None) -> ContractSummary:
    if not iteration_dir:
        return {"final": None}
    path = iteration_dir / "CONTRACT.json"
    if not path.is_file():
        return {"final": None}
    contract = read_json(path)
    return {"final": contract.get("final") if isinstance(contract.get("final"), bool) else None}


def _command_summaries(evidence: JsonObject | None) -> list[CommandSummary]:
    if not evidence:
        return []
    checks = evidence.get("checks")
    if not isinstance(checks, list):
        return []
    commands: list[CommandSummary] = []
    for check in checks:
        check_object = json_object(check)
        if not check_object:
            continue
        commands.append(
            {
                "id": text(check_object.get("id"), "UNKNOWN"),
                "command": _string_list(check_object.get("command")),
                "status": text(check_object.get("status"), "UNKNOWN"),
                "exitCode": integer(check_object.get("exit_code")),
                "acceptanceIds": _string_list(check_object.get("acceptance_ids")),
            }
        )
    return commands


def _review_gate_summary(project: Path, iteration_dir: Path | None, state: JsonObject, record: JsonObject | None) -> ReviewGateSummary:
    if not iteration_dir:
        return {"decision": "UNKNOWN", "status": "UNKNOWN", "detail": "not yet produced"}
    path = iteration_dir / "REVIEW_GATE.json"
    expected_hash = None
    current = json_object(state.get("current"))
    if current:
        expected_hash = text(current.get("review_gate_sha256"), "")
    if record:
        expected_hash = text(record.get("review_gate_sha256"), expected_hash or "")
    if not path.is_file():
        return {"decision": "UNKNOWN", "status": "UNKNOWN", "detail": "not yet produced"}
    gate = read_json(path)
    return {
        "decision": gate.get("decision", "UNKNOWN") if isinstance(gate.get("decision"), str) else "UNKNOWN",
        "status": "present",
        "proofLevel": gate.get("proof_level", "UNKNOWN") if isinstance(gate.get("proof_level"), str) else "UNKNOWN",
        "hash": expected_hash or sha256_file(path),
        "path": _relative(project, path),
    }


def _scope_summary(value: JsonValue | None) -> ScopeSummary | ProofStatus:
    scope = json_object(value)
    if not scope:
        return _unknown()
    budgets = json_object(scope.get("budgets")) or {}
    return {
        "status": text(scope.get("status"), "UNKNOWN"),
        "changed_files": _string_list(scope.get("changed_files")),
        "unmapped_files": _string_list(scope.get("unmapped_files")),
        "forbidden_files": _string_list(scope.get("forbidden_files")),
        "production_files": _string_list(scope.get("production_files")),
        "production_file_count": integer(scope.get("production_file_count")) or 0,
        "changed_lines": integer(scope.get("changed_lines")) or 0,
        "budgets": {
            "production_files": integer(budgets.get("production_files")) or 0,
            "changed_lines": integer(budgets.get("changed_lines")) or 0,
        },
        "file_budget_overflow": scope.get("file_budget_overflow") is True,
        "line_budget_overflow": scope.get("line_budget_overflow") is True,
    }


def _evidence_summary(project: Path, evidence_path: Path | None, evidence: JsonObject | None, evidence_hash: str, patch_hash: str) -> ProofStatus:
    if not evidence or not evidence_path:
        return _unknown()
    return {
        "status": text(evidence.get("status"), "UNKNOWN"),
        "hash": evidence_hash or sha256_file(evidence_path),
        "path": _relative(project, evidence_path),
        "patchHash": text(evidence.get("patch_sha256"), patch_hash),
    }
