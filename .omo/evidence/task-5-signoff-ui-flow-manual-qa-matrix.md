# Task 5 Manual QA Matrix

Post-fix blocker addendum: `.omo/evidence/task-5-signoff-ui-flow-manual-qa-addendum.md`

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| T5-S01 | Todo 5 red-first API proof | unittest API contract | `PYTHONPATH=src python3 -m unittest tests.test_web.WebApiTests.test_proof_summary_reports_unknown_draft_evidence tests.test_web.WebApiTests.test_proof_summary_reports_failed_verification tests.test_web.WebApiTests.test_proof_summary_reviewed_pass_nonfinal_keeps_signoff_unavailable tests.test_web.WebApiTests.test_proof_summary_reviewed_pass_final_exposes_review_gate_hash tests.test_web.WebApiTests.test_proof_summary_done_exposes_final_receipt tests.test_web.WebApiTests.test_inspect_mission_keeps_active_legality_scoped_to_active_mission 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-red.txt` | PASS | A1 |
| T5-S02 | DRAFT proof summary shows UNKNOWN / not yet produced, not green | HTTP API | `python3 .omo/evidence/task-5-signoff-ui-flow-http-probe.py`; section `DRAFT unknown proof` runs `curl -i --silent --show-error <server>/api/overview` | PASS | A2 |
| T5-S03 | VERIFY_FAILED shows failed command id/exit code and no signoff button | browser UI + API | `node /tmp/signoff-ui-flow-proof-qa.mjs 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-browser-rerun.txt` | PASS | A4, A5 |
| T5-S04 | REVIEWED PASS `contract.final=false` keeps signoff unavailable but shows accepted/rework info | HTTP API | `python3 .omo/evidence/task-5-signoff-ui-flow-http-probe.py`; section `REVIEWED PASS nonfinal` runs `curl -i --silent --show-error <server>/api/overview` | PASS | A2, A3 |
| T5-S05 | REVIEWED PASS `contract.final=true` exposes signoff and review gate hash | HTTP API + browser screenshot | `python3 .omo/evidence/task-5-signoff-ui-flow-http-probe.py`; section `REVIEWED PASS final` runs `curl -i --silent --show-error <server>/api/overview`; browser rerun command from T5-S03 | PASS | A2, A3, A6 |
| T5-S06 | DONE shows final receipt hash/path | API proof JSON | `node /tmp/signoff-ui-flow-proof-qa.mjs 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-browser-rerun.txt` | PASS | A3 |
| T5-S07 | historical `inspectMissionId` returns old proof while active actions/legality stay active-scoped | HTTP API | `python3 .omo/evidence/task-5-signoff-ui-flow-http-probe.py`; section `DONE historical proof with active-scoped legality` runs `curl -i --silent --show-error <server>/api/overview?inspectMissionId=<old>` | PASS | A2 |
| T5-S08 | browser proof surface appears before/beside raw artifacts/actions | browser UI screenshot/action log | `node /tmp/signoff-ui-flow-proof-qa.mjs 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-browser-rerun.txt` | PASS | A5, A6 |
| T5-S09 | `python3 scripts/test.py` evidence | repo gate | `python3 scripts/test.py 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-scripts-test-rerun.txt` | PASS | A7 |
| T5-S10 | `npm run typecheck` evidence | repo gate | `npm run typecheck 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-typecheck-rerun.txt` | PASS | A8 |
| T5-S11 | `python3 scripts/check_repo.py` evidence | repo gate | `python3 scripts/check_repo.py 2>&1 \| tee .omo/evidence/task-5-signoff-ui-flow-check-repo-rerun.txt` | PASS | A9 |
| T5-S12 | cleanup: no lingering listeners on 5173/8765 after QA reruns | OS listener check | `lsof -nP -iTCP:5173 -sTCP:LISTEN; lsof -nP -iTCP:8765 -sTCP:LISTEN` | PASS | A10 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| T5-A01 | Todo 5: missing evidence must not appear green | missing proof / false green | DRAFT reports `UNKNOWN` and `not yet produced` for evidence, scope, patch, review gate, and final receipt. | PASS | A2 |
| T5-A02 | Todo 5: failed verification must not expose signoff | failed command / illegal lifecycle action | UI shows `V-001: fail exit 1`; available actions are retry/check-scope only; no `Sign off` button. | PASS | A4, A5 |
| T5-A03 | Todo 5: non-final reviewed pass cannot sign off | contract limit | `contract.final=false` removes `finish_done` while preserving `finish_accepted` and `finish_rework`. | PASS | A2, A3 |
| T5-A04 | Todo 5: final reviewed pass can sign off only with review gate proof | receipt decision surface | `contract.final=true` exposes `finish_done` and a 64-char review gate hash/path. | PASS | A2, A3 |
| T5-A05 | Todo 5: historical inspection must not change active legality | active-vs-inspected trust boundary | Historical DONE proof/receipt is returned, but `status`, `actions`, `editablePaths`, and `next` remain scoped to the active DRAFT mission. | PASS | A2 |
| T5-A06 | Todo 5: malformed/unknown `inspectMissionId` | invalid query input | Unknown mission id returns controlled HTTP 400 JSON error, not a traceback or active proof fallback. | PASS | A2 |

## manualQa.artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | command transcript | Red-first API contract failures before Todo 5 implementation; missing `proofSummary` caused the target tests to error. | `.omo/evidence/task-5-signoff-ui-flow-red.txt` |
| A2 | HTTP transcript | Fresh `curl -i` transcript for DRAFT, unknown `inspectMissionId`, VERIFY_FAILED, REVIEWED nonfinal, REVIEWED final, and historical inspect scenarios. | `.omo/evidence/task-5-signoff-ui-flow-http.txt` |
| A3 | browser/API JSON | Browser QA extracted proof summaries for REVIEWED nonfinal, REVIEWED final, and DONE. | `.omo/evidence/task-5-signoff-ui-flow-proof.json` |
| A4 | browser transcript | VERIFY_FAILED browser text: failed command id/exit code present and `buttonsHaveSignoff=false`. | `.omo/evidence/task-5-signoff-ui-flow-verify-failed.txt` |
| A5 | browser run transcript | Browser QA command log and PASS result. | `.omo/evidence/task-5-signoff-ui-flow-browser-rerun.txt` |
| A6 | screenshot | Proof card screenshot from a real browser run; readable proof appears above the action/workspace record area. | `.omo/evidence/task-5-signoff-ui-flow-proof.png` |
| A7 | command transcript | Full repo `scripts/test.py` rerun: 35/35 conformance/web tests passed. | `.omo/evidence/task-5-signoff-ui-flow-scripts-test-rerun.txt` |
| A8 | command transcript | `npm run typecheck` rerun. | `.omo/evidence/task-5-signoff-ui-flow-typecheck-rerun.txt` |
| A9 | command transcript | `python3 scripts/check_repo.py` rerun. | `.omo/evidence/task-5-signoff-ui-flow-check-repo-rerun.txt` |
| A10 | OS transcript | Explicit cleanup listener check for 5173/8765 after QA reruns. | `.omo/evidence/task-5-signoff-ui-flow-cleanup-listeners.txt` |

## Notes

- No product source files were edited during this QA pass.
- The unknown `inspectMissionId` adversarial case is covered and passed with controlled HTTP 400.
