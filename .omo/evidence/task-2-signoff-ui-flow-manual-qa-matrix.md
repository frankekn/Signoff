# manualQa

Scope: `.omo/plans/signoff-ui-flow.md` Todo 2, phase rail and hero state truthfulness.

Overall verdict: PASS. All required rows have non-empty evidence artifacts. The original `.omo/evidence/task-2-signoff-ui-flow-diff-check.txt` is zero bytes, so this matrix cites the non-empty rerun artifact instead.

## surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| T2-S1 | VERIFY_FAILED renders as failed evidence, not completed build | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S2 | COUNCIL_REVIEW renders as paused review, not normal Council progress | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S3 | STOPPED renders terminal/stopped and does not mark Sign off active/complete | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S4 | BLOCKED renders blocked and does not mark Sign off active/complete | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S5 | PIVOT renders pivot and does not mark Sign off active/complete | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S6 | REVIEWED renders review decision pending, not signed off | Browser UI via Playwright against Vite + Signoff API fixture | `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` | PASS | A1, A2 |
| T2-S7 | Typecheck passed | TypeScript compiler | `npm run typecheck 2>&1 \| tee .omo/evidence/task-2-signoff-ui-flow-typecheck.txt` | PASS | A3 |
| T2-S8 | Browser QA rerun evidence exists | Shell evidence check | `find .omo/evidence -maxdepth 1 -type f ... -exec wc -c {} \;` and `file .omo/evidence/task-2-signoff-ui-flow-phase-rail.png` | PASS | A1, A2, A4 |
| T2-S9 | Cleanup: no 8765/5173 listeners remain | Local TCP listener check | `lsof -nP -iTCP:8765 -sTCP:LISTEN; lsof -nP -iTCP:5173 -sTCP:LISTEN` | PASS | A5 |
| T2-S10 | Generated bundle ownership is outside Todo 2 and waits for Todo 7 | Git working tree + plan/notepad inspection | `git status --short --ignored --untracked-files=all -- src/signoff/web_dist apps/web/dist` plus plan/notepad line inspection | PASS | A6 |
| T2-S11 | Diff check passed | Git whitespace check | `git diff --check` | PASS | A7 |

## adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| T2-A1 | VERIFY_FAILED must not look like completed build | Failed verification state alias regression | Rail shows `Failed evidence` with failed tone; Build may be complete, but the current failed evidence step is active | PASS | A1, A2, A8 |
| T2-A2 | COUNCIL_REVIEW must not look like normal Council progress | Review pause alias regression | Rail shows `Paused review`; Sign off remains neither active nor complete | PASS | A1, A2 |
| T2-A3 | STOPPED/BLOCKED/PIVOT must not complete Sign off | Terminal-state false-positive signoff | Rail labels the terminal outcome and does not show `Sign off` as active/complete | PASS | A1, A2 |
| T2-A4 | REVIEWED must not be treated as signed off | Pre-signoff review state confusion | Rail shows `Decision pending`, not signed off | PASS | A1, A2 |
| T2-A5 | Browser QA process cleanup | Stray dev/API server | Ports 8765 and 5173 have no LISTEN process after QA | PASS | A5 |
| T2-A6 | Generated bundle scope bleed | Todo ownership breach | Generated `src/signoff/web_dist/**` and ignored `apps/web/dist/**` changes are identified but unclaimed by Todo 2; Todo 7 owns rebuild/commit | PASS | A6 |

## artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | transcript | Playwright phase rail rerun transcript with PASS rows for VERIFY_FAILED, COUNCIL_REVIEW, STOPPED, BLOCKED, PIVOT, REVIEWED | `.omo/evidence/task-2-signoff-ui-flow-phase-rail.txt` |
| A2 | screenshot | Browser screenshot from phase rail QA rerun, PNG 1280x1517, sha256 `171d256e26e14584a89660d94c82b0e550c547a08240024e3e192768d1cfa322` | `.omo/evidence/task-2-signoff-ui-flow-phase-rail.png` |
| A3 | transcript | TypeScript typecheck transcript with `tsc -b --pretty false` and no errors | `.omo/evidence/task-2-signoff-ui-flow-typecheck.txt` |
| A4 | transcript | Browser QA rerun summary pointing to transcript and screenshot | `.omo/evidence/task-2-signoff-ui-flow-phase-rail-rerun.txt` |
| A5 | transcript | Listener cleanup evidence: `lsof` exits 1 for both 8765 and 5173, meaning no listeners | `.omo/evidence/task-2-signoff-ui-flow-listeners.txt` |
| A6 | transcript | Generated bundle ownership proof tying current generated dirtiness to Todo 7 scope | `.omo/evidence/task-2-signoff-ui-flow-generated-ownership.txt` |
| A7 | transcript | Non-empty rerun of `git diff --check`, exit_code=0 | `.omo/evidence/task-2-signoff-ui-flow-diff-check-rerun.txt` |
| A8 | transcript | Original red evidence: pre-fix VERIFY_FAILED rail missed `Failed evidence` | `.omo/evidence/task-2-signoff-ui-flow-phase-rail-red.txt` |
| A9 | transcript | Dirty scope note inspected during QA; generated bundle changes listed | `.omo/evidence/task-2-signoff-ui-flow-dirty-scope.txt` |
