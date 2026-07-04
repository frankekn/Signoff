"""The deterministic state machine around agent-authored artifacts."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .errors import IntegrityError, SignoffError, StateError, ValidationError
from .git import changed_files, changed_line_count, ensure_repository, patch, snapshot_commit
from .ledger import append as append_ledger
from .schemas import validate_contract, validate_push, validate_pull, validate_spec
from .state import (
    TERMINAL_PHASES,
    active_run,
    control_root,
    current_iteration_dir,
    ledger_path,
    run_dir,
    read_run_state,
    read_root_state,
    require_phase,
    verify_lock,
    write_run_state,
    write_root_state,
)
from .templates import (
    charter_template,
    contract_template,
    push_template,
    judgment_template,
    review_template,
    spec_template,
)
from .util import (
    atomic_write_json,
    atomic_write_text,
    bounded_text,
    ensure_within,
    matches_any,
    now_utc,
    read_json,
    require_clean_text,
    sha256_file,
    sha256_text,
    short_id,
)


RESTARTABLE_PHASES = {"IDLE", "DONE", "STOPPED"}


def _artifact_hashes(base: Path, names: dict[str, str]) -> dict[str, str]:
    return {name: sha256_file(base / relative) for name, relative in names.items()}


def _spec_info(project: Path, state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    base = run_dir(project, state["run_id"])
    goal = (base / "GOAL.txt").read_text(encoding="utf-8").rstrip("\n")
    spec = read_json(base / "SPEC.json")
    info = validate_spec(spec, run_id=state["run_id"], goal_sha256=sha256_text(goal))
    return spec, info


def _validate_charter(project: Path, state: dict[str, Any]) -> str:
    base = run_dir(project, state["run_id"])
    goal = (base / "GOAL.txt").read_text(encoding="utf-8").rstrip("\n")
    try:
        charter = (base / "CHARTER.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read CHARTER.md: {exc}") from exc
    require_clean_text(charter, "CHARTER.md", minimum=100)
    if goal not in charter:
        raise ValidationError("CHARTER.md must preserve the exact user outcome verbatim")
    return charter


def _contract_and_info(project: Path, state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], Path]:
    verify_lock(project, state)
    iteration_dir = current_iteration_dir(project, state)
    contract_path = iteration_dir / "CONTRACT.json"
    contract = read_json(contract_path)
    spec, spec_info = _spec_info(project, state)
    del spec
    info = validate_contract(
        contract,
        run_id=state["run_id"],
        iteration=state["current"]["iteration"],
        spec_requirement_ids=spec_info["requirement_ids"],
        spec_acceptance_ids=spec_info["acceptance_ids"],
    )
    expected = state["current"].get("contract_sha256")
    actual = sha256_file(contract_path)
    if expected and actual != expected:
        raise IntegrityError("active CONTRACT.json was edited after activation")
    return contract, info, contract_path


def _scope(project: Path, baseline: str, contract_info: dict[str, Any]) -> dict[str, Any]:
    files = changed_files(project, baseline)
    forbidden = [path for path in files if matches_any(path, contract_info["forbidden_paths"])]
    unmapped = [path for path in files if not matches_any(path, contract_info["allowed_paths"])]
    production = [path for path in files if not matches_any(path, contract_info["exempt_paths"])]
    lines = changed_line_count(project, baseline, files)
    budgets = contract_info["budgets"]
    file_overflow = len(production) > budgets["production_files"]
    line_overflow = lines > budgets["changed_lines"]
    passed = not forbidden and not unmapped and not file_overflow and not line_overflow
    return {
        "status": "pass" if passed else "fail",
        "changed_files": files,
        "unmapped_files": unmapped,
        "forbidden_files": forbidden,
        "production_files": production,
        "production_file_count": len(production),
        "changed_lines": lines,
        "budgets": budgets,
        "file_budget_overflow": file_overflow,
        "line_budget_overflow": line_overflow,
    }


def _evidence_hashes(iteration_dir: Path) -> dict[str, str]:
    return {
        "contract": sha256_file(iteration_dir / "CONTRACT.json"),
        "evidence": sha256_file(iteration_dir / "EVIDENCE.json"),
        "patch": sha256_file(iteration_dir / "PATCH.diff"),
    }


def _passed_check_ids(evidence: dict[str, Any]) -> set[str]:
    return {
        check["id"]
        for check in evidence.get("checks", [])
        if check.get("status") == "pass" and check.get("exit_code") == 0
    }


class Runtime:
    def __init__(self, project: Path):
        self.project = project.expanduser().resolve()

    def doctor(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        checks.append(
            {
                "name": "python",
                "status": "pass" if sys.version_info >= (3, 10) else "fail",
                "detail": sys.version.split()[0],
            }
        )
        try:
            ensure_repository(self.project)
            checks.append({"name": "git-repository", "status": "pass", "detail": str(self.project)})
        except SignoffError as exc:
            checks.append({"name": "git-repository", "status": "fail", "detail": str(exc)})
        control = control_root(self.project)
        try:
            control.mkdir(parents=True, exist_ok=True)
            probe = control / ".doctor-write"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            checks.append({"name": "repository-write", "status": "pass", "detail": str(control)})
        except OSError as exc:
            checks.append({"name": "repository-write", "status": "fail", "detail": str(exc)})
        root = read_root_state(self.project)
        active_id = root.get("active_run_id")
        if active_id:
            try:
                state = read_run_state(self.project, active_id)
                if state.get("lock"):
                    verify_lock(self.project, state)
                checks.append({"name": "run-integrity", "status": "pass", "detail": f"{active_id}: {state['phase']}"})
            except SignoffError as exc:
                checks.append({"name": "run-integrity", "status": "fail", "detail": str(exc)})
        else:
            checks.append({"name": "run-integrity", "status": "pass", "detail": "no active run"})
        return {"status": "pass" if all(item["status"] == "pass" for item in checks) else "fail", "checks": checks}

    def start(self, goal: str) -> dict[str, Any]:
        ensure_repository(self.project)
        goal = goal.strip()
        if not goal:
            raise ValidationError("goal must be the user's exact non-empty outcome")
        root = read_root_state(self.project)
        active_id = root.get("active_run_id")
        if active_id:
            active = read_run_state(self.project, active_id)
            if active.get("phase") not in RESTARTABLE_PHASES:
                raise StateError(f"run {active_id} is still active in phase {active['phase']}")
        run_id = short_id("run", goal)
        base = run_dir(self.project, run_id)
        base.mkdir(parents=True, exist_ok=False)
        goal_sha = sha256_text(goal)
        atomic_write_text(base / "GOAL.txt", goal + "\n")
        atomic_write_text(base / "CHARTER.md", charter_template(run_id, goal))
        atomic_write_json(base / "SPEC.json", spec_template(run_id, goal_sha, goal))
        baseline = snapshot_commit(self.project, f"Signoff run baseline {run_id}")
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "phase": "DRAFT",
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "goal_sha256": goal_sha,
            "run_baseline": baseline,
            "iteration": 0,
            "accepted_criteria": [],
            "history": [],
            "lock": None,
            "lock_file_sha256": None,
            "current": None,
            "revision": 1,
        }
        write_run_state(self.project, state)
        root["active_run_id"] = run_id
        if run_id not in root["runs"]:
            root["runs"].append(run_id)
        root["updated_at"] = now_utc()
        write_root_state(self.project, root)
        append_ledger(
            ledger_path(self.project, run_id),
            "run.started",
            {"run_id": run_id, "goal_sha256": goal_sha, "baseline": baseline},
        )
        return {
            "run_id": run_id,
            "phase": "DRAFT",
            "goal_path": str((base / "GOAL.txt").relative_to(self.project)),
            "charter_path": str((base / "CHARTER.md").relative_to(self.project)),
            "spec_path": str((base / "SPEC.json").relative_to(self.project)),
            "next": self.next_action(),
        }

    def prepare_push(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"DRAFT", "PUSH"})
        _validate_charter(self.project, state)
        _spec, spec_info = _spec_info(self.project, state)
        del spec_info
        base = run_dir(self.project, state["run_id"])
        hashes = _artifact_hashes(base, {"goal": "GOAL.txt", "charter": "CHARTER.md", "spec": "SPEC.json"})
        push_path = base / "PUSH.json"
        if push_path.exists() and state["phase"] == "PUSH":
            existing = read_json(push_path)
            if existing.get("advisors") and not any("REPLACE_ME" in json.dumps(x) for x in existing.get("advisors", [])):
                raise StateError("PUSH.json already contains advisor work; do not overwrite it")
        atomic_write_json(push_path, push_template(state["run_id"], hashes))
        state["phase"] = "PUSH"
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "push.prepared", {"artifact_hashes": hashes})
        return {"phase": "PUSH", "push_path": str(push_path.relative_to(self.project)), "artifact_hashes": hashes, "next": self.next_action()}

    def lock(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"PUSH"})
        _validate_charter(self.project, state)
        spec, spec_info = _spec_info(self.project, state)
        base = run_dir(self.project, state["run_id"])
        hashes = _artifact_hashes(base, {"goal": "GOAL.txt", "charter": "CHARTER.md", "spec": "SPEC.json"})
        push_path = base / "PUSH.json"
        push = read_json(push_path)
        push_result = validate_push(push, run_id=state["run_id"], expected_hashes=hashes)
        push_sha = sha256_file(push_path)
        verdict = push_result["verdict"]
        if verdict != "PROCEED":
            terminal = {"STOP": "STOPPED", "PIVOT": "PIVOT", "INSUFFICIENT_QUORUM": "BLOCKED"}[verdict]
            state["phase"] = terminal
            state["updated_at"] = now_utc()
            state["terminal_reason"] = push["decision"]["rationale"]
            write_run_state(self.project, state)
            append_ledger(ledger_path(self.project, state["run_id"]), "run.concluded", {"phase": terminal, "push_sha256": push_sha})
            return {"phase": terminal, "verdict": verdict, "reason": state["terminal_reason"]}
        lock = {
            "schema_version": 1,
            "run_id": state["run_id"],
            "revision": state["revision"],
            "locked_at": now_utc(),
            "goal_sha256": hashes["goal"],
            "charter_sha256": hashes["charter"],
            "spec_sha256": hashes["spec"],
            "push_sha256": push_sha,
            "push_result": push_result,
            "requirement_ids": sorted(spec_info["requirement_ids"]),
            "acceptance_ids": sorted(spec_info["acceptance_ids"]),
            "max_iterations": spec_info["max_iterations"],
        }
        lock_path = base / "LOCK.json"
        atomic_write_json(lock_path, lock)
        state["lock"] = lock
        state["lock_file_sha256"] = sha256_file(lock_path)
        state["phase"] = "LOCKED"
        state["updated_at"] = now_utc()
        state["max_iterations"] = spec_info["max_iterations"]
        state["push_first_slice"] = push["decision"]["first_slice"]
        write_run_state(self.project, state)
        append_ledger(
            ledger_path(self.project, state["run_id"]),
            "run.locked",
            {"lock_sha256": state["lock_file_sha256"], "push_sha256": push_sha},
        )
        del spec
        return {"phase": "LOCKED", "lock_path": str(lock_path.relative_to(self.project)), "lock_sha256": state["lock_file_sha256"], "next": self.next_action()}

    def prepare_slice(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"LOCKED"})
        verify_lock(self.project, state)
        if state["iteration"] >= state["max_iterations"]:
            state["phase"] = "PUSH_REVIEW"
            state["updated_at"] = now_utc()
            write_run_state(self.project, state)
            raise StateError("iteration budget exhausted; Push must STOP or authorize a pivot")
        spec, _ = _spec_info(self.project, state)
        iteration = state["iteration"] + 1
        iteration_dir = run_dir(self.project, state["run_id"]) / "iterations" / f"{iteration:04d}"
        iteration_dir.mkdir(parents=True, exist_ok=False)
        first_slice = state.get("push_first_slice", "") if iteration == 1 else ""
        atomic_write_json(iteration_dir / "CONTRACT.json", contract_template(state["run_id"], iteration, spec, first_slice))
        state["current"] = {"iteration": iteration, "attempt": 1, "root_causes": []}
        state["phase"] = "SLICE_DRAFT"
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "slice.prepared", {"iteration": iteration})
        return {"phase": "SLICE_DRAFT", "iteration": iteration, "contract_path": str((iteration_dir / "CONTRACT.json").relative_to(self.project)), "next": self.next_action()}

    def activate_slice(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"SLICE_DRAFT"})
        verify_lock(self.project, state)
        contract, info, contract_path = _contract_and_info(self.project, state)
        baseline = snapshot_commit(self.project, f"Signoff slice {state['current']['iteration']} baseline")
        contract_sha = sha256_file(contract_path)
        state["current"].update(
            {
                "contract_sha256": contract_sha,
                "baseline": baseline,
                "builder": info["builder"],
                "requirements": sorted(info["requirements"]),
                "acceptance_criteria": sorted(info["acceptance"]),
                "final": info["final"],
                "activated_at": now_utc(),
            }
        )
        state["phase"] = "IMPLEMENTING"
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        atomic_write_json(current_iteration_dir(self.project, state) / "GUARD.json", state["current"])
        append_ledger(
            ledger_path(self.project, state["run_id"]),
            "slice.activated",
            {"iteration": state["current"]["iteration"], "contract_sha256": contract_sha, "baseline": baseline},
        )
        return {"phase": "IMPLEMENTING", "iteration": state["current"]["iteration"], "contract_sha256": contract_sha, "builder": info["builder"], "next": self.next_action()}

    def check_scope(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"IMPLEMENTING", "VERIFY_FAILED", "VERIFIED", "REVIEWING", "REVIEWED"})
        _contract, info, _path = _contract_and_info(self.project, state)
        return _scope(self.project, state["current"]["baseline"], info)

    def verify(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"IMPLEMENTING", "VERIFY_FAILED"})
        contract, info, contract_path = _contract_and_info(self.project, state)
        iteration_dir = current_iteration_dir(self.project, state)
        pre_scope = _scope(self.project, state["current"]["baseline"], info)
        patch_before = patch(self.project, state["current"]["baseline"])
        patch_before_sha = sha256_text(patch_before)
        check_results: list[dict[str, Any]] = []
        for check in contract["verification"]:
            workdir = ensure_within(self.project, self.project / check["working_directory"])
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    check["command"],
                    cwd=workdir,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=check["timeout_seconds"],
                    check=False,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                stdout, stdout_truncated = bounded_text(proc.stdout)
                stderr, stderr_truncated = bounded_text(proc.stderr)
                result = {
                    "id": check["id"],
                    "command": check["command"],
                    "working_directory": check["working_directory"],
                    "acceptance_ids": check["acceptance_ids"],
                    "status": "pass" if proc.returncode == 0 else "fail",
                    "exit_code": proc.returncode,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "stdout": stdout,
                    "stderr": stderr,
                    "stdout_sha256": sha256_text(proc.stdout),
                    "stderr_sha256": sha256_text(proc.stderr),
                    "stdout_truncated": stdout_truncated,
                    "stderr_truncated": stderr_truncated,
                }
            except subprocess.TimeoutExpired as exc:
                stdout_raw = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr_raw = exc.stderr if isinstance(exc.stderr, str) else ""
                result = {
                    "id": check["id"],
                    "command": check["command"],
                    "working_directory": check["working_directory"],
                    "acceptance_ids": check["acceptance_ids"],
                    "status": "timeout",
                    "exit_code": None,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "stdout": bounded_text(stdout_raw)[0],
                    "stderr": bounded_text(stderr_raw)[0],
                    "stdout_sha256": sha256_text(stdout_raw),
                    "stderr_sha256": sha256_text(stderr_raw),
                    "timeout_seconds": check["timeout_seconds"],
                }
            except OSError as exc:
                result = {
                    "id": check["id"],
                    "command": check["command"],
                    "working_directory": check["working_directory"],
                    "acceptance_ids": check["acceptance_ids"],
                    "status": "error",
                    "exit_code": None,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "stdout": "",
                    "stderr": str(exc),
                    "stdout_sha256": sha256_text(""),
                    "stderr_sha256": sha256_text(str(exc)),
                }
            check_results.append(result)
        patch_after = patch(self.project, state["current"]["baseline"])
        patch_after_sha = sha256_text(patch_after)
        post_scope = _scope(self.project, state["current"]["baseline"], info)
        mutated = patch_before_sha != patch_after_sha
        all_checks_pass = all(item["status"] == "pass" and item["exit_code"] == 0 for item in check_results)
        status = "pass" if all_checks_pass and pre_scope["status"] == "pass" and post_scope["status"] == "pass" and not mutated else "fail"
        evidence = {
            "schema_version": 1,
            "run_id": state["run_id"],
            "iteration": state["current"]["iteration"],
            "generated_at": now_utc(),
            "contract_sha256": sha256_file(contract_path),
            "baseline": state["current"]["baseline"],
            "patch_sha256": patch_after_sha,
            "status": status,
            "checks": check_results,
            "scope_before": pre_scope,
            "scope_after": post_scope,
            "verification_mutated_patch": mutated,
            "patch_before_sha256": patch_before_sha,
            "patch_after_sha256": patch_after_sha,
        }
        atomic_write_text(iteration_dir / "PATCH.diff", patch_after)
        atomic_write_json(iteration_dir / "EVIDENCE.json", evidence)
        state["current"].update(
            {
                "evidence_sha256": sha256_file(iteration_dir / "EVIDENCE.json"),
                "patch_file_sha256": sha256_file(iteration_dir / "PATCH.diff"),
                "patch_sha256": patch_after_sha,
                "verification_status": status,
                "verified_at": now_utc(),
            }
        )
        state["phase"] = "VERIFIED" if status == "pass" else "VERIFY_FAILED"
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(
            ledger_path(self.project, state["run_id"]),
            "slice.verified",
            {"iteration": state["current"]["iteration"], "status": status, "evidence_sha256": state["current"]["evidence_sha256"], "patch_sha256": patch_after_sha},
        )
        return {"phase": state["phase"], "status": status, "checks": [{"id": x["id"], "status": x["status"], "exit_code": x["exit_code"]} for x in check_results], "scope": post_scope, "verification_mutated_patch": mutated, "evidence_path": str((iteration_dir / "EVIDENCE.json").relative_to(self.project)), "next": self.next_action()}

    def prepare_pull(self, count: int = 2) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"VERIFIED", "REVIEWING"})
        if state["current"].get("verification_status") != "pass":
            raise StateError("Pull cannot begin without passing executable evidence")
        if count < 2 or count > 8:
            raise ValidationError("reviewer count must be from 2 to 8")
        contract, info, _ = _contract_and_info(self.project, state)
        del contract
        iteration_dir = current_iteration_dir(self.project, state)
        evidence = read_json(iteration_dir / "EVIDENCE.json")
        if sha256_file(iteration_dir / "EVIDENCE.json") != state["current"]["evidence_sha256"]:
            raise IntegrityError("EVIDENCE.json changed after verification")
        if sha256_file(iteration_dir / "PATCH.diff") != state["current"]["patch_file_sha256"]:
            raise IntegrityError("PATCH.diff changed after verification")
        hashes = _evidence_hashes(iteration_dir)
        reviews_dir = iteration_dir / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        for index in range(1, count + 1):
            path = reviews_dir / f"review-{index}.json"
            if path.exists() and "REPLACE_ME" not in path.read_text(encoding="utf-8"):
                raise StateError(f"refusing to overwrite completed review: {path}")
            atomic_write_json(path, review_template(state["run_id"], state["current"]["iteration"], hashes, sorted(info["acceptance"]), index))
        judgment_path = iteration_dir / "JUDGMENT.json"
        if judgment_path.exists() and "REPLACE_ME" not in judgment_path.read_text(encoding="utf-8"):
            raise StateError("refusing to overwrite completed JUDGMENT.json")
        atomic_write_json(judgment_path, judgment_template(state["run_id"], state["current"]["iteration"], hashes, sorted(info["acceptance"])))
        state["phase"] = "REVIEWING"
        state["current"]["review_template_count"] = count
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "pull.prepared", {"iteration": state["current"]["iteration"], "reviewer_slots": count, "artifact_hashes": hashes})
        return {"phase": "REVIEWING", "reviews_dir": str(reviews_dir.relative_to(self.project)), "judgment_path": str(judgment_path.relative_to(self.project)), "artifact_hashes": hashes, "next": self.next_action()}

    def pull(self) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"REVIEWING"})
        _contract, info, _path = _contract_and_info(self.project, state)
        iteration_dir = current_iteration_dir(self.project, state)
        evidence = read_json(iteration_dir / "EVIDENCE.json")
        if evidence.get("status") != "pass":
            raise IntegrityError("Pull input evidence is not passing")
        hashes = _evidence_hashes(iteration_dir)
        reviews = [read_json(path) for path in sorted((iteration_dir / "reviews").glob("review-*.json"))]
        judgment = read_json(iteration_dir / "JUDGMENT.json")
        result = validate_pull(
            reviews,
            judgment,
            run_id=state["run_id"],
            iteration=state["current"]["iteration"],
            hashes=hashes,
            acceptance_ids=info["acceptance"],
            builder=info["builder"],
            evidence_check_ids=_passed_check_ids(evidence),
        )
        gate = {
            "schema_version": 1,
            "run_id": state["run_id"],
            "iteration": state["current"]["iteration"],
            "generated_at": now_utc(),
            "artifact_hashes": hashes,
            **result,
        }
        atomic_write_json(iteration_dir / "REVIEW_GATE.json", gate)
        state["phase"] = "REVIEWED"
        state["current"].update(
            {
                "review_gate_sha256": sha256_file(iteration_dir / "REVIEW_GATE.json"),
                "judgment_sha256": sha256_file(iteration_dir / "JUDGMENT.json"),
                "review_decision": result["decision"],
                "proof_level": result["proof_level"],
                "reviewed_at": now_utc(),
            }
        )
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "pull.decided", {"iteration": state["current"]["iteration"], "decision": result["decision"], "proof_level": result["proof_level"], "gate_sha256": state["current"]["review_gate_sha256"]})
        return {"phase": "REVIEWED", **result, "gate_path": str((iteration_dir / "REVIEW_GATE.json").relative_to(self.project)), "next": self.next_action()}

    def finish(self, decision: str, *, root_cause: str = "", note: str = "") -> dict[str, Any]:
        decision = decision.lower()
        if decision not in {"accepted", "done", "rework", "blocked", "stopped", "pivot"}:
            raise ValidationError("finish decision must be accepted, done, rework, blocked, stopped, or pivot")
        _, state = active_run(self.project)
        if decision in {"accepted", "done", "rework"}:
            require_phase(state, {"REVIEWED"})
            _contract, info, _ = _contract_and_info(self.project, state)
            iteration_dir = current_iteration_dir(self.project, state)
            if sha256_file(iteration_dir / "REVIEW_GATE.json") != state["current"].get("review_gate_sha256"):
                raise IntegrityError("REVIEW_GATE.json changed after the deterministic judgment gate")
            review_decision = state["current"].get("review_decision")
            if decision in {"accepted", "done"} and review_decision != "PASS":
                raise StateError(f"{decision.upper()} requires a PASS review gate")
            if decision == "rework" and review_decision == "PASS":
                raise StateError("a PASS gate should be accepted or completed, not called rework")
            if decision == "done":
                spec, spec_info = _spec_info(self.project, state)
                del spec
                if not info["final"]:
                    raise StateError("DONE requires contract.final=true")
                if info["acceptance"] != spec_info["acceptance_ids"] or info["requirements"] != spec_info["requirement_ids"]:
                    raise StateError("DONE requires a cumulative final contract covering every locked requirement and acceptance criterion")
            record = {
                "iteration": state["current"]["iteration"],
                "decision": decision.upper(),
                "closed_at": now_utc(),
                "contract_sha256": state["current"]["contract_sha256"],
                "evidence_sha256": state["current"]["evidence_sha256"],
                "patch_sha256": state["current"]["patch_sha256"],
                "review_gate_sha256": state["current"]["review_gate_sha256"],
                "proof_level": state["current"]["proof_level"],
                "acceptance_criteria": state["current"]["acceptance_criteria"],
                "scope": self.check_scope(),
                "note": note,
            }
            if decision == "rework":
                root_cause = require_clean_text(root_cause, "root_cause", minimum=4)
                state["current"].setdefault("root_causes", []).append(root_cause)
                state["current"]["attempt"] = int(state["current"].get("attempt", 1)) + 1
                record["root_cause"] = root_cause
                state["history"].append(record)
                repeated = state["current"]["root_causes"].count(root_cause) >= 2
                no_progress = len(state["current"]["root_causes"]) >= 2
                if repeated or no_progress:
                    state["phase"] = "PUSH_REVIEW"
                    state["pending_pivot_reason"] = "repeated root cause" if repeated else "two review cycles without accepted progress"
                else:
                    state["phase"] = "IMPLEMENTING"
                state["updated_at"] = now_utc()
                write_run_state(self.project, state)
                append_ledger(ledger_path(self.project, state["run_id"]), "slice.rework", {"iteration": state["current"]["iteration"], "root_cause": root_cause, "next_phase": state["phase"]})
                return {"phase": state["phase"], "decision": "REWORK", "root_cause": root_cause, "next": self.next_action()}
            state["history"].append(record)
            state["iteration"] = state["current"]["iteration"]
            state["accepted_criteria"] = sorted(set(state.get("accepted_criteria", [])) | set(state["current"]["acceptance_criteria"]))
            final_payload: dict[str, Any] | None = None
            if decision == "done":
                base = run_dir(self.project, state["run_id"])
                final_patch = patch(self.project, state["run_baseline"])
                final_patch_path = base / "FINAL_PATCH.diff"
                atomic_write_text(final_patch_path, final_patch)
                final_receipt = {
                    "schema_version": 1,
                    "run_id": state["run_id"],
                    "generated_at": now_utc(),
                    "goal_sha256": state["goal_sha256"],
                    "lock_file_sha256": state["lock_file_sha256"],
                    "run_baseline": state["run_baseline"],
                    "final_patch_sha256": sha256_text(final_patch),
                    "accepted_criteria": state["accepted_criteria"],
                    "final_iteration": record,
                    "accepted_iterations": [
                        item for item in state["history"] if item.get("decision") in {"ACCEPTED", "DONE"}
                    ],
                }
                final_receipt_path = base / "FINAL_RECEIPT.json"
                atomic_write_json(final_receipt_path, final_receipt)
                state["final_patch_file_sha256"] = sha256_file(final_patch_path)
                state["final_receipt_sha256"] = sha256_file(final_receipt_path)
                final_payload = {
                    "final_patch_file_sha256": state["final_patch_file_sha256"],
                    "final_receipt_sha256": state["final_receipt_sha256"],
                }
            state["current"] = None
            state["phase"] = "DONE" if decision == "done" else "LOCKED"
            state["updated_at"] = now_utc()
            write_run_state(self.project, state)
            append_ledger(
                ledger_path(self.project, state["run_id"]),
                f"slice.{decision}",
                {**record, **(final_payload or {})},
            )
            return {
                "phase": state["phase"],
                "decision": decision.upper(),
                "accepted_criteria": state["accepted_criteria"],
                **(final_payload or {}),
                "next": self.next_action(),
            }

        require_phase(state, {"DRAFT", "PUSH", "LOCKED", "SLICE_DRAFT", "IMPLEMENTING", "VERIFY_FAILED", "VERIFIED", "REVIEWING", "REVIEWED", "PUSH_REVIEW"})
        phase = decision.upper()
        if phase == "PIVOT":
            phase = "PUSH_REVIEW"
        state["phase"] = phase
        state["terminal_reason"] = require_clean_text(note or root_cause, "reason", minimum=4)
        state["updated_at"] = now_utc()
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "run.concluded" if phase in TERMINAL_PHASES else "run.pivot_requested", {"phase": phase, "reason": state["terminal_reason"]})
        return {"phase": phase, "reason": state["terminal_reason"], "next": self.next_action()}

    def authorize_pivot(self, reason: str) -> dict[str, Any]:
        _, state = active_run(self.project)
        require_phase(state, {"PUSH_REVIEW", "PIVOT"})
        reason = require_clean_text(reason, "pivot reason", minimum=8)
        base = run_dir(self.project, state["run_id"])
        revision_dir = base / "revisions" / f"revision-{state['revision']:04d}"
        revision_dir.mkdir(parents=True, exist_ok=False)
        for name in ("CHARTER.md", "SPEC.json", "PUSH.json", "LOCK.json"):
            source = base / name
            if source.exists():
                source.replace(revision_dir / name)
        goal = (base / "GOAL.txt").read_text(encoding="utf-8").rstrip("\n")
        atomic_write_text(base / "CHARTER.md", charter_template(state["run_id"], goal))
        atomic_write_json(base / "SPEC.json", spec_template(state["run_id"], sha256_text(goal), goal))
        state.setdefault("lock_history", []).append(state.get("lock"))
        state["revision"] += 1
        state["lock"] = None
        state["lock_file_sha256"] = None
        state["current"] = None
        state["phase"] = "DRAFT"
        state["updated_at"] = now_utc()
        state["pivot_reason"] = reason
        write_run_state(self.project, state)
        append_ledger(ledger_path(self.project, state["run_id"]), "run.pivot_authorized", {"revision": state["revision"], "reason": reason, "archived_to": str(revision_dir.relative_to(self.project))})
        return {"phase": "DRAFT", "revision": state["revision"], "archived_to": str(revision_dir.relative_to(self.project)), "next": self.next_action()}

    def integrity(self) -> dict[str, Any]:
        root, state = active_run(self.project)
        del root
        result: dict[str, Any] = {"run_id": state["run_id"], "phase": state["phase"], "ledger": "pass"}
        # read_run_state already verified the ledger.
        if state.get("lock"):
            result["lock_hashes"] = verify_lock(self.project, state)
            result["lock"] = "pass"
        else:
            result["lock"] = "unlocked"
        verified_history = 0
        base = run_dir(self.project, state["run_id"])
        for record in state.get("history", []):
            if record.get("decision") not in {"ACCEPTED", "DONE"}:
                continue
            iteration_dir = base / "iterations" / f"{int(record['iteration']):04d}"
            expected_files = {
                "CONTRACT.json": record.get("contract_sha256"),
                "EVIDENCE.json": record.get("evidence_sha256"),
                "PATCH.diff": record.get("patch_sha256"),
                "REVIEW_GATE.json": record.get("review_gate_sha256"),
            }
            for name, expected in expected_files.items():
                if not expected or sha256_file(iteration_dir / name) != expected:
                    raise IntegrityError(f"historical receipt hash mismatch: iteration {record['iteration']} {name}")
            verified_history += 1
        result["historical_receipts"] = verified_history
        if state.get("phase") == "DONE":
            if sha256_file(base / "FINAL_PATCH.diff") != state.get("final_patch_file_sha256"):
                raise IntegrityError("FINAL_PATCH.diff hash mismatch")
            if sha256_file(base / "FINAL_RECEIPT.json") != state.get("final_receipt_sha256"):
                raise IntegrityError("FINAL_RECEIPT.json hash mismatch")
            result["final_receipt"] = "pass"
        if state.get("current") and state["current"].get("contract_sha256"):
            iteration_dir = current_iteration_dir(self.project, state)
            actual = sha256_file(iteration_dir / "CONTRACT.json")
            if actual != state["current"]["contract_sha256"]:
                raise IntegrityError("active contract hash mismatch")
            result["contract"] = "pass"
            result["scope"] = self.check_scope()
            if state["current"].get("evidence_sha256"):
                if sha256_file(iteration_dir / "EVIDENCE.json") != state["current"]["evidence_sha256"]:
                    raise IntegrityError("evidence receipt hash mismatch")
                if sha256_file(iteration_dir / "PATCH.diff") != state["current"]["patch_file_sha256"]:
                    raise IntegrityError("patch receipt hash mismatch")
                result["evidence"] = "pass"
            if state["current"].get("review_gate_sha256"):
                if sha256_file(iteration_dir / "REVIEW_GATE.json") != state["current"]["review_gate_sha256"]:
                    raise IntegrityError("review gate receipt hash mismatch")
                result["review_gate"] = "pass"
        return result

    def status(self) -> dict[str, Any]:
        root = read_root_state(self.project)
        run_id = root.get("active_run_id")
        if not run_id:
            return {"phase": "IDLE", "active_run_id": None, "next": "Run ./signoff start \"<exact user-visible outcome>\""}
        state = read_run_state(self.project, run_id)
        result = {
            "run_id": run_id,
            "phase": state["phase"],
            "revision": state["revision"],
            "iteration": state["iteration"],
            "accepted_criteria": state.get("accepted_criteria", []),
            "current": state.get("current"),
            "next": self.next_action(),
        }
        try:
            result["integrity"] = self.integrity()
        except SignoffError as exc:
            result["integrity"] = {"status": "fail", "error": str(exc)}
        return result

    def next_action(self) -> str:
        root = read_root_state(self.project)
        run_id = root.get("active_run_id")
        if not run_id:
            return 'Run ./signoff start "<the user’s exact outcome>".'
        state = read_run_state(self.project, run_id)
        phase = state["phase"]
        base = run_dir(self.project, run_id).relative_to(self.project)
        slice_draft_action = "Complete the active CONTRACT.json, then run ./signoff slice."
        if state.get("current"):
            slice_draft_action = (
                f"Complete {base}/iterations/{state['current']['iteration']:04d}/CONTRACT.json, "
                "then run ./signoff slice."
            )
        actions = {
            "DRAFT": f"Complete {base}/CHARTER.md and {base}/SPEC.json, then run ./signoff prepare-push.",
            "PUSH": f"Run independent Push contexts using skills/push, fill {base}/PUSH.json, then run ./signoff lock.",
            "LOCKED": "Run ./signoff prepare-slice to create exactly one bounded iteration contract.",
            "SLICE_DRAFT": slice_draft_action,
            "IMPLEMENTING": "Implement only the active contract; then run ./signoff verify.",
            "VERIFY_FAILED": "Fix only the failed evidence or scope issue without changing locked artifacts; then run ./signoff verify again.",
            "VERIFIED": "Run ./signoff prepare-pull, collect fresh read-only reviews, then run ./signoff pull.",
            "REVIEWING": "Fill every review and JUDGMENT.json against the sealed hashes; then run ./signoff pull.",
            "REVIEWED": "Follow the deterministic gate: ./signoff finish accepted, ./signoff finish done, or ./signoff finish rework --root-cause \"...\".",
            "PUSH_REVIEW": "Implementation is paused. Run ./signoff pivot --reason \"<evidence-based reason>\" or ./signoff finish stopped --note \"<reason>\".",
            "DONE": "Terminal result: DONE. Do not continue implementation under this run.",
            "STOPPED": "Terminal result: STOPPED. Do not continue implementation under this run.",
            "PIVOT": "Terminal result: PIVOT. Start a revised run only through the pivot gate.",
            "BLOCKED": "Terminal result: BLOCKED. Resolve the external blocker before starting a new run.",
        }
        return actions.get(phase, f"Unknown phase {phase}; run ./signoff integrity and inspect STATE.json.")
