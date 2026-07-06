from __future__ import annotations

from traction.util import atomic_write_json, read_json

from tests.web_server import WebServerTestCase


class WebProofApiTests(WebServerTestCase):
    def test_proof_summary_reports_unknown_draft_evidence(self) -> None:
        run_id = self.fx.run_id
        status, payload = self.request("/api/overview")

        self.assertEqual(status, 200)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["runId"], run_id)
        self.assertEqual(proof["evidence"]["status"], "UNKNOWN")
        self.assertEqual(proof["evidence"]["detail"], "not yet produced")
        self.assertEqual(proof["scope"]["status"], "UNKNOWN")
        self.assertEqual(proof["patch"]["status"], "UNKNOWN")
        self.assertEqual(proof["reviewGate"]["decision"], "UNKNOWN")
        self.assertEqual(proof["acceptedCriteria"]["count"], 0)
        self.assertEqual(proof["acceptedCriteria"]["items"], [])
        self.assertIsNone(proof["contract"]["final"])
        self.assertEqual(proof["finalReceipt"]["status"], "UNKNOWN")

    def test_proof_summary_reports_failed_verification(self) -> None:
        self.fx.lock()
        self.fx.activate(command=["git", "grep", "-F", "-q", "definitely-not-present", "--", "app.py"])
        result = self.fx.runtime.verify()
        self.assertEqual(result["phase"], "VERIFY_FAILED")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["evidence"]["status"], "fail")
        self.assertEqual(proof["commands"][0]["id"], "V-001")
        self.assertEqual(proof["commands"][0]["status"], "fail")
        self.assertEqual(proof["commands"][0]["exitCode"], 1)
        self.assertEqual(proof["scope"]["status"], "pass")
        self.assertEqual(proof["patch"]["hash"], proof["evidence"]["patchHash"])

    def test_proof_summary_reviewed_pass_nonfinal_keeps_terminal_completion_unavailable(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=False)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertNotIn("finish_done", action_ids)
        self.assertIn("finish_accepted", action_ids)
        self.assertNotIn("finish_rework", action_ids)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["reviewGate"]["decision"], "PASS")
        self.assertFalse(proof["contract"]["final"])
        self.assertEqual(proof["acceptedCriteria"]["items"], [])

    def test_proof_summary_reviewed_pass_final_exposes_review_gate_hash(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertIn("finish_done", action_ids)
        proof = payload["data"]["proofSummary"]
        self.assertTrue(proof["contract"]["final"])
        self.assertEqual(proof["reviewGate"]["decision"], "PASS")
        self.assertRegex(proof["reviewGate"]["hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(proof["reviewGate"]["path"].endswith("/REVIEW_GATE.json"))

    def test_reviewed_failed_final_gate_only_exposes_rework_action(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir, verdicts=("FAIL", "FAIL"), judgment_decision="REWORK")
        self.fx.runtime.pull()

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertEqual(action_ids, ["finish_rework"])
        proof = payload["data"]["proofSummary"]
        self.assertTrue(proof["contract"]["final"])
        self.assertEqual(proof["reviewGate"]["decision"], "REWORK")

    def test_reviewed_blocked_gate_exposes_blocked_action(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir, verdicts=("UNKNOWN", "UNKNOWN"), judgment_decision="BLOCKED")
        self.fx.runtime.pull()

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertEqual(action_ids, ["finish_blocked"])
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["reviewGate"]["decision"], "BLOCKED")

    def test_proof_summary_done_exposes_final_receipt(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()
        self.fx.runtime.finish("done")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["finalReceipt"]["status"], "present")
        self.assertRegex(proof["finalReceipt"]["hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(proof["finalReceipt"]["path"].endswith("/FINAL_RECEIPT.json"))

    def test_malformed_contract_does_not_break_overview(self) -> None:
        self.fx.lock()
        self.fx.runtime.prepare_slice()
        iteration_dir = self.fx.run / "iterations" / "0001"
        contract_path = iteration_dir / "CONTRACT.json"
        contract_path.write_text("{not json", encoding="utf-8")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertIn(contract_path.relative_to(self.fx.project).as_posix(), payload["data"]["editablePaths"])
        self.assertIsNone(payload["data"]["proofSummary"]["contract"]["final"])

    def test_finish_blocked_does_not_false_fail_integrity(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir, verdicts=("UNKNOWN", "UNKNOWN"), judgment_decision="BLOCKED")
        self.fx.runtime.pull()
        self.fx.runtime.finish("blocked", note="external quorum unavailable")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"]["phase"], "BLOCKED")
        self.assertFalse(payload["data"]["blockedByIntegrity"])
        self.assertEqual(payload["data"]["integrityStatus"], "pass")

    def test_proof_summary_prefers_active_review_gate_hash_after_rework(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=False)
        self.fx.fill_pull(iteration_dir, verdicts=("FAIL", "FAIL"), judgment_decision="REWORK")
        self.fx.runtime.pull()
        self.fx.runtime.finish("rework", root_cause="review found missing evidence")
        self.fx.implement()
        self.fx.runtime.verify()
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()
        active_gate_hash = read_json(self.fx.run / "STATE.json")["current"]["review_gate_sha256"]

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["reviewGate"]["status"], "present")
        self.assertEqual(proof["reviewGate"]["hash"], active_gate_hash)
        self.assertEqual(proof["reviewGate"]["decision"], "PASS")

    def test_malformed_evidence_does_not_break_overview(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence()
        (iteration_dir / "EVIDENCE.json").write_text("{not json", encoding="utf-8")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["data"]["proofSummary"])
        self.assertEqual(payload["data"]["integrityStatus"], "fail")
