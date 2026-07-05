from __future__ import annotations

from traction.util import atomic_write_json, read_json

from tests.web_server import WebServerTestCase


class WebRunApiTests(WebServerTestCase):
    def test_overview_lists_stopped_and_next_run(self) -> None:
        first_run_id = self.fx.run_id
        self.fx.runtime.finish("stopped", note="done for test")
        status, payload = self.request("/api/runs", method="POST", body={"goal": "Second run outcome"})
        self.assertEqual(status, 201)
        second_run_id = payload["data"]["run_id"]

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        runs = payload["data"]["runs"]
        run_ids = [run["runId"] for run in runs]
        self.assertGreaterEqual(len(runs), 2)
        self.assertIn(first_run_id, run_ids)
        self.assertIn(second_run_id, run_ids)
        self.assertTrue(next(run for run in runs if run["runId"] == second_run_id)["active"])
        self.assertFalse(next(run for run in runs if run["runId"] == first_run_id)["active"])

    def test_inactive_run_artifacts_are_read_only(self) -> None:
        first_run_id = self.fx.run_id
        self.fx.runtime.finish("stopped", note="done for test")
        status, payload = self.request("/api/runs", method="POST", body={"goal": "Second run outcome"})
        self.assertEqual(status, 201)
        self.assertNotEqual(payload["data"]["run_id"], first_run_id)
        first_state_path = self.fx.run / "STATE.json"
        first_state = read_json(first_state_path)
        first_state["phase"] = "DRAFT"
        atomic_write_json(first_state_path, first_state)

        status, payload = self.request(f"/api/artifacts?runId={first_run_id}")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"])
        self.assertTrue(all(not artifact["editable"] for artifact in payload["data"]))

    def test_inspect_run_keeps_active_legality_scoped_to_active_run(self) -> None:
        old_run_id = self.fx.run_id
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()
        self.fx.runtime.finish("done")
        status, payload = self.request("/api/runs", method="POST", body={"goal": "Second run outcome"})
        self.assertEqual(status, 201)
        active_run_id = payload["data"]["run_id"]

        status, payload = self.request(f"/api/overview?inspectRunId={old_run_id}")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"]["run_id"], active_run_id)
        self.assertEqual(payload["data"]["proofSummary"]["runId"], old_run_id)
        self.assertEqual(payload["data"]["inspectedRun"]["runId"], old_run_id)
        self.assertEqual(payload["data"]["inspectedRun"]["phase"], "DONE")
        self.assertEqual(payload["data"]["goal"], "Second run outcome")
        self.assertIn("charter", payload["data"]["next"].lower())
        self.assertFalse(payload["data"]["blockedByIntegrity"])
        self.assertFalse(payload["data"]["canStartRun"])
        self.assertTrue(any(path.endswith("/CHARTER.md") for path in payload["data"]["editablePaths"]))
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertEqual(action_ids, ["prepare_push", "finish_stopped"])
        self.assertEqual(payload["data"]["proofSummary"]["finalReceipt"]["status"], "present")

    def test_inspected_historical_run_final_receipt_tamper_is_reported(self) -> None:
        old_run_id = self.fx.run_id
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()
        self.fx.runtime.finish("done")
        receipt = self.fx.run / "FINAL_RECEIPT.json"
        receipt.write_text(receipt.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 2'), encoding="utf-8")
        status, payload = self.request("/api/runs", method="POST", body={"goal": "Second run outcome"})
        self.assertEqual(status, 201)

        status, payload = self.request(f"/api/overview?inspectRunId={old_run_id}")
        self.assertEqual(status, 200)
        final_receipt = payload["data"]["proofSummary"]["finalReceipt"]
        self.assertEqual(final_receipt["status"], "fail")
        self.assertIn("hash mismatch", final_receipt["detail"])
