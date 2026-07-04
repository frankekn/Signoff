---
slug: signoff-ui-flow
status: plan-written-awaiting-execution
intent: clear
pending-action: user chooses $start-work or high-accuracy review
approach: Fix the current UI flow semantics around legal state, evidence, delegation, and mission history without adding dependencies or a new app architecture.
---

# Draft: signoff-ui-flow

## Components (topology ledger)
| id | outcome (one line) | status | evidence path |
| --- | --- | --- | --- |
| C1 | Server overview and runtime restart policy expose only legal UI actions for integrity, PIVOT, BLOCKED, DONE, and STOPPED. | active | src/signoff/web.py:31, src/signoff/web.py:134, src/signoff/runtime.py:180, src/signoff/runtime.py:768 |
| C2 | Phase rail and top-level state copy represent failure, pause, pivot, block, and signed-off states truthfully. | active | apps/web/src/components/PhaseRail.tsx:1, apps/web/src/pages/Dashboard.tsx:9 |
| C3 | Agent handoff copy is generated from the live mission state and tells the coding agent the exact legal next move. | active | apps/web/src/pages/Dashboard.tsx:93, src/signoff/runtime.py:768 |
| C4 | Mission history is visible and old receipts/evidence can be inspected without making old missions editable. | active | src/signoff/web.py:102, apps/web/src/api.ts:10, apps/web/src/pages/Dashboard.tsx:207 |
| C5 | Verification/review/signoff decisions show readable proof before the user can sign off. | active | src/signoff/runtime.py:695, apps/web/src/components/Timeline.tsx:23, src/signoff/web.py:172 |
| C6 | Evidence notes and artifact edits are captured in the UI without prompt boxes or silent dirty-state loss. | active | apps/web/src/pages/Dashboard.tsx:79, apps/web/src/components/ArtifactPanel.tsx:55 |
| C7 | Packaged UI and full repo gates prove the installed one-path experience still works. | active | package.json:8, scripts/check_repo.py:104, src/signoff/web.py:425 |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
| --- | --- | --- | --- |
| New frontend dependencies | Add none. Use existing React state, existing CSS, and existing API client. | Repo instruction says runtime deps stay zero; current app already has enough primitives. | Yes |
| UI topology | Keep the single dashboard page. Do not add routes or an app shell rewrite. | Findings are flow semantics, not navigation architecture. | Yes |
| Source of truth | Server/runtime owns legal actions, restartability, active editability, and proof summaries; client formats them. | Prevents a second policy copy in the UI. | Yes |
| Historical inspection contract | `GET /api/overview?inspectMissionId=<id>` returns active-mission legal fields plus `inspectedMission` and `proofSummary` for the requested mission. | The UI needs selected-mission proof without changing active-mission actions. | Yes |
| Restart policy | Only `IDLE`, `DONE`, and `STOPPED` may show/start a new mission. `PIVOT` requires `authorize_pivot`; `BLOCKED` requires resolving the blocker outside this mission first. | `next_action()` already says PIVOT/BLOCKED are not normal "start next mission" states. | Yes |
| Integrity wording | Split hard integrity failure from ordinary failed evidence/scope. Hard integrity blocks UI actions; failed verification points to re-run/fix flow. | Current `containsFailure()` treats nested scope failures as integrity corruption. | Yes |
| Test strategy | TDD for runtime/API contract changes; tests-after for pure UI rendering details; browser QA always required. | Server contract must fail first; UI behavior is best proven through the browser surface. | Yes |

## Findings (cited - path:lines)
- `PhaseRail` maps `VERIFY_FAILED` to `IMPLEMENTING` and `STOPPED`/`BLOCKED`/`PIVOT` to `DONE`, which visually turns non-signed-off states into progress or completion: apps/web/src/components/PhaseRail.tsx:11.
- Dashboard reduces integrity to a recursive boolean and renders it as one small stat while still rendering actions: apps/web/src/pages/Dashboard.tsx:34, apps/web/src/pages/Dashboard.tsx:89, apps/web/src/pages/Dashboard.tsx:173.
- `build_overview()` returns actions by phase and only removes `finish_done` when `current.final` is false; it does not gate on hard integrity failure: src/signoff/web.py:146.
- `Runtime.start()` allows starting a new mission after any `TERMINAL_PHASES`, but `next_action()` says `PIVOT` must go through pivot gate and `BLOCKED` must resolve the blocker first: src/signoff/runtime.py:180, src/signoff/runtime.py:793.
- The agent copy is static and omits mission id, phase, exact next action, editable paths, and current command: apps/web/src/pages/Dashboard.tsx:93.
- The API returns mission summaries, but Dashboard ignores them and always shows the active mission artifacts/timeline: src/signoff/web.py:102, apps/web/src/api.ts:10, apps/web/src/pages/Dashboard.tsx:207.
- Artifact editability is calculated from the requested mission state, not explicitly from "active mission only"; historical inspection must not imply old missions can be edited: src/signoff/web.py:172.
- Timeline dumps raw JSON payloads; it does not expose hash-chain or proof summary in the decision surface: apps/web/src/components/Timeline.tsx:23.
- Rework/stop/pivot notes use `window.prompt`, which is too weak for receipt-critical rationale: apps/web/src/pages/Dashboard.tsx:79.
- Artifact selection resets dirty state on path switch, so unsaved edits can disappear: apps/web/src/components/ArtifactPanel.tsx:55.
- Existing web tests cover overview/artifact round trip and STOPPED startability, but not PIVOT/BLOCKED, hard integrity action blocking, mission switching, copy payload, note form, proof summary, or dirty edit protection: tests/test_web.py:46.
- Build/test gates are already defined and must remain the final repo checks: package.json:8, scripts/test.py:13, scripts/check_repo.py:104.

## Decisions (with rationale)
- D1: Fix policy at the server/runtime boundary first. UI controls must consume legal state, not infer legality from copy.
- D2: Do not add a router or page split. A mission switcher inside the current dashboard is enough.
- D3: Replace "integrity recursive failure" with explicit hard integrity vs proof/scope status. This avoids blocking normal VERIFY_FAILED remediation while still preventing actions on hash/ledger corruption.
- D4: Add a compact proof summary to `/api/overview` rather than a new endpoint. `inspectMissionId` selects which mission is summarized; `status`, `actions`, `canStartMission`, `blockedByIntegrity`, `editablePaths`, `goal`, and `next` remain active-mission scoped.
- D5: Keep raw artifacts and raw timeline available, but make them secondary to readable proof and receipt summaries.
- D6: Replace prompt flows with one inline note panel shared by note-required actions; no modal framework.
- D7: Keep generated `apps/web/dist` and `src/signoff/web_dist` rebuilt only through `npm run build:web`.

## Scope IN
- Runtime/API restartability for `DONE`, `STOPPED`, `PIVOT`, and `BLOCKED`.
- API action filtering for hard integrity failure.
- Overview proof summary fields needed by the UI to show verification/review/signoff evidence for the active mission or an inspected historical mission.
- Mission selector for active and historical missions.
- Active-only editability and visible sealed/generated state.
- Phase rail and hero state copy for failure, review, pivot, block, stopped, and signed-off phases.
- Dynamic agent handoff copy.
- Inline note form for note-required actions.
- Dirty artifact switching guard.
- Tests and browser QA for the actual dashboard flow.

## Scope OUT (Must NOT have)
- No new runtime dependencies.
- No new frontend package.
- No new routing system, multi-page app, or workflow canvas.
- No redesign of the visual theme beyond layout needed for the new flow controls.
- No protocol schema changes unless an existing artifact lacks enough data for a proof summary.
- No changes to Council/Roast validation semantics.
- No edits to `.signoff/` dogfood receipts except incidental local QA artifacts outside commits.

## Open questions
None blocking. Defaults above are adopted for this plan. Metis gap B1 resolved by the `inspectMissionId` overview contract.

## Approval gate
status: plan-written-awaiting-execution
The user explicitly requested a plan based on the findings. The plan file has been generated. Execution still requires a separate start signal (`$start-work` or equivalent). CLEAR path high-accuracy review is optional before execution.
