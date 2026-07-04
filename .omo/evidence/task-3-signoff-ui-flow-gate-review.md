recommendation: APPROVE
verdict: confirmed

# Task 3 Gate Review Refresh - signoff-ui-flow

## originalIntent

Todo 3 should replace static agent handoff copy with live overview-derived copy
and replace `window.prompt` note collection with inline note UI for
note-required actions.

## desiredOutcome

- Handoff copy uses live mission id, phase, next action, editable paths, and
  legal actions.
- Handoff copy includes action limits and locked/generated artifact warning.
- Note-required actions use inline UI.
- Blank note submit is blocked before `/api/action`.
- Valid note posts `{ action, note }` and pivot authorization returns to
  `DRAFT`.
- No Todo 4/5/6 scope is claimed.

## userOutcomeReview

Previous source-behavior review passed. This refresh only re-reviewed the prior
blockers:

- Missing code review artifact.
- Missing manual QA matrix artifact.
- Missing generated-bundle ownership artifact.

All three are now present and supported by raw evidence.

## checkedArtifactPaths

- `.omo/evidence/task-3-signoff-ui-flow-code-review.md`
- `.omo/evidence/task-3-signoff-ui-flow-manual-qa-matrix.md`
- `.omo/evidence/task-3-signoff-ui-flow-generated-ownership.txt`
- `.omo/evidence/task-3-signoff-ui-flow-source-vs-webdist.txt`
- `.omo/evidence/task-3-signoff-ui-flow-cleanup-lsof.txt`
- `.omo/evidence/task-3-signoff-ui-flow-git-diff-name-status.txt`
- `.omo/evidence/task-3-signoff-ui-flow-rg-source-and-web-dist.txt`
- `apps/web/src`
- `src/signoff/web_dist/assets/index-DctO2657.js`

## blockerReview

1. Code review artifact: PASS.
   `.omo/evidence/task-3-signoff-ui-flow-code-review.md` exists, recommends
   approve, and explicitly documents `omo:programming` plus
   `omo:remove-ai-slops` coverage. It covers no `any`/suppression/prompt,
   explicit return types, no new dependency/abstraction, behavior evidence, and
   the `Dashboard.tsx` 248 pure-LOC warning band.

2. Manual QA matrix artifact: PASS.
   `.omo/evidence/task-3-signoff-ui-flow-manual-qa-matrix.md` exists and
   enumerates source-served browser QA, red baseline, inline note UI,
   blank-note block, `{ action, note }`, no `window.prompt`, prompt-injection
   data handling, typecheck, cleanup, and generated-bundle ownership.

3. Generated-bundle ownership artifact: PASS.
   `.omo/evidence/task-3-signoff-ui-flow-generated-ownership.txt` exists and
   assigns stale packaged `src/signoff/web_dist/**` behavior to Todo 7. Raw
   evidence supports this: source grep has no `window.prompt` or old static
   copy; packaged JS still contains both; `git diff --name-status` shows dirty
   generated bundle paths.

## directEvidence

- `rg -n "window\\.prompt|Read AGENTS\\.md\\. Run \\./signoff status" apps/web/src`:
  no source matches.
- `src/signoff/web_dist/assets/index-DctO2657.js` still contains
  `window.prompt=True` and old static copy, and lacks `Mission id:` /
  `Required note` / blank-note text. This is documented Todo 7 ownership, not a
  Todo 3 blocker.
- `.omo/evidence/task-3-signoff-ui-flow-cleanup-lsof.txt`: no listeners on
  5173/8765.
- `.omo/evidence/task-3-signoff-ui-flow-git-diff-name-status.txt`: broader dirty
  worktree and generated bundle paths are recorded.

## exactEvidenceGaps

None for the prior blockers.

## final

The previous blockers are satisfied. Todo 3 source behavior and evidence are
confirmed within the scoped source-served boundary; packaged generated UI
remains Todo 7 work.
