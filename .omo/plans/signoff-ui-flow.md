# signoff-ui-flow - Work Plan

## TL;DR (For humans)
**What you'll get:** The UI will behave like a real Signoff control surface: it will show the true legal state, the exact next move, the evidence behind a signoff decision, and old mission receipts without making unsafe actions look available.

**Why this approach:** The broken parts are policy and flow semantics, not visual polish. The plan fixes the server-owned legality first, then makes the dashboard render that legality without adding a new app structure.

**What it will NOT do:** It will not add dependencies, create a new routing system, redesign the brand/theme, or change Council/Roast protocol rules.

**Effort:** Medium
**Risk:** Medium - the work touches runtime/API state contracts plus the main dashboard flow.
**Decisions to sanity-check:** `PIVOT` and `BLOCKED` will not show "Start the next mission"; only `DONE` and `STOPPED` are restartable from the UI. Historical proof is inspected through `GET /api/overview?inspectMissionId=<id>` while legal actions stay scoped to the active mission.

Your next move: approve execution with `$start-work`, or ask for the optional high-accuracy plan review first. Full execution detail follows below.

---

> TL;DR (machine): Medium risk; fix Signoff UI flow by grounding actions, state rail, evidence, agent handoff, mission history, and edit safety in server-owned legal state.

## Scope
### Must have
- Runtime/API restartability distinguishes `IDLE`/`DONE`/`STOPPED` from `PIVOT`/`BLOCKED`.
- Hard integrity failure blocks UI actions and is visually dominant.
- Failed verification/scope state remains actionable through the legal remediation path and is not mislabeled as hash-chain corruption.
- Phase rail never renders `STOPPED`, `BLOCKED`, `PIVOT`, or `VERIFY_FAILED` as signed off.
- Agent copy includes live mission id, phase, next action, editable paths, and action limits.
- Mission history is visible; selecting an old mission shows artifacts/timeline read-only and does not change active mission legality.
- Signoff/rework decisions show readable proof: commands, scope status, evidence hashes, review gate decision, accepted criteria, final receipt when present.
- Note-required actions use an inline note form with validation, not `window.prompt`.
- Unsaved artifact edits cannot be silently discarded by switching artifacts or missions.
- `web_dist` is regenerated through the existing build path.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No new runtime dependency.
- No new frontend dependency.
- No router/page split.
- No speculative domain model or protocol schema rewrite.
- No compatibility shim or duplicate action policy in the client.
- No direct edits to generated UI bundles except via `npm run build:web`.
- No changes to Council/Roast quorum, independence, or schema semantics.
- No commits touching unrelated dirty worktree files unless they are required by this plan.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD for runtime/API legality changes in `tests/test_web.py`; tests-after for UI-only behavior through browser QA because no frontend test harness exists.
- Unit/API gates:
  - `python3 scripts/test.py`
  - `python3 scripts/check_repo.py`
  - `npm run typecheck`
  - `npm run build:web`
- Browser QA gate:
  - Each `/tmp/signoff-ui-flow-*-qa.mjs` script starts a Python child process that imports `tests.support.RepoFixture`, seeds the requested state through `Runtime`/`RepoFixture` methods, serves Signoff on a random local port with `create_server()`, prints one JSON line containing `{ "baseUrl": "...", "project": "...", "missionIds": [...] }`, then Playwright drives that real page.
  - State seeding must use runtime/API methods where possible: `runtime.finish("stopped")`, `runtime.finish("blocked", note=...)`, `runtime.finish("pivot", note=...)`, `runtime.authorize_pivot(...)`, `fx.lock()`, `fx.activate(...)`, `fx.implement()`, `runtime.verify()`, `fx.fill_roast(...)`, `runtime.roast()`, and `runtime.finish(...)`. Direct `.signoff/STATE.json` mutation is allowed only to create a hard integrity/tamper fixture that cannot be produced by legal runtime calls.
  - Save action logs and screenshots under `.omo/evidence/`.
- Evidence naming:
  - `.omo/evidence/task-1-signoff-ui-flow-api.txt`
  - `.omo/evidence/task-2-signoff-ui-flow-phase-rail.png`
  - `.omo/evidence/task-3-signoff-ui-flow-agent-copy.txt`
  - `.omo/evidence/task-4-signoff-ui-flow-missions.png`
  - `.omo/evidence/task-5-signoff-ui-flow-proof.png`
  - `.omo/evidence/task-6-signoff-ui-flow-editor.png`
  - `.omo/evidence/task-7-signoff-ui-flow-final.txt`

## Execution strategy
### Parallel execution waves
Wave 1: Todo 1 only. Server-owned legality must land first.

Wave 2: Todos 2, 3, and 4 can be implemented after Todo 1, but all touch `Dashboard.tsx`; avoid concurrent edits to the same file unless using separate worktrees. If one worker executes, do them in todo order.

Wave 3: Todos 5 and 6 after Todos 2-4. Proof summary and edit safety depend on the selected mission model.

Wave 4: Todo 7 only. Rebuild packaged assets and run full QA after all behavior work.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | None | 2, 3, 4, 5, 7 | None |
| 2 | 1 | 5, 7 | 3 and 4 only if file edits are coordinated |
| 3 | 1 | 7 | 2 and 4 only if file edits are coordinated |
| 4 | 1 | 5, 6, 7 | 2 and 3 only if file edits are coordinated |
| 5 | 1, 2, 4 | 7 | 6 after mission selection contract is stable |
| 6 | 4 | 7 | 5 |
| 7 | 1, 2, 3, 4, 5, 6 | Final handoff | None |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

- [x] 1. Fix server-owned legality for hard integrity and restartable phases
  What to do / Must NOT do: Add one deterministic restartability concept used by `Runtime.start()` and `build_overview()`: restartable is `IDLE`, `DONE`, or `STOPPED`; `PIVOT` and `BLOCKED` are terminal for implementation but not normal "start next mission" UI states. Add overview fields needed by the UI: `blockedByIntegrity`, `integrityStatus`, and a short `integrityMessage`. Treat top-level `status.integrity.status == "fail"` as hard integrity failure. Do not treat nested `scope.status == "fail"` as hard integrity corruption. When hard integrity fails, `/api/overview` must return no advancing actions and a next instruction that tells the user to inspect/repair integrity.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 3, 4, 5, 7
  References (executor has NO interview context - be exhaustive): `src/signoff/state.py:13`; `src/signoff/runtime.py:180`; `src/signoff/runtime.py:695`; `src/signoff/runtime.py:747`; `src/signoff/runtime.py:768`; `src/signoff/web.py:31`; `src/signoff/web.py:134`; `tests/test_web.py:72`
  Acceptance criteria (agent-executable): Add failing-first tests to `tests/test_web.py` proving: STOPPED overview `canStartMission=true`; DONE overview `canStartMission=true`; PIVOT overview `canStartMission=false`; BLOCKED overview `canStartMission=false`; `POST /api/missions` rejects active PIVOT/BLOCKED; hard integrity failure returns `blockedByIntegrity=true` and no actions; VERIFY_FAILED with failed scope does not set `blockedByIntegrity=true`.
  QA scenarios (name the exact tool + invocation): happy: `python3 scripts/test.py 2>&1 | tee .omo/evidence/task-1-signoff-ui-flow-api.txt` must show all tests pass and the new test names. failure: before production changes, run the new tests with `python3 -m unittest tests.test_web.WebApiTests.test_pivot_and_blocked_are_not_restartable tests.test_web.WebApiTests.test_hard_integrity_failure_blocks_actions` and capture failures in `.omo/evidence/task-1-signoff-ui-flow-red.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 2. Make the phase rail and hero state truthful
  What to do / Must NOT do: Replace the current alias table with explicit phase presentation data. `VERIFY_FAILED` must render as failed evidence, not completed build. `COUNCIL_REVIEW` must render as paused review, not normal Council progress. `STOPPED`, `BLOCKED`, and `PIVOT` must render as terminal/paused outcomes and must never mark "Sign off" as complete. `REVIEWED` may show review decision pending, not signed off. Keep the component small; no animation system, no external icons.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 5, 7
  References (executor has NO interview context - be exhaustive): `apps/web/src/components/PhaseRail.tsx:1`; `apps/web/src/pages/Dashboard.tsx:9`; `apps/web/src/styles.css:61`; `src/signoff/runtime.py:782`
  Acceptance criteria (agent-executable): In the browser, force or create `VERIFY_FAILED`, `COUNCIL_REVIEW`, `STOPPED`, `BLOCKED`, and `PIVOT` fixtures and assert visible text contains those states while `.phase-rail` does not show `Sign off` as active/complete for COUNCIL_REVIEW/STOPPED/BLOCKED/PIVOT. The hero badge tone must be bad for VERIFY_FAILED/BLOCKED and paused/terminal for COUNCIL_REVIEW/STOPPED/PIVOT.
  QA scenarios (name the exact tool + invocation): happy: `node /tmp/signoff-ui-flow-phase-rail-qa.mjs` seeds states via the shared Python fixture process (`VERIFY_FAILED` by `fx.lock()` plus failing `fx.activate(command=[...])` plus `runtime.verify()`, `COUNCIL_REVIEW` by repeated `runtime.finish("rework", root_cause=...)`, `STOPPED`/`BLOCKED`/`PIVOT` by `runtime.finish(...)`), drives the local UI with Playwright, captures `.omo/evidence/task-2-signoff-ui-flow-phase-rail.png`, and writes PASS only if all five states render truthfully. failure: seed a PIVOT fixture and assert `locator('.phase-rail').getByText('Sign off')` is not in an active/complete list; evidence `.omo/evidence/task-2-signoff-ui-flow-phase-rail-failure.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 3. Replace static agent copy and prompt actions with live handoff and inline notes
  What to do / Must NOT do: Generate agent handoff copy from `overview.status.mission_id`, `overview.status.phase`, `overview.next`, `overview.editablePaths`, and available actions. Include "do not edit locked/generated artifacts" and the current legal command/action. Replace `window.prompt` with an inline note panel for `requiresNote` actions. Blank notes must not submit. Preserve the existing `/api/action` payload shape unless a server-side validation message is needed.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 7
  References (executor has NO interview context - be exhaustive): `apps/web/src/pages/Dashboard.tsx:79`; `apps/web/src/pages/Dashboard.tsx:93`; `apps/web/src/pages/Dashboard.tsx:154`; `src/signoff/runtime.py:768`; `src/signoff/web.py:210`
  Acceptance criteria (agent-executable): Browser QA in DRAFT shows copied text includes mission id, `DRAFT`, `CHARTER.md`, `SPEC.json`, and the live next action. In COUNCIL_REVIEW, clicking `Authorize pivot` opens inline note UI, empty submit is blocked, and a valid note posts to `/api/action` and returns DRAFT. `window.prompt` must not be called.
  QA scenarios (name the exact tool + invocation): happy: `node /tmp/signoff-ui-flow-agent-copy-qa.mjs` seeds DRAFT with `RepoFixture`, then seeds COUNCIL_REVIEW by reaching REVIEWED and calling `runtime.finish("rework", root_cause=...)` twice through the Python fixture process, opens the page, clicks Copy for agent, reads clipboard or intercepts `navigator.clipboard.writeText`, submits a pivot note, and writes `.omo/evidence/task-3-signoff-ui-flow-agent-copy.txt`. failure: monkeypatch `window.prompt = () => { throw new Error("prompt called") }` before clicking a note-required action; evidence `.omo/evidence/task-3-signoff-ui-flow-no-prompt.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 4. Add mission history selection with active-only editability
  What to do / Must NOT do: Render `overview.missions` in the dashboard as a compact mission selector. Default to active mission. Selecting a historical mission updates `ArtifactPanel` and `Timeline` only in this todo; it must not change top-level legal actions for the active mission. Update artifact listing so `editable` is true only for the active mission and current editable paths. Do not add routing or persist selection outside React state. Do not add `proofSummary` or `inspectMissionId` here; Todo 5 owns that contract.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 5, 6, 7
  References (executor has NO interview context - be exhaustive): `src/signoff/web.py:102`; `src/signoff/web.py:172`; `src/signoff/web.py:391`; `apps/web/src/api.ts:10`; `apps/web/src/pages/Dashboard.tsx:207`; `apps/web/src/components/ArtifactPanel.tsx:22`; `apps/web/src/components/Timeline.tsx:11`
  Acceptance criteria (agent-executable): Add API tests proving `/api/overview` returns at least two mission summaries after STOPPED plus a second mission, and `/api/artifacts?missionId=<old>` marks all old mission artifacts read-only. Browser QA shows both missions, selecting the old mission changes artifacts/timeline content, and action buttons still reflect the active mission only.
  QA scenarios (name the exact tool + invocation): happy: `node /tmp/signoff-ui-flow-missions-qa.mjs` uses the Python fixture process to create mission A, stop it through `runtime.finish("stopped", note=...)`, start mission B through `runtime.start(...)`, selects mission A, screenshots `.omo/evidence/task-4-signoff-ui-flow-missions.png`, and writes selected mission ids plus artifact/timeline excerpts to `.omo/evidence/task-4-signoff-ui-flow-missions.txt`. failure: attempt `PUT /api/artifact` for a historical mission path with `curl -i -X PUT ...` and capture a 400 locked/generated error in `.omo/evidence/task-4-signoff-ui-flow-old-readonly.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 5. Add readable proof and receipt decision surface
  What to do / Must NOT do: Add `inspectMissionId` parsing to `GET /api/overview` and add a small server-built `proofSummary` to the response. Contract: without query params it summarizes the active mission; with `inspectMissionId=<known mission id>` it summarizes that inspected mission while `status`, `actions`, `canStartMission`, `blockedByIntegrity`, `editablePaths`, `goal`, and `next` remain scoped to the active mission. Include `inspectedMission` in the response so the UI cannot confuse active legality with inspected proof. Show command results, scope status, evidence hash, patch hash, review gate decision, accepted criteria count/list, `contract.final`, and final receipt hash/path when present. Keep raw artifact and timeline views. Do not invent green status when evidence is missing; show UNKNOWN or "not yet produced".
  Parallelization: Wave 3 | Blocked by: 1, 2, 4 | Blocks: 7
  References (executor has NO interview context - be exhaustive): `src/signoff/runtime.py:78`; `src/signoff/runtime.py:342`; `src/signoff/runtime.py:468`; `src/signoff/runtime.py:555`; `src/signoff/runtime.py:576`; `src/signoff/runtime.py:619`; `src/signoff/runtime.py:695`; `src/signoff/schemas.py:337`; `src/signoff/schemas.py:348`; `src/signoff/web.py:134`; `apps/web/src/pages/Dashboard.tsx:118`; `apps/web/src/components/Timeline.tsx:23`; `tests/support.py:116`; `tests/support.py:139`; `tests/support.py:147`; `tests/support.py:155`
  Acceptance criteria (agent-executable): API tests prove proof summary states: DRAFT -> unknown evidence; VERIFY_FAILED -> failed check/scope visible; REVIEWED PASS `contract.final=false` -> signoff unavailable but accepted/rework visible; REVIEWED PASS `contract.final=true` -> signoff available with review gate hash; DONE -> final receipt hash/path visible; historical `inspectMissionId` returns old proof while active actions stay active. Browser QA shows the proof summary above or beside raw artifacts before action buttons.
  QA scenarios (name the exact tool + invocation): happy: `node /tmp/signoff-ui-flow-proof-qa.mjs` uses the Python fixture process with `fx.passing_evidence(final=false)`, `fx.passing_evidence(final=true)`, `fx.fill_roast(...)`, `runtime.roast()`, and `runtime.finish("done")` to seed REVIEWED and DONE states, captures `.omo/evidence/task-5-signoff-ui-flow-proof.png`, and writes proof fields to `.omo/evidence/task-5-signoff-ui-flow-proof.json`. failure: create VERIFY_FAILED with `fx.activate(command=["git", "grep", "-F", "-q", "definitely-not-present", "--", "app.py"])` and `runtime.verify()`, then assert the UI shows the failed command id/exit code and no signoff button; evidence `.omo/evidence/task-5-signoff-ui-flow-verify-failed.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 6. Prevent dirty artifact loss across artifact and mission switches
  What to do / Must NOT do: Track dirty artifact edits by selected path. When dirty, switching artifact or mission must either keep the current selection and show an inline warning, or require explicit Discard. Save keeps current behavior. Do not use `window.confirm`; do not auto-save.
  Parallelization: Wave 3 | Blocked by: 4 | Blocks: 7
  References (executor has NO interview context - be exhaustive): `apps/web/src/components/ArtifactPanel.tsx:24`; `apps/web/src/components/ArtifactPanel.tsx:55`; `apps/web/src/components/ArtifactPanel.tsx:63`; `apps/web/src/pages/Dashboard.tsx:207`; `src/signoff/web.py:391`
  Acceptance criteria (agent-executable): Browser QA edits `CHARTER.md`, clicks `SPEC.json`, and proves the `CHARTER.md` draft remains visible or an inline discard confirmation blocks the switch. After Save, switching works. Selecting a historical mission while dirty is blocked until Save/Discard.
  QA scenarios (name the exact tool + invocation): happy: `node /tmp/signoff-ui-flow-editor-qa.mjs` seeds two missions through the shared Python fixture process, edits draft text, tries to switch artifacts/missions, saves, then switches; screenshot `.omo/evidence/task-6-signoff-ui-flow-editor.png`, transcript `.omo/evidence/task-6-signoff-ui-flow-editor.txt`. failure: before fix, the same script must show the draft text disappears after switching; capture `.omo/evidence/task-6-signoff-ui-flow-editor-red.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

- [x] 7. Rebuild packaged UI and run final real-surface verification
  What to do / Must NOT do: Run the existing build pipeline so `apps/web/dist` and `src/signoff/web_dist` match the source UI. Do not hand-edit generated assets. Run repo gates and a final browser flow covering install/open/start/edit/agent handoff/verify failed/reviewed/done/mission history.
  Parallelization: Wave 4 | Blocked by: 1, 2, 3, 4, 5, 6 | Blocks: final handoff
  References (executor has NO interview context - be exhaustive): `package.json:8`; `apps/web/package.json:6`; `scripts/copy_web_dist.py`; `scripts/test.py:13`; `scripts/check_repo.py:104`; `src/signoff/web.py:425`
  Acceptance criteria (agent-executable): `npm run typecheck`, `npm run build:web`, `python3 scripts/test.py`, and `python3 scripts/check_repo.py` all exit 0. Final Playwright QA verifies no console errors, all critical controls keyboard reachable, and terminal DONE screen shows signed-off proof plus a separate start-next-mission affordance.
  QA scenarios (name the exact tool + invocation): happy: `npm run typecheck 2>&1 | tee .omo/evidence/task-7-signoff-ui-flow-typecheck.txt && npm run build:web 2>&1 | tee .omo/evidence/task-7-signoff-ui-flow-build.txt && python3 scripts/test.py 2>&1 | tee .omo/evidence/task-7-signoff-ui-flow-tests.txt && python3 scripts/check_repo.py 2>&1 | tee .omo/evidence/task-7-signoff-ui-flow-check.txt && node /tmp/signoff-ui-flow-final-qa.mjs` with screenshot `.omo/evidence/task-7-signoff-ui-flow-final.png`. failure: run `git diff --check` and fail if generated bundles reference missing assets; evidence `.omo/evidence/task-7-signoff-ui-flow-diff-check.txt`.
  Commit: N | included in final `fix(ui): make signoff flow evidence-driven`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit: read `.omo/plans/signoff-ui-flow.md`, `git diff --stat`, and `git diff --name-only`; reject if implementation touches Scope OUT or leaves a todo unverified. Evidence `.omo/evidence/final-signoff-ui-flow-plan-compliance.txt`.
- [ ] F2. Code quality review: review `src/signoff/*.py`, `apps/web/src/*.ts*`, and changed tests for type safety, duplicate policy, prompt/modal regressions, and dead code. Evidence `.omo/evidence/final-signoff-ui-flow-code-quality.txt`.
- [ ] F3. Real manual QA: run the final Playwright scenario against a served disposable repo, capture desktop and mobile screenshots, and require PASS on actual UI text and controls. Evidence `.omo/evidence/final-signoff-ui-flow-manual-qa.txt`, `.omo/evidence/final-signoff-ui-flow-desktop.png`, `.omo/evidence/final-signoff-ui-flow-mobile.png`.
- [ ] F4. Scope fidelity: inspect `git diff -- . ':!src/signoff/web_dist/**' ':!apps/web/dist/**'` and generated asset references; reject unrelated formatting/package churn. Evidence `.omo/evidence/final-signoff-ui-flow-scope.txt`.

## Commit strategy
- One final commit after all todos and final verification pass: `fix(ui): make signoff flow evidence-driven`.
- Do not commit `.signoff/` dogfood artifacts.
- Include `.omo/plans/signoff-ui-flow.md` if Frank wants the plan committed; otherwise leave `.omo/` uncommitted as planning evidence.
- Commit generated `src/signoff/web_dist` changes only after `npm run build:web`.
- Do not amend existing commits unless explicitly requested.

## Success criteria
- A repo owner can start a mission, edit draft artifacts, copy a live agent handoff, understand the legal next action, inspect proof, and sign off only when evidence is visible.
- Failure, blocked, pivot, stopped, and signed-off states are visually and behaviorally distinct.
- Hard integrity failure blocks UI advancement; ordinary failed verification shows the remediation path.
- Historical missions and receipts are inspectable without making old artifacts editable.
- Note-required decisions capture rationale inline and persist through the existing action API.
- Dirty draft edits are not silently lost.
- All repo gates pass: `npm run typecheck`, `npm run build:web`, `python3 scripts/test.py`, `python3 scripts/check_repo.py`.
- Final browser QA passes on desktop and mobile with screenshots and no console errors.
