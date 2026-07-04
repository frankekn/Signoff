# Todo 1 Code Review - signoff-ui-flow

Verdict: PASS
codeQualityStatus: WATCH
recommendation: APPROVE
reportPath: `.omo/evidence/task-1-signoff-ui-flow-code-review.md`
blockers: none

## Scope Reviewed

Plan: `.omo/plans/signoff-ui-flow.md` Todo 1.
Notepad: `.omo/start-work/notepad.md`.
Scoped files: `src/signoff/runtime.py`, `src/signoff/web.py`, `tests/test_web.py`, `apps/web/src/api.ts`.

Dirty worktree note: inspected `git status --short` and `.omo/evidence/task-1-signoff-ui-flow-dirty-scope.txt`. The current worktree contains unrelated/generated changes, including `src/signoff/web_dist/**`, `apps/web/src/pages/Dashboard.tsx`, `apps/web/src/styles.css`, `package-lock.json`, `src/signoff/git.py`, and `tests/test_conformance.py`. The notepad and dirty-scope artifact explicitly keep those out of Todo 1. Generated bundle changes are not approved as Todo 1 work and must remain owned by Todo 7.

## Skill Perspective Check

Ran the required perspective check:

- `omo:programming`: loaded `SKILL.md`, `references/python/README.md`, and `references/typescript/README.md`.
- `omo:remove-ai-slops`: loaded `SKILL.md` and applied the overfit/slop categories to production and test diffs.
- Ponytail mode was active; review applied delete-first/no-speculative-abstraction criteria.

Diff-specific result: no new `Any`/`any`, suppressions, compatibility shim, broad defensive fallback, duplicate client/server action policy, or speculative abstraction found in the scoped Todo 1 diff.

Pre-existing context: `src/signoff/runtime.py` and `src/signoff/web.py` already exceed the programming skill's 250 pure-LOC ideal (`764` and `421` pure LOC). This is not introduced by Todo 1 and the plan explicitly targets those modules, so it is not a Todo 1 blocker.

## Verification Performed

Inspected:

- `.omo/plans/signoff-ui-flow.md`
- `.omo/start-work/notepad.md`
- full scoped diff and line-numbered scoped files
- `.omo/evidence/task-1-signoff-ui-flow-red.txt`
- `.omo/evidence/task-1-signoff-ui-flow-focused.txt`
- `.omo/evidence/task-1-signoff-ui-flow-api.txt`
- `.omo/evidence/task-1-signoff-ui-flow-typecheck.txt`
- `.omo/evidence/task-1-signoff-ui-flow-http.txt`
- `.omo/evidence/task-1-signoff-ui-flow-dirty-scope.txt`

Independent commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.test_web.WebApiTests.test_pivot_and_blocked_are_not_restartable \
  tests.test_web.WebApiTests.test_hard_integrity_failure_blocks_actions
git diff --check
rg -n "\bAny\b|\bany\b|as any|Array<any>|Promise<any>|Record<string, any>|@ts-ignore|@ts-expect-error|eslint-disable|type: ignore|# type: ignore|typing.Any|cast\(" \
  src/signoff/runtime.py src/signoff/web.py tests/test_web.py apps/web/src/api.ts
```

Results:

- Focused Todo 1 tests: PASS, 2 tests OK.
- `git diff --check`: PASS.
- Evidence `python3 scripts/test.py`: PASS, 27/27.
- Evidence `npm run typecheck`: PASS.
- Red-first evidence: meaningful. The old behavior failed because PIVOT was restartable and `blockedByIntegrity` was missing, not because of a tautological delete-only test.

## Behavior Review

Todo 1 behavior matches the plan:

- `RESTARTABLE_PHASES = {"IDLE", "DONE", "STOPPED"}` is the single server-owned restartability concept at `src/signoff/runtime.py:53`.
- `Runtime.start()` uses that concept and rejects active `PIVOT`/`BLOCKED` missions at `src/signoff/runtime.py:192`.
- `build_overview()` exposes `canStartMission`, `blockedByIntegrity`, `integrityStatus`, and `integrityMessage` at `src/signoff/web.py:138` and `src/signoff/web.py:168`.
- Top-level `status.integrity.status == "fail"` empties advancing actions and replaces `next` with repair guidance at `src/signoff/web.py:157`.
- Nested failed scope remains actionable because the hard block only checks the top-level `status` field, not nested `scope.status`, at `src/signoff/web.py:139`.
- TypeScript API shape was updated without adding client-side action policy in `apps/web/src/api.ts:40`.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

1. Dirty worktree risk remains operationally important, though documented.
   `git status --short` shows generated `src/signoff/web_dist/**` changes and other non-Todo-1 files. The notepad and dirty-scope artifact correctly say those are outside Todo 1 and must wait for Todo 7. Do not include them in any Todo 1 approval/commit.

2. `tests/test_web.py:106` combines STOPPED, DONE, PIVOT, and BLOCKED into one test. The assertions are behavior-level and red-first, not tautological, but a future split would improve failure localization. Not a gate blocker.

3. Existing Python modules touched by Todo 1 are oversized under the programming skill's stricter 250 pure-LOC rule. This is pre-existing and not caused by the Todo 1 diff; no new abstraction was added.

## Slop / Overfit Coverage

No deletion-only tests, requested-removal-only tests, tautological constant-mirroring tests, prompt brittle tests, compatibility shims, speculative helpers, or unnecessary production parsing/normalization were found in the scoped diff.

The two new test helpers are reused and central to fixture state setup. Direct Council JSON mutation in `conclude_from_council()` is acceptable test setup for constructing PIVOT/BLOCKED states through the existing lock path.

## Programming / Type-Safety Coverage

No diff-added `Any`, TypeScript `any`, type suppressions, non-null assertions, dynamic imports, or untyped escape hatches were found. New Python test helper functions have explicit return types. Typecheck evidence passed.

Existing `Any` usage remains in the pre-existing Python runtime/web API surface; not introduced by this Todo 1 diff.

## Final Decision

PASS for Todo 1 scoped implementation.

Approval is scoped only to `src/signoff/runtime.py`, `src/signoff/web.py`, `tests/test_web.py`, and `apps/web/src/api.ts`. Generated bundles and unrelated dirty files remain unapproved for Todo 1.
