# Todo 6 Manual QA Addendum: Post-Fix Tab-Switch Blocker

Plan: `.omo/plans/signoff-ui-flow.md` Todo 6, "Prevent dirty artifact loss across artifact and mission switches".

DoneClaim under review: `.omo/evidence/task-6-signoff-ui-flow-fix-doneclaim.txt`.

Scope: QA/report artifacts only. No product source was edited.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-PF-SE-001 | post-fix dirty Artifacts -> Timeline -> Artifacts tab switch: draft marker preserved | Browser UI at `http://127.0.0.1:5175/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-tab-switch-qa.mjs` | PASS | PF-A1, PF-A2 |
| T6-PF-SE-002 | post-fix dirty Artifacts -> Timeline -> Artifacts tab switch: Timeline not shown after dirty click | Browser UI at `http://127.0.0.1:5175/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-tab-switch-qa.mjs` | PASS | PF-A1, PF-A2 |
| T6-PF-SE-003 | post-fix dirty Artifacts -> Timeline -> Artifacts tab switch: inline warning appears | Browser UI at `http://127.0.0.1:5175/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-tab-switch-qa.mjs` | PASS | PF-A1, PF-A2 |
| T6-PF-SE-004 | existing dirty artifact switch remains blocked | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | PF-A3, PF-A4 |
| T6-PF-SE-005 | existing dirty mission switch remains blocked | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | PF-A3, PF-A4 |
| T6-PF-SE-006 | existing Save then artifact switch still works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | PF-A3, PF-A4 |
| T6-PF-SE-007 | existing Discard then mission switch still works | Browser UI at `http://127.0.0.1:5174/`, API routed to temporary `signoff.web.create_server` | `node /tmp/signoff-ui-flow-editor-qa.mjs` | PASS | PF-A3, PF-A4 |
| T6-PF-SE-008 | listener cleanup after browser QA | OS TCP listeners | `lsof -nP -iTCP:5174 -sTCP:LISTEN; lsof -nP -iTCP:5175 -sTCP:LISTEN; lsof -nP -iTCP:8765 -sTCP:LISTEN` | PASS | PF-A5 |
| T6-PF-SE-009 | generated ownership unchanged | Git status plus existing ownership report | `git status --short -- src/signoff/web_dist apps/web/dist .omo/evidence/task-6-signoff-ui-flow-generated-ownership.txt .omo/evidence/task-6-signoff-ui-flow-generated-status.txt` | PASS | PF-A6 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| T6-PF-ADV-001 | dirty tab switch must not unmount editor and lose draft | stale state | Clicking `Timeline` while `CHARTER.md` is dirty keeps the draft marker visible and leaves the user on `Artifacts`. | PASS | PF-A1, PF-A2 |
| T6-PF-ADV-002 | dirty tab switch must warn instead of silently ignoring the click | misleading success output | The blocked `Timeline` click shows the inline warning; transcript records `warningCountAfterTimelineClick: 1`. | PASS | PF-A1, PF-A2 |
| T6-PF-ADV-003 | existing artifact/mission guards must not regress | stale state | Dirty artifact switch and dirty mission switch remain blocked; explicit Save and Discard still unblock their respective workflows. | PASS | PF-A3, PF-A4 |
| T6-PF-ADV-004 | QA cleanup must not leave local servers | hung or long commands | No listeners remain on QA ports 5174, 5175, or 8765 after the reruns. | PASS | PF-A5 |
| T6-PF-ADV-005 | generated bundle dirt must stay unclaimed by Todo 6 | dirty worktree | Generated bundle dirt remains classified as Todo 7-owned; the ownership report did not need an update. | PASS | PF-A6 |

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| PF-A1 | transcript | Fresh post-fix browser QA for dirty `Artifacts -> Timeline -> Artifacts`: `tabSwitchPreservedDraft=true`, `timelineVisibleAfterClick=false`, `warningCountAfterTimelineClick=1`, `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt` |
| PF-A2 | screenshot | Fresh post-fix browser screenshot from tab-switch QA. | `.omo/evidence/task-6-signoff-ui-flow-tab-switch.png` |
| PF-A3 | transcript | Fresh editor QA confirming `artifactSwitchBlocked=true`, `missionSwitchBlocked=true`, `tabSwitchBlocked=true`, `savedAfterClick=true`, `switchAfterSave=true`, `switchMissionAfterDiscard=true`, `result: PASS`. | `.omo/evidence/task-6-signoff-ui-flow-editor.txt` |
| PF-A4 | screenshot | Fresh editor QA screenshot. | `.omo/evidence/task-6-signoff-ui-flow-editor.png` |
| PF-A5 | terminal log | Listener cleanup proof for 5174, 5175, and 8765; no listener rows and explicit PASS line. | `.omo/evidence/task-6-signoff-ui-flow-postfix-listeners.txt` |
| PF-A6 | ownership report | Existing generated bundle ownership decision; unchanged because generated dirt remains Todo 7-owned. | `.omo/evidence/task-6-signoff-ui-flow-generated-ownership.txt` |

## Verdict

PASS. The previous reject blocker is closed by current browser evidence: the dirty draft marker is preserved, Timeline is not shown after the dirty click, and the inline warning appears. No blockers found in the requested QA/report scope.
