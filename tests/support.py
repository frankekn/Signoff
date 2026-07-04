from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from signoff.runtime import Runtime
from signoff.util import atomic_write_json, read_json


class RepoFixture:
    goal = "Change greet to return hello world"

    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="loop-test-")
        self.project = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "user.name", "Signoff Test"], check=True)
        (self.project / "app.py").write_text('def greet():\n    return "hello"\n', encoding="utf-8")
        (self.project / "test_app.py").write_text(
            'import unittest\nimport app\nclass T(unittest.TestCase):\n    def test_greet(self):\n        self.assertEqual(app.greet(), "hello world")\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.project), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.project), "commit", "-qm", "initial"], check=True)
        self.runtime = Runtime(self.project)
        self.runtime.start(self.goal)
        self.mission_id = self.runtime.status()["mission_id"]
        self.mission = self.project / ".signoff" / "missions" / self.mission_id

    def close(self) -> None:
        self.tmp.cleanup()

    def valid_draft(self) -> None:
        (self.mission / "CHARTER.md").write_text(
            f"""# Mission Charter

- Mission: `{self.mission_id}`
- Exact user outcome (immutable):

> {self.goal}

## User-visible success
Calling greet returns exactly hello world.

## Hard constraints
Preserve all unrelated behavior and user work.

## Non-goals
Do not refactor unrelated files or introduce dependencies.

## Stop / pivot conditions
Stop when executable evidence cannot prove the requested behavior.

## Evidence standard
The focused unit test must pass against the sealed patch.
""",
            encoding="utf-8",
        )
        spec = read_json(self.mission / "SPEC.json")
        spec["acceptance_criteria"][0]["observable"] = "Calling greet returns exactly hello world."
        spec["acceptance_criteria"][0]["oracle"]["description"] = "A focused unit test asserts the exact return value."
        spec["non_goals"] = ["Do not refactor unrelated files."]
        atomic_write_json(self.mission / "SPEC.json", spec)

    def valid_council(self, *, conflict: bool = False, resolve: bool = False, duplicate_context: bool = False) -> None:
        self.runtime.prepare_council()
        council = read_json(self.mission / "COUNCIL.json")
        for index, advisor in enumerate(council["advisors"], start=1):
            advisor["identity"] = {
                "participant_id": f"advisor-{index}",
                "provider": f"provider-{index}",
                "model": f"model-{index}",
                "context_id": "same-context" if duplicate_context else f"advisor-context-{index}",
            }
            advisor["verdict"] = "PROCEED"
            advisor["null_hypothesis"] = "The current behavior may already satisfy the requested outcome."
            advisor["first_move"] = "Run the focused failing unit test before changing code."
            advisor["cut"] = "Exclude every unrelated refactor and dependency change."
            for claim in advisor["claims"]:
                stance = "SUPPORT"
                if conflict and index == 2 and claim["topic_key"] == "feasibility":
                    stance = "OPPOSE"
                claim.update(
                    stance=stance,
                    claim="The route is bounded, valuable, and independently testable.",
                    evidence="The repository contains a focused test and a one-file implementation surface.",
                    falsifier="A baseline check proving the requested behavior already exists or cannot be isolated.",
                )
        council["decision"]["rationale"] = "Independent advisors examined the same claims and support a bounded route."
        council["decision"]["first_slice"] = "Make the focused greet behavior pass without adjacent cleanup."
        council["decision"]["chair"] = {
            "participant_id": "chair",
            "provider": "chair-provider",
            "model": "chair-model",
            "context_id": "chair-context",
        }
        if conflict and resolve:
            council["decision"]["conflict_resolutions"] = [
                {
                    "topic_key": "feasibility",
                    "basis": "existing_evidence",
                    "evidence": "The focused test and one-file path make the route executable within budget.",
                    "conclusion": "Proceed with the smallest implementation slice.",
                }
            ]
        atomic_write_json(self.mission / "COUNCIL.json", council)

    def lock(self, **council_kwargs) -> None:
        self.valid_draft()
        self.valid_council(**council_kwargs)
        self.runtime.lock()

    def activate(
        self,
        *,
        final: bool = True,
        changed_lines: int = 20,
        production_files: int = 1,
        command: list[str] | None = None,
        timeout_seconds: int = 30,
        allowed_paths: list[str] | None = None,
        forbidden_paths: list[str] | None = None,
    ) -> Path:
        self.runtime.prepare_slice()
        iteration_dir = self.mission / "iterations" / "0001"
        contract = read_json(iteration_dir / "CONTRACT.json")
        contract["builder"] = {
            "participant_id": "builder",
            "provider": "builder-provider",
            "model": "builder-model",
            "context_id": "builder-context",
        }
        contract["allowed_paths"] = allowed_paths or ["app.py", "test_app.py"]
        contract["forbidden_paths"] = forbidden_paths or [".git/**", ".signoff/**"]
        contract["exempt_paths"] = ["test_*.py"]
        contract["budgets"] = {"production_files": production_files, "changed_lines": changed_lines}
        contract["verification"] = [
            {
                "id": "V-001",
                "command": command or ["git", "grep", "-F", "-q", 'return "hello world"', "--", "app.py"],
                "timeout_seconds": timeout_seconds,
                "working_directory": ".",
                "acceptance_ids": ["AC-001"],
            }
        ]
        contract["final"] = final
        atomic_write_json(iteration_dir / "CONTRACT.json", contract)
        self.runtime.activate_slice()
        return iteration_dir

    def implement(self) -> None:
        (self.project / "app.py").write_text('def greet():\n    return "hello world"\n', encoding="utf-8")

    def passing_evidence(self, **activate_kwargs) -> Path:
        iteration_dir = self.activate(**activate_kwargs)
        self.implement()
        result = self.runtime.verify()
        if result["status"] != "pass":
            raise AssertionError(result)
        return iteration_dir

    def fill_roast(
        self,
        iteration_dir: Path,
        verdicts: Iterable[str] = ("PASS", "PASS"),
        *,
        prepare: bool = True,
        reviewer_one_is_builder: bool = False,
        duplicate_context: bool = False,
        judgment_decision: str = "PASS",
        resolution_basis: str | None = None,
        finding: dict | None = None,
        disposition: dict | None = None,
    ) -> None:
        if prepare:
            self.runtime.prepare_roast()
        for index, (path, verdict) in enumerate(zip(sorted((iteration_dir / "reviews").glob("review-*.json")), verdicts), start=1):
            review = read_json(path)
            identity = {
                "participant_id": "builder" if reviewer_one_is_builder and index == 1 else f"reviewer-{index}",
                "provider": f"review-provider-{index}",
                "model": f"review-model-{index}",
                "context_id": "builder-context" if reviewer_one_is_builder and index == 1 else ("same-review-context" if duplicate_context else f"review-context-{index}"),
            }
            review["reviewer"] = identity
            review["criteria"][0] = {
                "acceptance_id": "AC-001",
                "verdict": verdict,
                "evidence_refs": ["V-001"] if verdict == "PASS" else [],
                "reason": "The sealed evidence and patch determine this criterion verdict.",
            }
            review["overall"] = "PASS" if verdict == "PASS" else "REWORK"
            if finding and index == 1:
                review["findings"] = [finding]
            atomic_write_json(path, review)
        judgment = read_json(iteration_dir / "JUDGMENT.json")
        judgment["judge"] = {
            "participant_id": "judge",
            "provider": "judge-provider",
            "model": "judge-model",
            "context_id": "judge-context",
        }
        judgment["decision"] = judgment_decision
        judgment["criterion_decisions"][0] = {
            "acceptance_id": "AC-001",
            "verdict": "PASS" if judgment_decision == "PASS" else "FAIL",
            "reason": "The judgment follows executable evidence and the locked criterion.",
        }
        judgment["rationale"] = "The lead judgment accounts for every criterion and preserved finding."
        if resolution_basis:
            judgment["conflict_resolutions"] = [
                {
                    "acceptance_id": "AC-001",
                    "basis": resolution_basis,
                    "evidence_ref": "V-001",
                    "conclusion": "The passed executable check resolves the material disagreement.",
                }
            ]
        if disposition:
            judgment["finding_dispositions"] = [disposition]
        atomic_write_json(iteration_dir / "JUDGMENT.json", judgment)
