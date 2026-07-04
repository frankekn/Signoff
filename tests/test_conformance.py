from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from traction.errors import IntegrityError, StateError, ValidationError
from traction.installer import install
from traction.util import atomic_write_json, read_json

from tests.support import RepoFixture


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

    def test_22_patch_receipt_excludes_signoff_control_artifacts(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
