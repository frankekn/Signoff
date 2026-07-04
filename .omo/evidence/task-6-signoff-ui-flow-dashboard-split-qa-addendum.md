# Todo 6 QA Addendum: Dashboard Component Extraction

Plan: `.omo/plans/signoff-ui-flow.md` Todo 6, "Prevent dirty artifact loss across artifact and mission switches".

DoneClaim under review: `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-doneclaim.txt`.

Scope: QA/report artifacts only. No product source was edited.

Verdict: PASS.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-DS-SE-001 | Dashboard split did not regress dirty artifact switch blocking | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | DS-A1, DS-A2 |
| T6-DS-SE-002 | Dashboard split did not regress dirty mission switch blocking | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | DS-A1, DS-A2 |
| T6-DS-SE-003 | Dirty `Artifacts -> Timeline` tab switch blocks, draft marker preserved, Timeline not shown, warning appears | Browser UI at `http://127.0.0.1:5175/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-tab-switch-qa.mjs` | PASS | DS-A3, DS-A4 |
| T6-DS-SE-004 | Save then artifact switch works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | DS-A1, DS-A2 |
| T6-DS-SE-005 | Discard then mission switch works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | DS-A1, DS-A2 |
| T6-DS-SE-006 | Typecheck/test/diff-check artifacts exist and PASS | Terminal commands | `npm run typecheck`; `python3 scripts/test.py`; `git diff --check -- apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/StartMissionCard.tsx` | PASS | DS-A5, DS-A6, DS-A7, DS-A8 |
| T6-DS-SE-007 | Generated ownership unchanged and still Todo 7-owned | Git status plus ownership report | `git status --short -- src/signoff/web_dist apps/web/dist`; `find apps/web/dist src/signoff/web_dist -maxdepth 2 -type f -print \| sort` | PASS | DS-A9, DS-A10 |
| T6-DS-SE-008 | Listener cleanup after reruns | OS TCP listeners | `lsof -nP -iTCP:5174 -sTCP:LISTEN; lsof -nP -iTCP:5175 -sTCP:LISTEN; lsof -nP -iTCP:8765 -sTCP:LISTEN` | PASS | DS-A11 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-DS-ADV-001 | dirty artifact switch must not lose unsaved draft after extraction | stale state | Clicking `SPEC.json` while `CHARTER.md` is dirty keeps the current artifact selected and shows the inline warning. | PASS | DS-A1, DS-A2 |
| T6-DS-ADV-002 | dirty mission switch must not lose unsaved draft after extraction | stale state | Selecting another mission while dirty keeps the current mission selected and preserves the dirty editor state. | PASS | DS-A1, DS-A2 |
| T6-DS-ADV-003 | dirty tab switch must not unmount the editor | stale state | Clicking `Timeline` while dirty keeps `Artifacts` visible, preserves `TASK-6-TAB-SWITCH-DRAFT-MARKER`, and shows one warning. | PASS | DS-A3, DS-A4 |
| T6-DS-ADV-004 | explicit Save remains the only write path before artifact switching | dirty worktree | After `Save changes`, the toolbar reports `Saved` and artifact switching works. | PASS | DS-A1, DS-A2 |
| T6-DS-ADV-005 | explicit Discard remains the mission-switch unblock path | dirty worktree | After `Discard draft`, mission switching works without autosave or silent draft preservation. | PASS | DS-A1, DS-A2 |
| T6-DS-ADV-006 | extracted Dashboard files keep repo gates green | regression through component extraction | TypeScript typecheck, Python API/conformance tests, and scoped diff whitespace check all pass on the current checkout. | PASS | DS-A5 |
| T6-DS-ADV-007 | generated bundle dirt must not be claimed by Dashboard split | generated ownership | Generated bundle changes remain classified as Todo 7-owned; this addendum did not rebuild or edit generated assets. | PASS | DS-A9, DS-A10 |
| T6-DS-ADV-008 | QA reruns must not leave local servers | hung or long commands | No listeners remain on QA ports 5174, 5175, or 8765 after browser reruns. | PASS | DS-A11 |

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| DS-A1 | browser transcript | Fresh editor QA after this addendum request: `artifactSwitchBlocked=true`, `missionSwitchBlocked=true`, `tabSwitchBlocked=true`, `switchAfterSave=true`, `switchMissionAfterDiscard=true`, `savedAfterClick=true`, `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-editor.txt` |
| DS-A2 | browser screenshot | Fresh editor QA screenshot from `node /tmp/signoff-ui-flow-editor-qa.mjs`. | `.omo/evidence/task-6-signoff-ui-flow-editor.png` |
| DS-A3 | browser transcript | Fresh tab-switch QA after this addendum request: `tabSwitchPreservedDraft=true`, `timelineVisibleAfterClick=false`, `warningCountAfterTimelineClick=1`, marker `TASK-6-TAB-SWITCH-DRAFT-MARKER`, `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt` |
| DS-A4 | browser screenshot | Fresh tab-switch QA screenshot from `node /tmp/signoff-ui-flow-tab-switch-qa.mjs`. | `.omo/evidence/task-6-signoff-ui-flow-tab-switch.png` |
| DS-A5 | terminal log | Fresh addendum gate confirmation: `npm run typecheck`, `python3 scripts/test.py`, and scoped `git diff --check` all report PASS. | `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-addendum-gates.txt` |
| DS-A6 | terminal log | Existing Dashboard split typecheck artifact from the DoneClaim; non-empty and current command output. | `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-typecheck.txt` |
| DS-A7 | terminal log | Existing Dashboard split API/conformance artifact from the DoneClaim; `Ran 35 tests`, `OK`, `Conformance: 35/35 passed`. | `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-api.txt` |
| DS-A8 | terminal log | Existing Dashboard split scoped diff-check artifact; `PASS git diff --check found no whitespace errors`. | `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-diff-check.txt` |
| DS-A9 | ownership report | Existing generated bundle ownership decision: generated `src/signoff/web_dist/` and `apps/web/dist/` dirt is Todo 7-owned, not Todo 6-owned. | `.omo/evidence/task-6-signoff-ui-flow-generated-ownership.txt` |
| DS-A10 | terminal log | Existing generated bundle git status and file listing used to confirm current generated ownership state. | `.omo/evidence/task-6-signoff-ui-flow-generated-status.txt` |
| DS-A11 | terminal log | Fresh listener cleanup proof after this addendum request; no listeners on 5174, 5175, or 8765, `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-addendum-listeners.txt` |

## DoneClaim Check

The DoneClaim is accepted for the requested QA surface. Fresh browser reruns confirm the Dashboard extraction preserved dirty artifact, dirty mission, dirty tab-switch, Save, and Discard behavior. Fresh gate evidence confirms typecheck, tests, and scoped diff-check pass. Generated ownership remains Todo 7-owned. Listener cleanup passes after reruns.

## Blockers

None.
