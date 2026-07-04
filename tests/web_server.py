from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import signoff
from signoff.util import atomic_write_json, read_json
from signoff.web import create_server
from signoff.web_proof import JsonObject

from tests.support import RepoFixture


class WebServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RepoFixture()
        self._start_server()

    def tearDown(self) -> None:
        self._stop_server()
        self.fx.close()

    def restart_fixture(self) -> None:
        self._stop_server()
        self.fx.close()
        self.fx = RepoFixture()
        self._start_server()

    def conclude_from_push(self, verdict: str) -> None:
        self.fx.valid_draft()
        self.fx.valid_push()
        push = read_json(self.fx.mission / "PUSH.json")
        push["decision"]["verdict"] = verdict
        if verdict == "INSUFFICIENT_QUORUM":
            push["advisors"] = push["advisors"][:1]
        atomic_write_json(self.fx.mission / "PUSH.json", push)
        self.fx.runtime.lock()

    def request(self, path: str, *, method: str = "GET", body: JsonObject | None = None) -> tuple[int, JsonObject]:
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
            with exc:
                return exc.code, json.loads(exc.read().decode("utf-8"))

    def _start_server(self) -> None:
        static_root = Path(signoff.__file__).resolve().parent / "web_dist"
        self.server = create_server(self.fx.project, host="127.0.0.1", port=0, static_root=static_root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.base = f"http://{host}:{port}"

    def _stop_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
