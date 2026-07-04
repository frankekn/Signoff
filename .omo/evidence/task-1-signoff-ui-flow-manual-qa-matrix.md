# Todo 1 Manual QA Matrix

Verdict: PASS

Plan: `.omo/plans/signoff-ui-flow.md` Todo 1, "Fix server-owned legality for hard integrity and restartable phases".

Surface: Signoff local HTTP API served by `signoff.web.create_server()` against disposable `tests.support.RepoFixture` repos.

Primary invocation: `PYTHONPATH=src python3 - <<'PY' ...` in `/Users/termtek/Github/Signoff`; the script issued real `curl -i -sS` requests and wrote artifact `A1`.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T1-S01 | Todo 1 AC: STOPPED overview `canStartMission=true` | HTTP `GET /api/overview` | `curl -i -sS http://127.0.0.1:51953/api/overview` | PASS | A1 lines 1-11 |
| T1-S02 | Todo 1 AC: DONE overview `canStartMission=true` | HTTP `GET /api/overview` | `curl -i -sS http://127.0.0.1:51955/api/overview` | PASS | A1 lines 13-23 |
| T1-S03 | Todo 1 AC: PIVOT overview `canStartMission=false` | HTTP `GET /api/overview` | `curl -i -sS http://127.0.0.1:51957/api/overview` | PASS | A1 lines 25-35 |
| T1-S04 | Todo 1 AC: BLOCKED overview `canStartMission=false` | HTTP `GET /api/overview` | `curl -i -sS http://127.0.0.1:51961/api/overview` | PASS | A1 lines 49-59 |
| T1-S05 | Todo 1 AC: `POST /api/missions` rejects active PIVOT/BLOCKED with controlled 400 | HTTP `POST /api/missions` | `curl -i -sS -X POST http://127.0.0.1:51957/api/missions -H Content-Type: application/json --data {\"goal\":\"Start after pivot\"}` and `curl -i -sS -X POST http://127.0.0.1:51961/api/missions -H Content-Type: application/json --data {\"goal\":\"Start after blocked\"}` | PASS | A1 lines 37-47, A1 lines 61-71 |
| T1-S06 | Todo 1 AC: hard integrity failure returns `blockedByIntegrity=true`, `integrityStatus=fail`, no actions, repair-oriented next text | HTTP `GET /api/overview` after locked `SPEC.json` tamper | `curl -i -sS http://127.0.0.1:51964/api/overview` | PASS | A1 lines 73-83 |
| T1-S07 | Todo 1 AC: VERIFY_FAILED nested `scope.status=fail` does not set `blockedByIntegrity=true` | Runtime fixture setup plus HTTP `GET /api/overview` | `RepoFixture.lock(); activate(); implement(); write surprise.txt; runtime.verify()` then `curl -i -sS http://127.0.0.1:51966/api/overview` | PASS | A1 lines 85-135 |
| T1-S08 | Todo 1 AC: malformed input returns controlled 400 | HTTP `POST /api/missions` with non-object JSON | `curl -i -sS -X POST http://127.0.0.1:51968/api/missions -H Content-Type: application/json --data \"not an object\"` | PASS | A1 lines 137-147 |
| T1-S09 | Todo 1 QA gate: focused and full API tests pass | CLI/API test runner | `python3 scripts/test.py 2>&1 | tee .omo/evidence/task-1-signoff-ui-flow-api.txt` | PASS | A4 lines 23-49 |
| T1-S10 | Todo 1 QA gate: TypeScript API shape check passes | CLI typecheck | `npm run typecheck 2>&1 | tee .omo/evidence/task-1-signoff-ui-flow-typecheck.txt` | PASS | A5 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T1-A01 | Todo 1 AC: hard integrity failure blocks actions | Trust-boundary/integrity tamper | Top-level `status.integrity.status == fail` must block all advancing actions and direct repair/inspection. | PASS | A1 lines 73-83 |
| T1-A02 | Todo 1 AC: failed scope is not hard integrity corruption | Integrity false positive | Nested `scope.status=fail` under VERIFY_FAILED remains actionable, with `blockedByIntegrity=false` and `integrityStatus=pass`. | PASS | A1 lines 85-135 |
| T1-A03 | Todo 1 AC: PIVOT/BLOCKED cannot use normal mission start | Invalid lifecycle transition | Active PIVOT and BLOCKED reject normal `POST /api/missions` with controlled 400 JSON. | PASS | A1 lines 37-47, A1 lines 61-71 |
| T1-A04 | Todo 1 AC: malformed input controlled 400 | Malformed HTTP body | Non-object JSON returns `400 Bad Request` and `{\"ok\": false, \"error\": \"request body must be a JSON object\"}`. | PASS | A1 lines 137-147 |
| T1-A05 | Scope guard: generated bundle ownership | Dirty/generated ownership | Current `src/signoff/web_dist/**` changes are not Todo 1 scope and must wait for Todo 7 rebuild ownership. | PASS | A2 lines 22-38 |
| T1-A06 | Cleanup receipt | Process hygiene | No QA harness/server process remains after probe command exits. | PASS | A1 lines 194-201, A3 lines 1-4 |

## Dirty / Generated Ownership

Current generated bundle changes under `src/signoff/web_dist/**` are dirty, but they are not claimed by Todo 1. Todo 1 scope from `.omo/start-work/notepad.md` is `src/signoff/runtime.py`, `src/signoff/web.py`, `tests/test_web.py`, and `apps/web/src/api.ts`. Generated `src/signoff/web_dist/**` changes must wait for Todo 7 and the explicit `npm run build:web` ownership gate.

Evidence: A2 lines 22-38.

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| A1 | HTTP transcript | Real `curl -i` probes for STOPPED, DONE, PIVOT, BLOCKED, start rejection, integrity failure, VERIFY_FAILED scope failure, malformed input, and cleanup thread receipt. | `.omo/evidence/task-1-signoff-ui-flow-manual-qa-probe.txt` |
| A2 | Dirty-scope receipt | `git status --short`, scoped Todo 1 file list, generated `src/signoff/web_dist/**` dirty names, and ownership verdict. | `.omo/evidence/task-1-signoff-ui-flow-dirty-scope.txt` |
| A3 | Process cleanup receipt | `pgrep` check showing no remaining QA harness/server process. | `.omo/evidence/task-1-signoff-ui-flow-cleanup.txt` |
| A4 | Full test evidence | `python3 scripts/test.py` output showing Todo 1 web tests and full conformance run passed. | `.omo/evidence/task-1-signoff-ui-flow-api.txt` |
| A5 | Typecheck evidence | `npm run typecheck` output for the web workspace. | `.omo/evidence/task-1-signoff-ui-flow-typecheck.txt` |
