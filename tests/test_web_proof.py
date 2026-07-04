from __future__ import annotations

from tests.web_server import WebServerTestCase


class WebProofApiTests(WebServerTestCase):
    def test_proof_summary_reports_unknown_draft_evidence(self) -> None:
        mission_id = self.fx.mission_id
        status, payload = self.request("/api/overview")

        self.assertEqual(status, 200)
        proof = payload["data"]["proofSummary"]
        self.assertEqual(proof["missionId"], mission_id)
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

    def test_proof_summary_reviewed_pass_nonfinal_keeps_signoff_unavailable(self) -> None:
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=False)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertNotIn("finish_done", action_ids)
        self.assertIn("finish_accepted", action_ids)
        self.assertIn("finish_rework", action_ids)
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
