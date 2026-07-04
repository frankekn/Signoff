from __future__ import annotations

from urllib.request import urlopen

from signoff.util import atomic_write_json, read_json

from tests.web_server import WebServerTestCase


class WebApiTests(WebServerTestCase):
    def test_overview_and_artifact_round_trip(self) -> None:
        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"]["phase"], "DRAFT")
        self.assertEqual(payload["data"]["product"], "Signoff")
        self.assertFalse(payload["data"]["canStartMission"])

        mission_id = payload["data"]["status"]["mission_id"]
        status, payload = self.request(f"/api/artifacts?missionId={mission_id}")
        self.assertEqual(status, 200)
        charter = next(item for item in payload["data"] if item["name"] == "CHARTER.md")
        self.assertTrue(charter["editable"])

        updated = (self.fx.mission / "CHARTER.md").read_text(encoding="utf-8").replace(
            "[fill the observable end state in language a non-technical user can verify]",
            "Calling greet returns exactly hello world for the user.",
        )
        status, payload = self.request(
            "/api/artifact",
            method="PUT",
            body={"path": charter["path"], "content": updated},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["saved"])
        self.assertIn("hello world for the user", (self.fx.mission / "CHARTER.md").read_text(encoding="utf-8"))

    def test_terminal_overview_can_start_next_mission(self) -> None:
        status, payload = self.request("/api/action", method="POST", body={"action": "finish_stopped", "note": "done for test"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["phase"], "STOPPED")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["canStartMission"])

    def test_pivot_and_blocked_are_not_restartable(self) -> None:
        self.fx.runtime.finish("stopped", note="done for test")
        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["canStartMission"])

        self.restart_fixture()
        self.fx.lock()
        iteration = self.fx.passing_evidence(final=True)
        self.fx.fill_roast(iteration)
        self.fx.runtime.roast()
        self.fx.runtime.finish("done")
        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["canStartMission"])

        self.restart_fixture()
        self.conclude_from_push("PIVOT")
        status, payload = self.request("/api/overview")
        create_status, create_payload = self.request("/api/missions", method="POST", body={"goal": "Start after pivot"})
        self.assertEqual(status, 200)
        self.assertFalse(payload["data"]["canStartMission"])
        self.assertEqual(create_status, 400)
        self.assertFalse(create_payload["ok"])

        self.restart_fixture()
        self.conclude_from_push("INSUFFICIENT_QUORUM")
        status, payload = self.request("/api/overview")
        create_status, create_payload = self.request("/api/missions", method="POST", body={"goal": "Start after blocked"})
        self.assertEqual(status, 200)
        self.assertFalse(payload["data"]["canStartMission"])
        self.assertEqual(create_status, 400)
        self.assertFalse(create_payload["ok"])

    def test_hard_integrity_failure_blocks_actions(self) -> None:
        self.fx.lock()
        spec = read_json(self.fx.mission / "SPEC.json")
        spec["constraints"].append("Tampered after lock")
        atomic_write_json(self.fx.mission / "SPEC.json", spec)

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["blockedByIntegrity"])
        self.assertEqual(payload["data"]["integrityStatus"], "fail")
        self.assertIn("inspect", payload["data"]["integrityMessage"].lower())
        self.assertIn("integrity", payload["data"]["next"].lower())
        self.assertEqual(payload["data"]["actions"], [])

        self.restart_fixture()
        self.fx.lock()
        self.fx.activate()
        self.fx.implement()
        (self.fx.project / "surprise.txt").write_text("scope creep\n", encoding="utf-8")
        verify_result = self.fx.runtime.verify()
        self.assertEqual(verify_result["phase"], "VERIFY_FAILED")
        self.assertEqual(verify_result["scope"]["status"], "fail")

        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertFalse(payload["data"]["blockedByIntegrity"])
        self.assertNotEqual(payload["data"]["integrityStatus"], "fail")

    def test_static_ui_and_illegal_action_error(self) -> None:
        with urlopen(self.base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Signoff", html)

        status, payload = self.request("/api/action", method="POST", body={"action": "verify"})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertIn("illegal action", payload["error"])
