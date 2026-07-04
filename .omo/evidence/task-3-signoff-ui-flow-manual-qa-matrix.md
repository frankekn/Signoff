# Todo 3 Manual QA Matrix

Overall verdict: PASS

Scope: Todo 3 of `.omo/plans/signoff-ui-flow.md`, read-only QA plus evidence writes under `.omo/evidence/`.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T3-SE-01 | Red baseline shows old static copy / prompt problem | Playwright browser QA against source UI before Todo 3 change | `node /tmp/signoff-ui-flow-agent-copy-red.mjs` | PASS | A1 |
| T3-SE-02 | DRAFT copied handoff includes mission id, DRAFT, CHARTER.md, SPEC.json, live next action | Playwright browser QA against Vite source UI plus Python RepoFixture API | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A4 |
| T3-SE-03 | Inline note UI appears for note-required action | Playwright browser QA against COUNCIL_REVIEW fixture | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A3, A4 |
| T3-SE-04 | Empty note submit blocked | Playwright browser QA with `/api/action` request monitoring | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A3 |
| T3-SE-05 | Valid note posts `{ action, note }` through existing `/api/action` shape | Playwright browser QA with request payload assertion | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A3 |
| T3-SE-06 | `window.prompt` not called and not present in source path | Browser QA monkeypatch plus source grep | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs`; `rg -n "window.prompt\|Read AGENTS.md. Run ./signoff status" apps/web/src` | PASS | A3, A7 |
| T3-SE-07 | User note treated as JSON data, not HTML/code | Playwright browser QA with prompt-injection-shaped note payload assertion | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A3 |
| T3-SE-08 | Typecheck passed | TypeScript compiler | `npm run typecheck 2>&1 \| tee .omo/evidence/task-3-signoff-ui-flow-typecheck.txt` | PASS | A5 |
| T3-SE-09 | Browser QA rerun evidence exists | DoneClaim plus browser transcript and screenshot | `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` | PASS | A2, A4, A6 |
| T3-SE-10 | Cleanup: no 5173/8765 listeners remain | Local TCP listener inspection | `lsof -i :5173 -i :8765` | PASS | A8 |
| T3-SE-11 | Generated bundle ownership: stale `src/signoff/web_dist/**` is outside Todo 3; Todo 7 rebuild owns packaged assets | Plan/notepad ownership inspection plus diff/grep evidence | `git diff --name-status`; `rg "window.prompt\|Read AGENTS.md. Run ./signoff status" apps/web/src src/signoff/web_dist` | PASS | A7, A9, A10, A11 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T3-AC-01 | Red baseline shows old static copy / prompt problem | Regression baseline | Old source must fail by missing mission/editable paths and calling `window.prompt` | PASS | A1 |
| T3-AC-02 | Empty note submit blocked | Malformed input | Blank note must show inline validation and must not call `/api/action` | PASS | A2, A3 |
| T3-AC-03 | Valid note posts `{ action, note }` through existing `/api/action` shape | API contract preservation | Note-required action must use existing `/api/action` payload shape with action id and note text | PASS | A2, A3 |
| T3-AC-04 | `window.prompt` not called | Forbidden browser primitive | Monkeypatched `window.prompt` must remain uncalled through note-required flow | PASS | A3 |
| T3-AC-05 | `window.prompt` not present in source path | Source regression | `apps/web/src` must not contain `window.prompt` or old static copy string | PASS | A7 |
| T3-AC-06 | User note treated as JSON data, not HTML/code | Prompt injection / HTML injection | Prompt-injection-shaped note must be sent unchanged as JSON data, not evaluated or inserted as HTML | PASS | A2, A3 |
| T3-AC-07 | Browser QA rerun evidence exists | Flake control | Final source-served browser QA rerun must exit 0 and leave transcript/screenshot | PASS | A2, A4, A6 |
| T3-AC-08 | Cleanup: no 5173/8765 listeners remain | Resource cleanup | QA scripts must terminate Vite/API listeners; `lsof` should report no listeners | PASS | A8 |
| T3-AC-09 | Generated bundle ownership | Stale generated artifact boundary | Stale packaged JS must not be claimed as Todo 3 source failure; Todo 7 owns rebuild | PASS | A7, A9, A10, A11 |

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| A1 | transcript | Red baseline proving static handoff copy lacked mission/editable paths and note action called `window.prompt` | `.omo/evidence/task-3-signoff-ui-flow-agent-copy-red.txt` |
| A2 | transcript | Source-served Playwright/browser QA transcript for DRAFT copy and COUNCIL_REVIEW note flow | `.omo/evidence/task-3-signoff-ui-flow-agent-copy.txt` |
| A3 | transcript | No-prompt/inline-note evidence: prompt monkeypatch, empty-note block, valid JSON action payload | `.omo/evidence/task-3-signoff-ui-flow-no-prompt.txt` |
| A4 | screenshot | Browser screenshot from Todo 3 source-served QA | `.omo/evidence/task-3-signoff-ui-flow-agent-copy.png` |
| A5 | command output | TypeScript typecheck transcript | `.omo/evidence/task-3-signoff-ui-flow-typecheck.txt` |
| A6 | doneclaim | Executor DoneClaim listing changed files, QA invocations, rerun, cleanup, and bundle ownership notes | `.omo/evidence/task-3-signoff-ui-flow-doneclaim.txt` |
| A7 | command output | Source-vs-generated grep summary: source clean, generated bundle stale | `.omo/evidence/task-3-signoff-ui-flow-source-vs-webdist.txt` |
| A8 | command output | `lsof -i :5173 -i :8765` cleanup proof, no listeners | `.omo/evidence/task-3-signoff-ui-flow-cleanup-lsof.txt` |
| A9 | command output | `git diff --name-status` showing dirty generated bundle paths under `src/signoff/web_dist/**` | `.omo/evidence/task-3-signoff-ui-flow-git-diff-name-status.txt` |
| A10 | command output | Exact requested combined grep over `apps/web/src src/signoff/web_dist`; matches remain in generated bundle only per A7 | `.omo/evidence/task-3-signoff-ui-flow-rg-source-and-web-dist.txt` |
| A11 | ownership note | Generated-bundle ownership artifact assigning packaged JS staleness to Todo 7 | `.omo/evidence/task-3-signoff-ui-flow-generated-ownership.txt` |

## Notes

- PASS is limited to Todo 3 source-served behavior and the Todo 3 manual QA matrix completeness.
- Packaged generated JS staleness is explicitly not claimed by Todo 3; Todo 7 owns `npm run build:web` and `src/signoff/web_dist/**`.
