# Todo 6 Manual QA Matrix

Plan: `.omo/plans/signoff-ui-flow.md` Todo 6, "Prevent dirty artifact loss across artifact and mission switches".

DoneClaim under review: `.omo/evidence/task-6-signoff-ui-flow-doneclaim.txt`.

Post-fix addendum for the previous `Artifacts -> Timeline -> Artifacts` blocker: `.omo/evidence/task-6-signoff-ui-flow-manual-qa-addendum.md`.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-SE-001 | failure scenario: pre-fix dirty artifact switch loses draft | Preserved browser QA transcript from pre-fix run | `node /tmp/signoff-ui-flow-editor-qa.mjs --expect-red` | PASS | A1 |
| T6-SE-002 | dirty artifact switch blocked with inline warning and current draft remains visible | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | A2, A3 |
| T6-SE-003 | dirty mission switch blocked with inline warning and current mission remains selected | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | A2, A3 |
| T6-SE-004 | Save then artifact switch works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | A2, A3 |
| T6-SE-005 | Discard then mission switch works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | A2, A3 |
| T6-SE-006 | no `window.confirm` / no autosave | Source and generated UI bundle text | `rg -n "window\\.confirm|\\bconfirm\\(|auto.?save|autosave" apps/web/src src/signoff/web_dist || true` | PASS | A6 |
| T6-SE-007 | `npm run typecheck` evidence | Terminal command | `npm run typecheck 2>&1 \| tee .omo/evidence/task-6-signoff-ui-flow-typecheck.txt` | PASS | A4 |
| T6-SE-008 | `python3 scripts/test.py` evidence | Terminal command | `python3 scripts/test.py 2>&1 \| tee .omo/evidence/task-6-signoff-ui-flow-api.txt` | PASS | A5 |
| T6-SE-009 | cleanup/listener evidence | OS TCP listeners | `lsof -nP -iTCP:5174 -sTCP:LISTEN || true; lsof -nP -iTCP:5173 -sTCP:LISTEN || true; lsof -nP -iTCP:8765 -sTCP:LISTEN || true` | PASS | A7 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-ADV-001 | dirty artifact switch must not lose unsaved draft | stale state | Switching artifacts while `CHARTER.md` has a local unsaved draft keeps `CHARTER.md` selected, leaves the marker visible, and shows inline warning text. | PASS | A2, A3 |
| T6-ADV-002 | dirty mission switch must not lose unsaved draft | stale state | Selecting a different mission while the artifact editor is dirty keeps the active mission selected and leaves the draft marker visible. | PASS | A2, A3 |
| T6-ADV-003 | explicit Save remains the only write path | dirty worktree | After explicit `Save changes`, artifact switching works and the toolbar reports `Saved`; no implicit write is needed to unblock. | PASS | A2, A3 |
| T6-ADV-004 | explicit Discard must unblock without preserving dirty draft | dirty worktree | After `Discard draft`, mission switching works and dirty warning is detached. | PASS | A2, A3 |
| T6-ADV-005 | no browser modal or autosave fallback | misleading success output | Text search finds no `window.confirm`, bare `confirm(`, `autosave`, or `auto-save` marker in source or packaged UI text; browser proof still passes via inline warning and explicit Save/Discard. | PASS | A2, A6 |
| T6-ADV-006 | QA cleanup must not leave long-running local servers | hung or long commands | Vite/API QA processes exit and no listeners remain on 5174, 5173, or 8765. | PASS | A7 |
| T6-ADV-007 | generated bundle dirt must not be claimed by Todo 6 | dirty worktree | Current generated bundle dirt is recorded as Todo 7-owned, not Todo 6-owned. | PASS | A8, A9 |

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| A1 | transcript | Preserved red repro showing `TASK-6-UNSAVED-DRAFT-MARKER` absent after pre-fix `SPEC.json` click; result `RED_CONFIRMED`. | `.omo/evidence/task-6-signoff-ui-flow-editor-red.txt` |
| A2 | transcript | Current browser QA rerun with `artifactSwitchBlocked=true`, `missionSwitchBlocked=true`, `switchAfterSave=true`, `switchMissionAfterDiscard=true`, and `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-editor.txt` |
| A3 | screenshot | Current browser UI screenshot from the passing editor QA run. | `.omo/evidence/task-6-signoff-ui-flow-editor.png` |
| A4 | terminal log | Current `npm run typecheck` output; exit 0. | `.omo/evidence/task-6-signoff-ui-flow-typecheck.txt` |
| A5 | terminal log | Current `python3 scripts/test.py` output; 35/35 passed. | `.omo/evidence/task-6-signoff-ui-flow-api.txt` |
| A6 | terminal log | Source/generated text probe for `window.confirm`, `confirm(`, `autosave`, and `auto-save`; no matches. | `.omo/evidence/task-6-signoff-ui-flow-no-confirm-autosave.txt` |
| A7 | terminal log | Listener cleanup proof for 5174, 5173, and 8765; no listener rows. | `.omo/evidence/task-6-signoff-ui-flow-listeners.txt` |
| A8 | terminal log | Generated bundle git status and file listing used for ownership classification. | `.omo/evidence/task-6-signoff-ui-flow-generated-status.txt` |
| A9 | ownership report | Generated bundle ownership decision for `src/signoff/web_dist/` and `apps/web/dist/`. | `.omo/evidence/task-6-signoff-ui-flow-generated-ownership.txt` |

## Verdict

PASS. No blockers found in the requested Todo 6 QA/report scope.
