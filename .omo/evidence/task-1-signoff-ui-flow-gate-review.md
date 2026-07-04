# Todo 1 Signoff UI Flow Gate Review

recommendation: REJECT

## originalIntent
Verify Todo 1 of `.omo/plans/signoff-ui-flow.md`: server-owned restartability and hard-integrity legality for the Signoff UI/API.

## desiredOutcome
Only `IDLE`, `DONE`, and `STOPPED` are restartable. `PIVOT` and `BLOCKED` cannot start a normal next mission via overview/UI API or `POST /api/missions`. Hard integrity failure is only top-level `status.integrity.status == "fail"`, blocks actions, and returns repair-oriented next text. Nested `scope.status == "fail"` under `VERIFY_FAILED` is not hard integrity corruption. The UI API type contract exposes the new overview fields.

## userOutcomeReview
The current implementation behavior matches the Todo 1 user-visible outcome in direct tests and HTTP probes. The API now reports legality and hard-integrity state from server-owned policy instead of client guesswork. The scoped DoneClaim patch does not include generated bundle paths.

This gate still cannot approve under final-gate rules because required review artifacts are absent: no independent code review report with explicit `programming` and `remove-ai-slops` coverage, no manual QA matrix, and no notepad path were provided or found. The worktree also contains unrelated dirty generated bundle changes, so ownership of generated file dirt cannot be proven from current git state alone.

## checked artifact paths
- `AGENTS.md`
- `.omo/plans/signoff-ui-flow.md`
- `src/signoff/runtime.py`
- `src/signoff/web.py`
- `tests/test_web.py`
- `apps/web/src/api.ts`
- `.omo/evidence/task-1-signoff-ui-flow-red.txt`
- `.omo/evidence/task-1-signoff-ui-flow-focused.txt`
- `.omo/evidence/task-1-signoff-ui-flow-api.txt`
- `.omo/evidence/task-1-signoff-ui-flow-typecheck.txt`
- `.omo/evidence/task-1-signoff-ui-flow-http.txt`
- `.omo/evidence/task-1-signoff-ui-flow-doneclaim.txt`
- `.omo/evidence/task-1-signoff-ui-flow-diff.patch`
- `.omo/evidence/task-1-signoff-ui-flow-worktree.txt`

## commands inspected or run
- `git status --short`
- `git diff -- src/signoff/runtime.py`
- `git diff -- src/signoff/web.py`
- `git diff -- tests/test_web.py`
- `git diff -- apps/web/src/api.ts`
- `git diff --name-status`
- `git diff --stat`
- `git diff --check -- src/signoff/runtime.py src/signoff/web.py tests/test_web.py apps/web/src/api.ts`
- `PYTHONPATH=src python3 -m unittest tests.test_web.WebApiTests.test_pivot_and_blocked_are_not_restartable tests.test_web.WebApiTests.test_hard_integrity_failure_blocks_actions`
- Same focused unittest command rerun a second time.
- `npm run typecheck`
- Inline `PYTHONPATH=src python3` HTTP probe covering malformed `POST /api/missions`, hard-integrity `/api/overview`, PIVOT `/api/overview`, and PIVOT `POST /api/missions`.

## blockers
- Missing required independent code review report with explicit `programming` and `remove-ai-slops`/overfit-slop coverage.
- Missing manual QA matrix artifact.
- Missing notepad path.
- Current worktree includes unrelated generated `src/signoff/web_dist` changes. The scoped Todo 1 patch excludes them, but current git state cannot independently prove they were not touched by the Todo 1 worker.

## exact evidence gaps
- `find .omo/evidence -maxdepth 1 -type f \( -iname '*review*' -o -iname '*qa*' -o -iname '*matrix*' -o -iname '*notepad*' \) -print` returned no review, QA matrix, or notepad artifacts.
- `.omo/evidence/task-1-signoff-ui-flow-doneclaim.txt` lists adversarial classes but does not include a code review report with skill-perspective checks or overfit/slop criterion coverage.
- `git diff -- src/signoff/web_dist apps/web/dist` shows generated bundle diffs in the current worktree, while `.omo/evidence/task-1-signoff-ui-flow-diff.patch` excludes generated bundles.

## direct slop and overfit pass
- No deletion-only tests found.
- No tautological tests found.
- No implementation-mirroring assertions found; assertions target HTTP/API observable fields and restart rejection.
- No unnecessary production extraction found; the shared `RESTARTABLE_PHASES` concept is required by the plan and used by both runtime start and overview legality.
- Test duplication is acceptable: the extra STOPPED API-action test covers the HTTP action path while the combined restartability test covers runtime-seeded STOPPED/DONE/PIVOT/BLOCKED classes.

## recommendation
REJECT until the missing review/manual-QA/notepad artifacts are supplied or explicitly waived.
