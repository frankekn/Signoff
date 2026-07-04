# Todo 4 Gate Review: signoff-ui-flow

recommendation: APPROVE

AdversarialVerify {
  task: "Todo 4 - mission history selection with active-only editability",
  verdict: "confirmed",
  evidence: [
    ".omo/evidence/task-4-signoff-ui-flow-code-review.md",
    ".omo/evidence/task-4-signoff-ui-flow-manual-qa-matrix.md",
    ".omo/evidence/task-4-signoff-ui-flow-generated-ownership.txt",
    ".omo/evidence/task-4-signoff-ui-flow-focused-api-rerun.txt",
    ".omo/evidence/task-4-signoff-ui-flow-browser-rerun.txt",
    ".omo/evidence/task-4-signoff-ui-flow-cleanup-listeners.txt",
    ".omo/evidence/task-4-signoff-ui-flow-no-todo5-rg.txt",
    ".omo/evidence/task-4-signoff-ui-flow-owned-diff-name-status.txt",
    ".omo/start-work/notepad.md",
    ".omo/start-work/ledger.jsonl",
    ".omo/plans/signoff-ui-flow.md"
  ],
  repro: [
    "Inspected new blocker-clearing artifacts directly.",
    "Verified code-review artifact reports PASS with programming/type-safety and remove-ai-slops/overfit coverage.",
    "Verified manual QA matrix reports PASS rows for selector behavior, active action preservation, historical read-only behavior, malformed input, no Todo 5 bleed, tests/typecheck, and listener cleanup.",
    "Verified generated ownership artifact assigns dirty/stale web_dist bundle work to Todo 7, not Todo 4.",
    "Inspected raw rerun and grep artifacts supporting the matrix."
  ],
  findings: [
    "Previous blocker for missing independent code-review coverage is cleared by .omo/evidence/task-4-signoff-ui-flow-code-review.md.",
    "Previous blocker for missing manual QA matrix is cleared by .omo/evidence/task-4-signoff-ui-flow-manual-qa-matrix.md and referenced raw evidence.",
    "Previous blocker for generated bundle ownership is cleared by .omo/evidence/task-4-signoff-ui-flow-generated-ownership.txt; generated web_dist remains dirty/stale but is explicitly Todo 7-owned.",
    "Updated notepad now points at Todo 4 and records the new gate artifacts; ledger has matching gate-artifact events.",
    "No obvious contradiction found in the new artifacts. Browser rerun exit code 143 is consistent with dev-server cleanup after PASS, and cleanup-listeners shows no remaining listeners.",
    "No proofSummary or inspectMissionId bleed found in the Todo 4 source/test scope."
  ],
  confidence: 0.92
}

## Original Intent

Todo 4 adds mission history selection to the dashboard. The user should be able to inspect historical mission artifacts and timeline entries without changing the active mission or enabling historical edits.

## Desired Outcome

- Dashboard renders `overview.missions` as a compact mission selector.
- The default selected mission is the active mission.
- Selecting a historical mission updates only `ArtifactPanel` and `Timeline`.
- Top-level legal actions remain tied to the active mission.
- Historical mission artifacts are read-only.
- Todo 4 does not introduce Todo 5 fields such as `proofSummary` or `inspectMissionId`.
- Todo 4 does not implement a dirty-edit guard beyond necessary selection behavior.

## User Outcome Review

The previous blockers were artifact and ownership gaps, not failing Todo 4 behavior. The new artifacts close those gaps. The source/API behavior remains supported by the focused API rerun, browser QA rerun, typecheck/test evidence referenced by the matrix, and direct no-Todo-5 grep evidence. Todo 4 is safe to check off.

Generated packaged UI remains a known dirty/stale surface, but the plan, notepad, code-review artifact, manual QA matrix, and generated-ownership artifact consistently assign `apps/web/dist` and `src/signoff/web_dist` synchronization to Todo 7. That is not a Todo 4 blocker.

## Blockers

None.

## Checked Artifact Paths

- `.omo/plans/signoff-ui-flow.md`
- `.omo/start-work/notepad.md`
- `.omo/start-work/ledger.jsonl`
- `.omo/evidence/task-4-signoff-ui-flow-code-review.md`
- `.omo/evidence/task-4-signoff-ui-flow-manual-qa-matrix.md`
- `.omo/evidence/task-4-signoff-ui-flow-generated-ownership.txt`
- `.omo/evidence/task-4-signoff-ui-flow-focused-api-rerun.txt`
- `.omo/evidence/task-4-signoff-ui-flow-browser-rerun.txt`
- `.omo/evidence/task-4-signoff-ui-flow-cleanup-listeners.txt`
- `.omo/evidence/task-4-signoff-ui-flow-no-todo5-rg.txt`
- `.omo/evidence/task-4-signoff-ui-flow-owned-diff-name-status.txt`

## Exact Evidence Gaps

No blocking evidence gaps remain.

Non-blocking notes:
- Todo 4 remains unchecked in the plan pending this gate result; the reviewer was instructed not to edit plan checkboxes.
- Generated bundle dirtiness is documented as Todo 7-owned and must be resolved before packaged-build completion, not before Todo 4 checkoff.

## Adversarial Classes

- malformed_input: covered by manual QA matrix historical PUT 400 row.
- dirty_worktree: scoped owned diff matches Todo 4 source files; generated dirtiness documented as Todo 7-owned.
- stale_state: updated notepad and ledger now reflect the blocker-clearing artifacts.
- misleading_success_output: raw rerun, grep, browser, cleanup, code review, and matrix artifacts were inspected directly.
- flaky_tests: focused API rerun and typecheck/test evidence are present in the matrix; no contrary failure artifact found.
- cancel_resume: browser rerun terminated the dev server after PASS; cleanup artifact shows no listeners.
- hung_or_long_commands: no lingering listeners found.
- prompt_injection: N/A; no dangerous HTML surface was added by Todo 4.
