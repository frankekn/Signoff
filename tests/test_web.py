from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import signoff
from signoff.web import create_server

from tests.support import RepoFixture


class WebApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RepoFixture()
        static_root = Path(signoff.__file__).resolve().parent / "web_dist"
        self.server = create_server(self.fx.project, host="127.0.0.1", port=0, static_root=static_root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.fx.close()

    def request(self, path: str, *, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_overview_and_artifact_round_trip(self) -> None:
        status, payload = self.request("/api/overview")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"]["phase"], "DRAFT")
        self.assertEqual(payload["data"]["product"], "Signoff")

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

    def test_static_ui_and_illegal_action_error(self) -> None:
        with urlopen(self.base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Signoff", html)

        status, payload = self.request("/api/action", method="POST", body={"action": "verify"})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertIn("illegal action", payload["error"])


if __name__ == "__main__":
    unittest.main()
