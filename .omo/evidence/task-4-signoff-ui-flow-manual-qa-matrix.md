# manualQa: Todo 4 Mission History Selection

Scope: QA/report artifacts only. Product source was not edited during this pass.

## surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| S1 | Todo 4 red-first API proof existed before fix | unittest/API transcript | prior red proof: `cat .omo/evidence/task-4-signoff-ui-flow-red.txt` | PASS | A1 |
| S2 | Overview lists active/stopped/next missions | API unittest | `PYTHONPATH=src python3 -m unittest tests.test_web.WebApiTests.test_overview_lists_stopped_and_next_mission tests.test_web.WebApiTests.test_inactive_mission_artifacts_are_read_only` | PASS | A2 |
| S3 | Inactive mission artifacts are read-only by API | API unittest | `PYTHONPATH=src python3 -m unittest tests.test_web.WebApiTests.test_overview_lists_stopped_and_next_mission tests.test_web.WebApiTests.test_inactive_mission_artifacts_are_read_only` | PASS | A2 |
| S4 | Browser mission selector defaults active | browser UI | `node /tmp/signoff-ui-flow-missions-qa.mjs` | PASS | A3, A4, A5 |
| S5 | Selecting old mission changes artifacts/timeline only | browser UI | `node /tmp/signoff-ui-flow-missions-qa.mjs` | PASS | A3, A4, A5 |
| S6 | Active actions remain scoped to active mission | browser UI | `node /tmp/signoff-ui-flow-missions-qa.mjs` | PASS | A3, A4, A5 |
| S7 | Historical artifact PUT returns controlled 400 | HTTP API | `curl -i -X PUT -H 'Content-Type: application/json' --data '{"path":"<old mission CHARTER.md>","content":"historical overwrite attempt"}' http://127.0.0.1:8765/api/artifact` | PASS | A6 |
| S8 | No `proofSummary` / `inspectMissionId` implementation in Todo 4 | source grep | `rg -n "proofSummary\|inspectMissionId" src/signoff apps/web tests` | PASS | A7 |
| S9 | `python3 scripts/test.py` evidence | repo test gate | `python3 scripts/test.py` | PASS | A8 |
| S10 | `npm run typecheck` evidence | TypeScript gate | `npm run typecheck` | PASS | A9 |
| S11 | Cleanup: no lingering listeners on 5173/8765 after servers | OS port check | `lsof -nP -iTCP:5173 -iTCP:8765 -sTCP:LISTEN` | PASS | A10, A11 |

## adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| ADV1 | Todo 4 red-first API proof | regression-first proof | Pre-fix evidence shows the historical read-only API test failed before the fix. | PASS | A1 |
| ADV2 | Inactive artifacts read-only | stale/historical state | Old mission artifacts stay non-editable even if that old mission state is made `DRAFT`. | PASS | A2 |
| ADV3 | Historical artifact PUT controlled 400 | invalid lifecycle edit | PUT to an old mission artifact returns a controlled HTTP 400 JSON error, not a write or crash. | PASS | A6 |
| ADV4 | Unknown mission | malformed input | Requesting a missing mission returns controlled HTTP 400 JSON. | PASS | A3 |
| ADV5 | Invalid artifact path | path traversal / invalid artifact | Requesting `../STATE.json` returns controlled HTTP 400 JSON. | PASS | A3 |
| ADV6 | Selection scope | state confusion | Selecting a historical mission changes artifact/timeline inspection only; action buttons remain active-mission actions. | PASS | A3, A4, A5 |
| ADV7 | Todo 5 bleed-through | contract ownership | Todo 4 source/tests do not implement `proofSummary` or `inspectMissionId`. | PASS | A7 |
| ADV8 | QA server cleanup | hung process / leaked listener | Ports 5173 and 8765 have no listeners after browser QA cleanup. | PASS | A10, A11 |

## artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | text | Red-first unittest transcript showing `test_inactive_mission_artifacts_are_read_only` failed before the fix. | `.omo/evidence/task-4-signoff-ui-flow-red.txt` |
| A2 | text | Fresh focused API unittest rerun for mission overview and inactive read-only artifacts. | `.omo/evidence/task-4-signoff-ui-flow-focused-api-rerun.txt` |
| A3 | text | Fresh browser UI transcript with selector, old mission, active action, malformed input, and PUT assertions. | `.omo/evidence/task-4-signoff-ui-flow-missions.txt` |
| A4 | png | Fresh browser screenshot for Todo 4 mission selector QA. | `.omo/evidence/task-4-signoff-ui-flow-missions.png` |
| A5 | text | Browser QA process transcript showing Vite invocation and PASS from the Playwright script. | `.omo/evidence/task-4-signoff-ui-flow-browser-rerun.txt` |
| A6 | text | `curl -i` transcript for historical artifact PUT returning controlled HTTP 400 JSON. | `.omo/evidence/task-4-signoff-ui-flow-old-readonly.txt` |
| A7 | text | Source grep proving no Todo 5 `proofSummary` / `inspectMissionId` implementation in Todo 4 source/tests. | `.omo/evidence/task-4-signoff-ui-flow-no-todo5-rg.txt` |
| A8 | text | Fresh full repo test transcript from `python3 scripts/test.py`. | `.omo/evidence/task-4-signoff-ui-flow-scripts-test-rerun.txt` |
| A9 | text | Fresh TypeScript typecheck transcript from `npm run typecheck`. | `.omo/evidence/task-4-signoff-ui-flow-typecheck-rerun.txt` |
| A10 | text | Pre-QA listener check for ports 5173 and 8765. | `.omo/evidence/task-4-signoff-ui-flow-listeners-before-nonempty.txt` |
| A11 | text | Post-QA listener check for ports 5173 and 8765 showing no listeners. | `.omo/evidence/task-4-signoff-ui-flow-cleanup-listeners.txt` |
