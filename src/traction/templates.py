"""Human-readable and agent-fillable artifact templates."""
from __future__ import annotations

from typing import Any


def charter_template(run_id: str, goal: str) -> str:
    return f"""# Run Charter

- Run: `{run_id}`
- Exact user outcome (immutable):

> {goal}

## User-visible success

[fill the observable end state in language a non-technical user can verify]

## Hard constraints

[fill constraints that must never be traded away]

## Non-goals

[fill adjacent work that is explicitly excluded]

## Stop / pivot conditions

[fill conditions under which more implementation would be dishonest or wasteful]

## Evidence standard

[fill the minimum executable or external proof required before DONE]
"""


def spec_template(run_id: str, goal_sha256: str, goal: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "goal_sha256": goal_sha256,
        "requirements": [
            {
                "id": "REQ-001",
                "statement": goal,
                "priority": "must",
                "source": "user",
            }
        ],
        "acceptance_criteria": [
            {
                "id": "AC-001",
                "requirement_ids": ["REQ-001"],
                "observable": "REPLACE_ME with a falsifiable user-visible result",
                "oracle": {
                    "type": "command",
                    "description": "REPLACE_ME with what the verification proves",
                },
            }
        ],
        "non_goals": ["REPLACE_ME with at least one adjacent change that is excluded"],
        "constraints": ["Preserve unrelated user work and existing behavior outside the goal"],
        "stop_conditions": ["Stop or pivot when the goal cannot be proven within the iteration budget"],
        "max_iterations": 5,
    }


def push_template(run_id: str, hashes: dict[str, str]) -> dict[str, Any]:
    def advisor(index: int) -> dict[str, Any]:
        return {
            "identity": {
                "participant_id": f"REPLACE_ME-advisor-{index}",
                "provider": "REPLACE_ME",
                "model": "REPLACE_ME",
                "context_id": f"REPLACE_ME-independent-context-{index}",
            },
            "independent_first_round": True,
            "verdict": "PROCEED",
            "route": "REPLACE_ME with the smallest viable route this advisor recommends",
            "falsifiable_criteria": [
                "REPLACE_ME with an observable outcome that proves or falsifies the route",
            ],
            "risk": "REPLACE_ME with the strongest reason this route fails",
            "first_move": "REPLACE_ME with one executable first move",
            "cut": "REPLACE_ME with work to remove from scope",
        }

    return {
        "schema_version": 1,
        "run_id": run_id,
        "artifact_hashes": hashes,
        "advisors": [advisor(1), advisor(2)],
        "decision": {
            "verdict": "PROCEED",
            "rationale": "REPLACE_ME with evidence-based synthesis of advisor verdicts and routes",
            "route_synthesis": "REPLACE_ME with which advisor route was chosen or how routes were merged",
            "conflict_resolutions": [],
            "first_slice": "REPLACE_ME with the smallest high-leverage acceptance slice",
            "chair": {
                "participant_id": "REPLACE_ME-chair",
                "provider": "REPLACE_ME",
                "model": "REPLACE_ME",
                "context_id": "REPLACE_ME-chair-context",
            },
        },
    }


def contract_template(run_id: str, iteration: int, spec: dict[str, Any], first_slice: str) -> dict[str, Any]:
    requirement_ids = [item["id"] for item in spec["requirements"]]
    acceptance_ids = [item["id"] for item in spec["acceptance_criteria"]]
    return {
        "schema_version": 1,
        "run_id": run_id,
        "iteration": iteration,
        "title": first_slice or "REPLACE_ME with one bounded slice",
        "builder": {
            "participant_id": "REPLACE_ME-builder",
            "provider": "REPLACE_ME",
            "model": "REPLACE_ME",
            "context_id": "REPLACE_ME-builder-context",
        },
        "requirements": requirement_ids[:1],
        "acceptance_criteria": acceptance_ids[:1],
        "allowed_paths": ["REPLACE_ME/**"],
        "forbidden_paths": [".git/**", ".traction/**"],
        "exempt_paths": ["tests/**", "docs/**"],
        "budgets": {"production_files": 5, "changed_lines": 300},
        "verification": [
            {
                "id": "V-001",
                "command": ["python3", "-m", "unittest", "discover", "-s", "tests"],
                "timeout_seconds": 120,
                "working_directory": ".",
                "acceptance_ids": acceptance_ids[:1],
            }
        ],
        "final": False,
    }


def review_template(
    run_id: str,
    iteration: int,
    hashes: dict[str, str],
    acceptance_ids: list[str],
    index: int,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "iteration": iteration,
        "reviewer": {
            "participant_id": f"REPLACE_ME-reviewer-{index}",
            "provider": "REPLACE_ME",
            "model": "REPLACE_ME",
            "context_id": f"REPLACE_ME-fresh-review-context-{index}",
        },
        "artifact_hashes": hashes,
        "read_only": True,
        "criteria": [
            {
                "acceptance_id": acceptance_id,
                "verdict": "UNKNOWN",
                "evidence_refs": [],
                "reason": "REPLACE_ME with evidence tied to this criterion",
            }
            for acceptance_id in acceptance_ids
        ],
        "findings": [],
        "overall": "REWORK",
    }


def judgment_template(run_id: str, iteration: int, hashes: dict[str, str], acceptance_ids: list[str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "iteration": iteration,
        "judge": {
            "participant_id": "REPLACE_ME-judge",
            "provider": "REPLACE_ME",
            "model": "REPLACE_ME",
            "context_id": "REPLACE_ME-fresh-judge-context",
        },
        "artifact_hashes": hashes,
        "decision": "REWORK",
        "criterion_decisions": [
            {
                "acceptance_id": acceptance_id,
                "verdict": "UNKNOWN",
                "reason": "REPLACE_ME",
            }
            for acceptance_id in acceptance_ids
        ],
        "finding_dispositions": [],
        "conflict_resolutions": [],
        "rationale": "REPLACE_ME with an evidence-based lead judgment",
    }
