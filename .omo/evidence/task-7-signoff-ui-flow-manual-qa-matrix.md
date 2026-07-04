# Todo 7 Manual QA Matrix

DoneClaim: Todo 7 - Rebuild packaged UI and run final real-surface verification.

Verdict: PASS. No blockers found for Todo 7 QA/release-surface criteria.

## surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| S1 | Todo 7 acceptance: typecheck exits 0 | CLI | `npm run typecheck 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-typecheck.txt` | PASS | AR1 |
| S2 | Todo 7 acceptance: build exits 0 and copy step runs | CLI | `npm run build:web 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-build.txt` | PASS | AR2 |
| S3 | Todo 7 acceptance: conformance tests exit 0 | CLI | `python3 scripts/test.py 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-tests.txt` | PASS | AR3 |
| S4 | Todo 7 acceptance: repo check exits 0 | CLI | `python3 scripts/check_repo.py 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-check.txt` | PASS | AR4 |
| S5 | Todo 7 failure scenario: diff whitespace/assets gate | CLI | `git diff --check 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-diff-check.txt` | PASS | AR5 |
| S6 | Todo 7 failure scenario: generated asset refs exist in both generated roots | CLI data audit | `node <<'NODE' ... refs/existence audit ... NODE \| tee .omo/evidence/task-7-signoff-ui-flow-generated-status.txt` | PASS | AR6 |
| S7 | Todo 7 QA: packaged browser QA used packaged assets | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR8 |
| S8 | Todo 7 acceptance: packaged UI loads with no console/page errors | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S9 | Todo 7 QA: start mission and edit draft | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR8 |
| S10 | Todo 6 carried into Todo 7: dirty artifact switch blocked | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR8 |
| S11 | Todo 6 carried into Todo 7: dirty tab switch blocked | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S12 | Todo 6 carried into Todo 7: save then switch works | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S13 | Todo 3 carried into Todo 7: agent handoff copy includes live mission/context | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S14 | Todo 4 carried into Todo 7: old mission read-only and active actions preserved | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S15 | Todo 5 carried into Todo 7: VERIFY_FAILED surface visible | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S16 | Todo 5 carried into Todo 7: REVIEWED proof/signoff visible | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR8 |
| S17 | Todo 7 acceptance: DONE proof plus start-next-mission visible | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR8 |
| S18 | Todo 7 acceptance: keyboard focus reaches controls | Browser via Playwright | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7 |
| S19 | Todo 7 QA cleanup: listener cleanup | OS listener audit from Playwright script | `node /tmp/signoff-ui-flow-final-qa.mjs` | PASS | AR7, AR9 |

## adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| A1 | Todo 7 failure scenario | Missing generated asset reference | Every `/assets/...` reference in `apps/web/dist/index.html` and `src/signoff/web_dist/index.html` resolves to an existing file. | PASS | AR6 |
| A2 | Todo 7 packaged browser QA | Wrong static root | Browser QA must load `staticRoot=/Users/termtek/Github/Signoff/src/signoff/web_dist`, not the source dev server. | PASS | AR7 |
| A3 | Todo 7 acceptance | Browser runtime error | Console errors and page errors must remain empty during packaged UI flow. | PASS | AR7 |
| A4 | Todo 6 carried into final QA | Dirty artifact switch data loss | Attempting to switch artifacts while draft is dirty must be blocked by an inline warning. | PASS | AR7, AR8 |
| A5 | Todo 6 carried into final QA | Dirty tab/mission switch data loss | Attempting to switch tabs/missions while draft is dirty must be blocked until save/discard. | PASS | AR7 |
| A6 | Todo 4 carried into final QA | Historical mission mutation/confused legality | Old mission artifacts must be read-only while active mission actions remain preserved. | PASS | AR7 |
| A7 | Todo 5 carried into final QA | Failed verification mislabeled green | VERIFY_FAILED proof must remain visible as failed, not completed/signed off. | PASS | AR7 |
| A8 | Todo 7 cleanup | Leaked packaged QA listeners | Every QA port used by the scenario must have no listener after cleanup. | PASS | AR9 |

## artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| AR1 | CLI transcript | `npm run typecheck` rerun; exits 0 and includes `result: PASS`. | `.omo/evidence/task-7-signoff-ui-flow-typecheck.txt` |
| AR2 | CLI transcript | `npm run build:web` rerun; Vite build succeeded and `scripts/copy_web_dist.py` copied `apps/web/dist -> src/signoff/web_dist`. | `.omo/evidence/task-7-signoff-ui-flow-build.txt` |
| AR3 | CLI transcript | `python3 scripts/test.py` rerun; 35/35 conformance/web tests passed. | `.omo/evidence/task-7-signoff-ui-flow-tests.txt` |
| AR4 | CLI transcript | `python3 scripts/check_repo.py` rerun; repository check passed. | `.omo/evidence/task-7-signoff-ui-flow-check.txt` |
| AR5 | CLI transcript | `git diff --check` rerun; no whitespace errors and PASS marker recorded. | `.omo/evidence/task-7-signoff-ui-flow-diff-check.txt` |
| AR6 | Data audit transcript | Generated HTML asset reference audit for `apps/web/dist` and `src/signoff/web_dist`. | `.omo/evidence/task-7-signoff-ui-flow-generated-status.txt` |
| AR7 | Browser action log | Final packaged Playwright QA transcript with static root, binary observables, focus sequence, console/page errors, and result. | `.omo/evidence/task-7-signoff-ui-flow-final.txt` |
| AR8 | Browser screenshot | Final packaged UI screenshot from the Playwright QA scenario. | `.omo/evidence/task-7-signoff-ui-flow-final.png` |
| AR9 | OS listener audit | QA ports reported with no listener after cleanup. | `.omo/evidence/task-7-signoff-ui-flow-listeners.txt` |
| AR10 | Prior DoneClaim | Existing Todo 7 DoneClaim read before this QA report. | `.omo/evidence/task-7-signoff-ui-flow-doneclaim.txt` |
