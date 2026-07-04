PASS

# Todo 4 Code Review: signoff-ui-flow

codeQualityStatus: CLEAR
recommendation: APPROVE
reviewScope: `src/signoff/web.py`, `tests/test_web.py`, `apps/web/src/pages/Dashboard.tsx`, `apps/web/src/styles.css`
blockers: none

## Skill Perspective Check

Ran: `omo:remove-ai-slops` and `omo:programming`; loaded Python and TypeScript references before judging tests/maintainability.

Result: no Todo 4 blocker under either perspective. The Todo 4 change is direct source/API behavior, not a speculative abstraction, compatibility path, fake UI state, or duplicate source of truth. Existing file-size debt remains visible (`src/signoff/web.py` 422 pure LOC, `apps/web/src/pages/Dashboard.tsx` 274 pure LOC), but splitting these already-large files is outside Todo 4 and would violate the current scoped review.

## Findings By Severity

CRITICAL: none.

HIGH: none.

MEDIUM: none.

LOW: generated bundle dirtiness is Todo 7-owned, not Todo 4-owned. `git status --short -- src/signoff/web_dist apps/web/dist` shows dirty generated assets, and generated JS is stale relative to source. This does not block Todo 4 because `.omo/plans/signoff-ui-flow.md` assigns `npm run build:web`, `apps/web/dist`, and `src/signoff/web_dist` synchronization to Todo 7, and `.omo/start-work/notepad.md` says generated bundle changes stay unclaimed by Todos 1-4 until that rebuild. Supporting artifact: `.omo/evidence/task-4-signoff-ui-flow-generated-ownership.txt`.

## Source Behavior

- `src/signoff/web.py:102` builds mission summaries from root mission history; `src/signoff/web.py:180` rejects unknown mission ids before artifact/event reads.
- `src/signoff/web.py:187` makes artifacts editable only when the requested mission equals `active_mission_id`. This is the right boundary; historical UI state cannot grant write permission.
- `apps/web/src/pages/Dashboard.tsx:55` keeps selected mission in React state only. `apps/web/src/pages/Dashboard.tsx:71` defaults back to the active mission when the current selection is missing/stale.
- `apps/web/src/pages/Dashboard.tsx:263` renders `overview.missions`; `apps/web/src/pages/Dashboard.tsx:285` passes the selected mission only to `ArtifactPanel`/`Timeline`. Top-level phase, next copy, and actions still use active `overview` data.
- `apps/web/src/styles.css:114` adds a compact scrollable selector; mobile wrapping is handled at `apps/web/src/styles.css:174`.

## Type Safety And Boundary Validation

- TypeScript: no added `any`, `as any`, `@ts-ignore`, or `@ts-expect-error` in the scoped diff. Added/changed functions have explicit return types where applicable: `Dashboard(): ReactElement`, `runAction(...): void`, `submitNoteAction(): void`.
- Python: new test helpers have explicit `-> None`; the Todo 4 production hunk does not add new `Any` annotations. Existing `dict[str, Any]` API typing in `src/signoff/web.py` is pre-existing debt, not a Todo 4 regression.
- Boundary validation: `/api/artifacts?missionId=...` and `/api/events?missionId=...` validate mission ids through `_require_known_mission`; artifact writes still go through `_safe_artifact_path` and `_editable_paths`, so inactive mission selection cannot bypass edit legality.

## Slop / Overfit Review

- Tests are not deletion-only or tautological. `.omo/evidence/task-4-signoff-ui-flow-red.txt` shows `test_inactive_mission_artifacts_are_read_only` failed before the server editability fix, then the focused rerun passed.
- Tests assert observable API behavior: at least two mission summaries, active flags, and read-only historical artifacts (`tests/test_web.py:106`, `tests/test_web.py:127`). They do not mirror implementation constants.
- No Todo 5 contract bleed: `.omo/evidence/task-4-signoff-ui-flow-no-todo5-rg.txt` reports no `proofSummary` or `inspectMissionId` source/test matches.
- No fake UI state: browser evidence `.omo/evidence/task-4-signoff-ui-flow-missions.txt` drives source UI and confirms active default, old mission selection, artifact/timeline change, active action preservation, malformed mission/path 400s, and historical PUT 400.

## Verification

- Reran: `PYTHONPATH=src python3 -m unittest tests.test_web.WebApiTests.test_overview_lists_stopped_and_next_mission tests.test_web.WebApiTests.test_inactive_mission_artifacts_are_read_only` -> PASS, 2 tests.
- Reran: `npm run typecheck` -> PASS.
- Reran: `git diff --check -- src/signoff/web.py tests/test_web.py apps/web/src/pages/Dashboard.tsx apps/web/src/styles.css` -> PASS.
- Inspected full Todo 4 evidence: API red/green transcripts, full `python3 scripts/test.py` transcript, browser mission transcript/screenshot, manual QA matrix, and generated ownership artifact.

## Decision

Todo 4 source/API behavior is approvable. Current dirty/stale `src/signoff/web_dist/` is not blocking Todo 4; it must remain Todo 7 work because Todo 7 owns the official packaged UI rebuild and source-to-generated synchronization.
