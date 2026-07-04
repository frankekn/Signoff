from __future__ import annotations

from signoff.util import atomic_write_json, read_json

from tests.web_server import WebServerTestCase


class WebMissionApiTests(WebServerTestCase):
    def test_overview_lists_stopped_and_next_mission(self) -> None:
        first_mission_id = self.fx.mission_id
        self.fx.runtime.finish("stopped", note="done for test")
        status, payload = self.request("/api/missions", method="POST", body={"goal": "Second mission outcome"})
        self.assertEqual(status, 201)
        second_mission_id = payload["data"]["mission_id"]

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        missions = payload["data"]["missions"]
        mission_ids = [mission["missionId"] for mission in missions]
        self.assertGreaterEqual(len(missions), 2)
        self.assertIn(first_mission_id, mission_ids)
        self.assertIn(second_mission_id, mission_ids)
        self.assertTrue(next(mission for mission in missions if mission["missionId"] == second_mission_id)["active"])
        self.assertFalse(next(mission for mission in missions if mission["missionId"] == first_mission_id)["active"])

    def test_inactive_mission_artifacts_are_read_only(self) -> None:
        first_mission_id = self.fx.mission_id
        self.fx.runtime.finish("stopped", note="done for test")
        status, payload = self.request("/api/missions", method="POST", body={"goal": "Second mission outcome"})
        self.assertEqual(status, 201)
        self.assertNotEqual(payload["data"]["mission_id"], first_mission_id)
        first_state_path = self.fx.mission / "STATE.json"
        first_state = read_json(first_state_path)
        first_state["phase"] = "DRAFT"
        atomic_write_json(first_state_path, first_state)

        status, payload = self.request(f"/api/artifacts?missionId={first_mission_id}")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"])
        self.assertTrue(all(not artifact["editable"] for artifact in payload["data"]))

    def test_inspect_mission_keeps_active_legality_scoped_to_active_mission(self) -> None:
        old_mission_id = self.fx.mission_id
        self.fx.lock()
        iteration_dir = self.fx.passing_evidence(final=True)
        self.fx.fill_pull(iteration_dir)
        self.fx.runtime.pull()
        self.fx.runtime.finish("done")
        status, payload = self.request("/api/missions", method="POST", body={"goal": "Second mission outcome"})
        self.assertEqual(status, 201)
        active_mission_id = payload["data"]["mission_id"]

        status, payload = self.request(f"/api/overview?inspectMissionId={old_mission_id}")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"]["mission_id"], active_mission_id)
        self.assertEqual(payload["data"]["proofSummary"]["missionId"], old_mission_id)
        self.assertEqual(payload["data"]["inspectedMission"]["missionId"], old_mission_id)
        self.assertEqual(payload["data"]["inspectedMission"]["phase"], "DONE")
        self.assertEqual(payload["data"]["goal"], "Second mission outcome")
        self.assertIn("charter", payload["data"]["next"].lower())
        self.assertFalse(payload["data"]["blockedByIntegrity"])
        self.assertFalse(payload["data"]["canStartMission"])
        self.assertTrue(any(path.endswith("/CHARTER.md") for path in payload["data"]["editablePaths"]))
        action_ids = [action["id"] for action in payload["data"]["actions"]]
        self.assertEqual(action_ids, ["prepare_push", "finish_stopped"])
        self.assertEqual(payload["data"]["proofSummary"]["finalReceipt"]["status"], "present")
