from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

from traction.errors import IntegrityError, StateError, ValidationError
from traction.installer import install
from traction.util import atomic_write_json, read_json, sha256_file

from tests.support import RepoFixture


def _legacy_mission_id(run_id: str) -> str:
    return "mission-" + run_id.removeprefix("run-")


def _move_current_control_to_legacy(project: Path, run_id: str) -> tuple[Path, str]:
    current_root = project / ".traction"
    legacy_root = project / ".signoff"
    mission_id = _legacy_mission_id(run_id)
    mission_dir = legacy_root / "missions" / mission_id
    current_root.rename(legacy_root)
    runs_dir = legacy_root / "runs"
    missions_dir = legacy_root / "missions"
    runs_dir.rename(missions_dir)
    (missions_dir / run_id).rename(mission_dir)
    root = read_json(legacy_root / "state.json")
    root["active_mission_id"] = mission_id
    root["missions"] = [mission_id]
    root.pop("active_run_id", None)
    root.pop("runs", None)
    atomic_write_json(legacy_root / "state.json", root)
    state = read_json(mission_dir / "STATE.json")
    state["mission_id"] = mission_id
    state.pop("run_id", None)
    if "run_baseline" in state:
        state["mission_baseline"] = state.pop("run_baseline")
    atomic_write_json(mission_dir / "STATE.json", state)
    return legacy_root, mission_id


class ConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RepoFixture()

    def tearDown(self) -> None:
        self.fx.close()

    def test_01_golden_path_reaches_done_with_receipts(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration)
        result = self.fx.runtime.pull()
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(self.fx.runtime.finish("done")["phase"], "DONE")
        self.assertTrue((self.fx.run / "FINAL_PATCH.diff").is_file())
        self.assertTrue((self.fx.run / "FINAL_RECEIPT.json").is_file())
        integrity = self.fx.runtime.integrity()
        self.assertEqual(integrity["ledger"], "pass")
        self.assertEqual(integrity["final_receipt"], "pass")

    def test_02_placeholder_draft_cannot_reach_push(self) -> None:
        with self.assertRaises(ValidationError):
            self.fx.runtime.prepare_push()

    def test_03_locked_spec_tamper_is_detected(self) -> None:
        self.fx.lock()
        spec = read_json(self.fx.run / "SPEC.json")
        spec["constraints"].append("Quietly changed after lock")
        atomic_write_json(self.fx.run / "SPEC.json", spec)
        with self.assertRaises(IntegrityError):
            self.fx.runtime.prepare_slice()

    def test_04_advisor_with_empty_falsifiable_criteria_is_rejected(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        push["advisors"][0]["falsifiable_criteria"] = []
        atomic_write_json(self.fx.run / "PUSH.json", push)
        with self.assertRaises(ValidationError):
            self.fx.runtime.lock()

    def test_05_push_duplicate_context_is_not_quorum(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push(duplicate_context=True)
        with self.assertRaises(ValidationError):
            self.fx.runtime.lock()

    def test_06_advisor_verdict_split_without_evidence_resolution_is_rejected(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push(conflict=True, resolve=False)
        with self.assertRaises(ValidationError):
            self.fx.runtime.lock()

    def test_07_push_conflict_can_be_resolved_by_evidence(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push(conflict=True, resolve=True)
        self.assertEqual(self.fx.runtime.lock()["phase"], "LOCKED")

    def test_push_route_divergence_without_evidence_resolution_is_rejected(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        push["advisors"][1]["route"] = "Replace the application with a new CLI and defer the focused unit test."
        atomic_write_json(self.fx.run / "PUSH.json", push)

        with self.assertRaisesRegex(ValidationError, "route-divergence"):
            self.fx.runtime.lock()

    def test_push_route_divergence_can_be_resolved_by_evidence(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        push["advisors"][1]["route"] = "Replace the application with a new CLI and defer the focused unit test."
        push["decision"]["conflict_resolutions"] = [
            {
                "topic": "route-divergence",
                "basis": "existing_evidence",
                "evidence": "The locked spec only needs app.py behavior, so the one-file route is the bounded route.",
                "conclusion": "Use the app.py route and reject the broader CLI rewrite.",
            }
        ]
        atomic_write_json(self.fx.run / "PUSH.json", push)

        self.assertEqual(self.fx.runtime.lock()["phase"], "LOCKED")

    def test_unanimous_stop_advisors_cannot_be_overridden_without_evidence(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        for advisor in push["advisors"]:
            advisor["verdict"] = "STOP"
        push["decision"]["verdict"] = "PROCEED"
        push["decision"]["rationale"] = "The chair wants to continue despite unanimous advisor stop verdicts."
        atomic_write_json(self.fx.run / "PUSH.json", push)

        with self.assertRaisesRegex(ValidationError, "advisor-unanimous-stop"):
            self.fx.runtime.lock()

    def test_unanimous_advisor_override_can_be_resolved_by_evidence(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        for advisor in push["advisors"]:
            advisor["verdict"] = "STOP"
        push["decision"]["verdict"] = "PROCEED"
        push["decision"]["rationale"] = "The chair uses existing evidence to continue despite unanimous stop advice."
        push["decision"]["conflict_resolutions"] = [
            {
                "topic": "advisor-unanimous-stop",
                "basis": "existing_evidence",
                "evidence": "The existing failing unit test and one-file implementation path keep the slice bounded.",
                "conclusion": "Proceed with the one-file route despite the unanimous stop advice.",
            }
        ]
        atomic_write_json(self.fx.run / "PUSH.json", push)

        self.assertEqual(self.fx.runtime.lock()["phase"], "LOCKED")

    def test_chair_can_stop_without_overriding_unanimous_proceed_advisors(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        push["decision"]["verdict"] = "STOP"
        push["decision"]["rationale"] = "Stopping is the honest terminal decision for this run."
        atomic_write_json(self.fx.run / "PUSH.json", push)

        self.assertEqual(self.fx.runtime.lock()["phase"], "STOPPED")

    def test_08_unmapped_file_fails_scope(self) -> None:
        self.fx.lock()
        self.fx.activate()
        self.fx.implement()
        (self.fx.project / "surprise.txt").write_text("scope creep\n", encoding="utf-8")
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertIn("surprise.txt", result["scope"]["unmapped_files"])

    def test_09_changed_line_budget_is_enforced(self) -> None:
        self.fx.lock()
        self.fx.activate(changed_lines=1)
        self.fx.implement()
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["scope"]["line_budget_overflow"])

    def test_10_failing_command_cannot_be_called_evidence(self) -> None:
        self.fx.lock()
        self.fx.activate(command=["git", "grep", "-F", "-q", "definitely-not-present", "--", "app.py"])
        self.fx.implement()
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["checks"][0]["exit_code"], 1)

    def test_11_verification_mutation_invalidates_patch(self) -> None:
        self.fx.lock()
        command = ["git", "checkout", "--", "app.py"]
        self.fx.activate(command=command)
        self.fx.implement()
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["verification_mutated_patch"])

    def test_12_builder_cannot_count_as_reviewer(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.fill_pull(iteration, reviewer_one_is_builder=True)
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_13_duplicate_review_context_is_not_quorum(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.fill_pull(iteration, duplicate_context=True)
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_14_unknown_cannot_be_promoted_to_pass(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.fill_pull(iteration, verdicts=("PASS", "UNKNOWN"))
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_15_vote_is_not_valid_arbitration(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.fill_pull(iteration, verdicts=("PASS", "FAIL"), resolution_basis="vote")
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_16_evidence_can_resolve_review_disagreement(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.fill_pull(iteration, verdicts=("PASS", "FAIL"), resolution_basis="experiment")
        self.assertEqual(self.fx.runtime.pull()["decision"], "PASS")

    def test_17_high_finding_cannot_be_silently_dismissed(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        finding = {
            "id": "F-001",
            "severity": "high",
            "acceptance_ids": ["AC-001"],
            "claim": "A high-severity regression remains in the sealed patch.",
            "evidence": "The reviewer identifies the affected execution path.",
            "falsifier": "A focused passing check covering the claimed regression.",
            "recommended_disposition": "ACT_ON",
        }
        disposition = {
            "finding_id": "F-001",
            "disposition": "DISMISSED",
            "rationale": "The lead does not believe the reviewer.",
            "evidence_ref": "",
        }
        self.fx.fill_pull(iteration, finding=finding, disposition=disposition)
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_18_ledger_tamper_is_detected(self) -> None:
        self.fx.lock()
        ledger = self.fx.run / "LEDGER.jsonl"
        lines = ledger.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["payload"]["goal_sha256"] = "0" * 64
        lines[0] = json.dumps(record)
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            self.fx.runtime.status()

    def test_19_done_requires_cumulative_final_contract(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence(final=False)
        self.fx.fill_pull(iteration)
        self.fx.runtime.pull()
        with self.assertRaises(StateError):
            self.fx.runtime.finish("done")

    def test_20_install_is_idempotent_and_local(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        first = install(self.fx.project, source_root)
        second = install(self.fx.project, source_root)
        self.assertEqual(first["status"], "installed")
        self.assertEqual(second["status"], "installed")
        self.assertTrue((self.fx.project / "traction").is_file())
        self.assertTrue((self.fx.project / ".agents" / "skills" / "loop" / "SKILL.md").is_file())
        self.assertTrue((self.fx.project / ".traction" / "runtime" / "traction" / "cli.py").is_file())

    def test_21_historical_receipt_tamper_is_detected(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration)
        self.fx.runtime.pull()
        self.fx.runtime.finish("done")
        evidence = iteration / "EVIDENCE.json"
        data = read_json(evidence)
        data["status"] = "fail"
        atomic_write_json(evidence, data)
        with self.assertRaises(IntegrityError):
            self.fx.runtime.integrity()

    def test_22_patch_receipt_excludes_traction_control_artifacts(self) -> None:
        control = self.fx.project / "AGENTS.md"
        control.write_text("initial control instructions\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.fx.project), "add", "AGENTS.md"], check=True)
        subprocess.run(["git", "-C", str(self.fx.project), "commit", "-qm", "track control artifact"], check=True)
        self.fx.lock()
        control.write_text("modified control instructions\n", encoding="utf-8")
        scratch = self.fx.project / ".traction" / "agent-scratch.log"
        scratch.write_text("untracked control noise\n", encoding="utf-8")
        iteration = self.fx.passing_evidence(final=True)
        sealed_patch = (iteration / "PATCH.diff").read_text(encoding="utf-8")
        self.assertNotIn("diff --git a/AGENTS.md", sealed_patch)
        self.assertNotIn("modified control instructions", sealed_patch)
        self.assertNotIn("diff --git a/.traction/", sealed_patch)
        self.assertNotIn("agent-scratch.log", sealed_patch)

    def test_23_charter_tamper_after_lock_is_detected(self) -> None:
        self.fx.lock()
        charter = (self.fx.run / "CHARTER.md").read_text(encoding="utf-8")
        (self.fx.run / "CHARTER.md").write_text(charter + "\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            self.fx.runtime.prepare_slice()

    def test_24_push_tamper_after_lock_is_detected(self) -> None:
        self.fx.lock()
        push = read_json(self.fx.run / "PUSH.json")
        push["decision"]["rationale"] += " tampered"
        atomic_write_json(self.fx.run / "PUSH.json", push)
        with self.assertRaises(IntegrityError):
            self.fx.runtime.prepare_slice()

    def test_25_contract_tamper_after_activation_is_detected(self) -> None:
        self.fx.lock()
        iteration = self.fx.activate()
        contract = read_json(iteration / "CONTRACT.json")
        contract["title"] = "Tampered title for test"
        atomic_write_json(iteration / "CONTRACT.json", contract)
        with self.assertRaises(IntegrityError):
            self.fx.runtime.check_scope()

    def test_26_forbidden_path_violation_fails_scope(self) -> None:
        self.fx.lock()
        self.fx.activate(forbidden_paths=[".git/**", ".traction/**", "surprise.txt"])
        self.fx.implement()
        (self.fx.project / "surprise.txt").write_text("forbidden\n", encoding="utf-8")
        scope = self.fx.runtime.check_scope()
        self.assertEqual(scope["status"], "fail")
        self.assertIn("surprise.txt", scope["forbidden_files"])
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["scope"]["status"], "fail")
        self.assertIn("surprise.txt", result["scope"]["forbidden_files"])

    def test_27_production_file_budget_overflow_fails_scope(self) -> None:
        self.fx.lock()
        self.fx.activate(production_files=1)
        self.fx.implement()
        (self.fx.project / "extra.py").write_text("# extra production file\n", encoding="utf-8")
        scope = self.fx.runtime.check_scope()
        self.assertEqual(scope["status"], "fail")
        self.assertTrue(scope["file_budget_overflow"])
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["scope"]["file_budget_overflow"])

    def test_28_oracle_timeout_fails_verification(self) -> None:
        self.fx.lock()
        self.fx.activate(
            command=[sys.executable, "-c", "import time; time.sleep(5)"],
            timeout_seconds=1,
        )
        self.fx.implement()
        result = self.fx.runtime.verify()
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["checks"][0]["status"], "timeout")
        self.assertEqual(result["phase"], "VERIFY_FAILED")

    def test_29_review_with_wrong_sealed_hash_is_rejected(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        self.fx.runtime.prepare_pull()
        self.fx.fill_pull(iteration, prepare=False)
        review = read_json(iteration / "reviews" / "review-1.json")
        review["artifact_hashes"]["patch"] = "0" * 64
        atomic_write_json(iteration / "reviews" / "review-1.json", review)
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_30_pass_judgment_cannot_retain_act_on_finding(self) -> None:
        self.fx.lock()
        iteration = self.fx.passing_evidence()
        finding = {
            "id": "F-001",
            "severity": "medium",
            "acceptance_ids": ["AC-001"],
            "claim": "A retained finding still requires action before acceptance.",
            "evidence": "The reviewer identifies work that remains in the sealed patch.",
            "falsifier": "A focused passing check proving the finding is already resolved.",
            "recommended_disposition": "ACT_ON",
        }
        disposition = {
            "finding_id": "F-001",
            "disposition": "ACT_ON",
            "rationale": "The lead agrees this must be addressed before acceptance.",
            "evidence_ref": "",
        }
        self.fx.fill_pull(iteration, finding=finding, disposition=disposition, judgment_decision="PASS")
        with self.assertRaises(ValidationError):
            self.fx.runtime.pull()

    def test_31_push_conflict_resolution_with_vote_basis_is_rejected(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push(conflict=True, resolve=False)
        push = read_json(self.fx.run / "PUSH.json")
        push["decision"]["conflict_resolutions"] = [
            {
                "topic": "verdict-split",
                "basis": "vote",
                "evidence": "Both advisors participated and one side had more votes.",
                "conclusion": "Proceed because the majority favored implementation.",
            }
        ]
        atomic_write_json(self.fx.run / "PUSH.json", push)
        with self.assertRaises(ValidationError):
            self.fx.runtime.lock()

    def test_32_install_replaces_legacy_signoff_managed_block(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        control = self.fx.project / "AGENTS.md"
        control.write_text(
            "\n".join(
                [
                    "Existing instructions.",
                    "",
                    "<!-- signoff:managed:start -->",
                    "Run ./signoff status before editing.",
                    "<!-- signoff:managed:end -->",
                    "",
                    "Keep this footer.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        install(self.fx.project, source_root)

        text = control.read_text(encoding="utf-8")
        self.assertNotIn("signoff:managed", text)
        self.assertNotIn("./signoff", text)
        self.assertEqual(text.count("traction:managed:start"), 1)
        self.assertIn("./traction status", text)
        self.assertIn("Keep this footer.", text)

    def test_33_install_refuses_active_legacy_signoff_state(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        legacy_root, _mission_id = _move_current_control_to_legacy(self.fx.project, self.fx.run_id)

        with self.assertRaisesRegex(StateError, "old ./signoff CLI"):
            install(self.fx.project, source_root)

        self.assertTrue(legacy_root.exists())
        self.assertFalse((self.fx.project / ".traction").exists())

    def test_34_install_migrates_terminal_legacy_signoff_state(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        self.fx.runtime.finish("stopped", note="done for test")
        legacy_root, mission_id = _move_current_control_to_legacy(self.fx.project, self.fx.run_id)

        install(self.fx.project, source_root)

        current_root = self.fx.project / ".traction"
        run_id = "run-" + mission_id.removeprefix("mission-")
        self.assertFalse(legacy_root.exists())
        self.assertTrue((current_root / "state.json").is_file())
        self.assertTrue((current_root / "runs" / run_id / "STATE.json").is_file())
        root = read_json(current_root / "state.json")
        state = read_json(current_root / "runs" / run_id / "STATE.json")
        self.assertEqual(root["active_run_id"], run_id)
        self.assertEqual(root["runs"], [run_id])
        self.assertEqual(state["run_id"], run_id)
        self.assertNotIn("active_mission_id", root)
        self.assertNotIn("missions", root)
        self.assertNotIn("mission_id", state)
        status = self.fx.runtime.status()
        self.assertEqual(status["run_id"], self.fx.run_id)
        self.assertEqual(status["phase"], "STOPPED")
        self.assertEqual(self.fx.runtime.doctor()["status"], "pass")

    def test_install_removes_manifest_owned_legacy_signoff_launchers_and_skills(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        self.fx.runtime.finish("stopped", note="done for test")
        legacy_root, _mission_id = _move_current_control_to_legacy(self.fx.project, self.fx.run_id)
        legacy_paths = [
            "signoff",
            "signoff.cmd",
            "signoff.ps1",
            ".agents/skills/signoff/SKILL.md",
            ".agents/skills/council/SKILL.md",
            ".agents/skills/roast/SKILL.md",
            ".claude/skills/signoff/SKILL.md",
            ".claude/skills/council/SKILL.md",
            ".claude/skills/roast/SKILL.md",
            ".gemini/skills/signoff/SKILL.md",
            ".gemini/skills/council/SKILL.md",
            ".gemini/skills/roast/SKILL.md",
        ]
        for relative in legacy_paths:
            path = self.fx.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"legacy managed file: {relative}\n", encoding="utf-8")
        atomic_write_json(
            legacy_root / "install-manifest.json",
            {
                "schema_version": 1,
                "files": {
                    relative: sha256_file(self.fx.project / relative)
                    for relative in legacy_paths
                },
            },
        )

        install(self.fx.project, source_root)

        for relative in legacy_paths:
            self.assertFalse((self.fx.project / relative).exists(), relative)
        for host in (".agents", ".claude", ".gemini"):
            for skill in ("signoff", "council", "roast"):
                self.assertFalse((self.fx.project / host / "skills" / skill).exists())
        self.assertTrue((self.fx.project / "traction").is_file())
        self.assertTrue((self.fx.project / ".agents" / "skills" / "traction" / "SKILL.md").is_file())

    def test_stopping_from_pivot_records_terminal_state_without_accepting_work(self) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.run / "PUSH.json")
        push["decision"]["verdict"] = "PIVOT"
        push["decision"]["rationale"] = "The goal needs a revised route before implementation."
        push["decision"]["conflict_resolutions"] = [
            {
                "topic": "advisor-unanimous-proceed",
                "basis": "user_decision",
                "evidence": "The user-facing route needs revision before implementation continues.",
                "conclusion": "Record a PIVOT terminal state before any implementation slice.",
            }
        ]
        atomic_write_json(self.fx.run / "PUSH.json", push)
        self.assertEqual(self.fx.runtime.lock()["phase"], "PIVOT")

        with self.assertRaises(StateError):
            self.fx.runtime.finish("accepted")
        with self.assertRaises(StateError):
            self.fx.runtime.finish("done")

        result = self.fx.runtime.finish("stopped", note="stop the pivot instead")
        self.assertEqual(result["phase"], "STOPPED")
        self.assertEqual(self.fx.runtime.status()["phase"], "STOPPED")

    def test_35_installed_launcher_ignores_project_traction_module(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        (self.fx.project / "traction.py").write_text(
            'raise RuntimeError("project traction.py shadowed bundled runtime")\n',
            encoding="utf-8",
        )
        install(self.fx.project, source_root)

        proc = subprocess.run(
            [str(self.fx.project / "traction"), "doctor"],
            cwd=self.fx.project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "pass")

    def test_36_build_release_excludes_legacy_signoff_control_dir(self) -> None:
        source = Path(__file__).resolve().parents[1] / "scripts" / "build_release.py"
        module = ast.parse(source.read_text(encoding="utf-8"))
        excluded_parts: set[str] | None = None
        for statement in module.body:
            if not isinstance(statement, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "EXCLUDED_PARTS" for target in statement.targets):
                continue
            excluded_parts = ast.literal_eval(statement.value)
            break

        if excluded_parts is None:
            self.fail("EXCLUDED_PARTS was not found")
        self.assertIn(".traction", excluded_parts)
        self.assertIn(".signoff", excluded_parts)


if __name__ == "__main__":
    unittest.main()
