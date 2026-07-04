recommendation: APPROVE
verdict: confirmed
confidence: 0.91

# Todo 6 Final Gate Review

## originalIntent

Todo 6 must prevent unsaved artifact edits from being silently lost when the user switches artifacts, missions, or the Artifacts/Timeline mission-record tab. The intended UX is to keep the current editable surface and show an inline warning, or allow navigation only after explicit Save or Discard. The change must not use `window.confirm`, autosave, dependency/router/page split, broad redesign, Todo 5 proof/server-contract changes, or Todo 7 generated-bundle rebuild claims.

## desiredOutcome

A user editing a draft artifact can try to click another artifact, another mission, or the Timeline tab without losing the current draft. Save still persists through the existing artifact save path. Discard remains an explicit user action.

## userOutcomeReview

The shipped Todo 6 source and evidence now satisfy the user-visible outcome:

- Dirty artifact switch is blocked and keeps the edited draft visible.
- Dirty mission switch is blocked and keeps the current mission/editor state.
- Dirty `Artifacts -> Timeline` tab switch is blocked, keeps the user on Artifacts, shows an inline warning, and preserves `TASK-6-TAB-SWITCH-DRAFT-MARKER`.
- Save still works before artifact switching.
- Discard explicitly clears the draft and then allows mission switching.

The prior tab-switch blocker is fixed by current browser evidence. The prior Dashboard file-size blocker is fixed by a cohesive presentational split: `Dashboard.tsx` is now 245 pure LOC and the extracted TSX components are all below 250 pure LOC.

## blockers

None.

## checkedArtifactPaths

- `/Users/termtek/Github/Signoff/AGENTS.md`
- `/Users/termtek/Github/Signoff/.omo/plans/signoff-ui-flow.md`
- `/Users/termtek/Github/Signoff/.omo/start-work/notepad.md`
- `/Users/termtek/Github/Signoff/.omo/start-work/ledger.jsonl`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-doneclaim.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-code-review.md`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-manual-qa-matrix.md`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-fix-doneclaim.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-manual-qa-addendum.md`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-editor.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-doneclaim.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-code-review.md`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-qa-addendum.md`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-loc.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-typecheck.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-api.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-diff-check.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-forbidden-grep.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-qa.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-listeners.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-addendum-gates.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-dashboard-split-addendum-listeners.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-generated-ownership.txt`
- `/Users/termtek/Github/Signoff/.omo/evidence/task-6-signoff-ui-flow-generated-status.txt`
- `/tmp/signoff-ui-flow-editor-qa.mjs`
- `/tmp/signoff-ui-flow-tab-switch-qa.mjs`

## sourcePathsChecked

- `/Users/termtek/Github/Signoff/apps/web/src/pages/Dashboard.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/components/ArtifactPanel.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/components/HeroPanel.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/components/ProofCard.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/components/NextActionCard.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/components/StartMissionCard.tsx`
- `/Users/termtek/Github/Signoff/apps/web/src/api.ts`
- `/Users/termtek/Github/Signoff/apps/web/src/styles.css`
- `/Users/termtek/Github/Signoff/package-lock.json`
- `/Users/termtek/Github/Signoff/src/signoff/web_dist/`
- `/Users/termtek/Github/Signoff/apps/web/dist/`

## directEvidence

- Plan checkbox precondition: Todo 6 is still pending in `.omo/plans/signoff-ui-flow.md`; Todo 7 is also pending.
- Typecheck rerun: `npm run typecheck` exited 0.
- API/conformance rerun: `python3 scripts/test.py` exited 0 with `Ran 35 tests` and `Conformance: 35/35 passed`.
- Scoped whitespace gate: `git diff --check -- apps/web/src/components/ArtifactPanel.tsx apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/StartMissionCard.tsx apps/web/src/styles.css` exited 0.
- File-size check rerun:
  - `apps/web/src/pages/Dashboard.tsx`: 245 pure LOC.
  - `apps/web/src/components/HeroPanel.tsx`: 56 pure LOC.
  - `apps/web/src/components/ProofCard.tsx`: 82 pure LOC.
  - `apps/web/src/components/NextActionCard.tsx`: 78 pure LOC.
  - `apps/web/src/components/StartMissionCard.tsx`: 37 pure LOC.
  - `apps/web/src/components/ArtifactPanel.tsx`: 155 pure LOC.
- Forbidden mechanism/source scan: no matches for `window.confirm`, bare `confirm(`, `window.prompt`, bare `prompt(`, autosave markers, `as any`, `: any`, `Record<string, any>`, `Array<any>`, `Promise<any>`, `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, or `type: ignore` in scoped UI/API files.
- Router/dependency check: no new router/page split in scoped files; existing router references are confined to pre-existing `apps/web/src/main.tsx` and existing package metadata.
- Dependency check: `git diff -- package.json apps/web/package.json --exit-code` is clean. `package-lock.json` has registry `resolved` URL churn only; no package name/version/integrity/dependency stanza changes were found.
- Listener check: no Signoff QA listeners on 5174, 5175, or 8765. Port 5173 currently has an unrelated `/Users/termtek/Github/vibe-seo` Vite process, so it is not a Todo 6 cleanup blocker.

## behaviorEvidence

- `.omo/evidence/task-6-signoff-ui-flow-editor.txt` reports:
  - `binaryObservable.artifactSwitchBlocked: true`
  - `binaryObservable.missionSwitchBlocked: true`
  - `binaryObservable.tabSwitchBlocked: true`
  - `binaryObservable.switchAfterSave: true`
  - `binaryObservable.switchMissionAfterDiscard: true`
  - `binaryObservable.savedAfterClick: true`
  - `result: PASS`
- `.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt` reports:
  - `binaryObservable.tabSwitchPreservedDraft: true`
  - `binaryObservable.timelineVisibleAfterClick: false`
  - `binaryObservable.warningCountAfterTimelineClick: 1`
  - `result: PASS`
- Screenshots `.omo/evidence/task-6-signoff-ui-flow-editor.png` and `.omo/evidence/task-6-signoff-ui-flow-tab-switch.png` are nonblank and show the expected editor surface; the tab-switch screenshot shows `TASK-6-TAB-SWITCH-DRAFT-MARKER` still in the editor with Save/Discard controls visible.
- The QA scripts drive a real browser against a temporary Signoff API server and Vite UI, inspect textareas, selected rows, mission buttons, timeline visibility, warning count, toolbar text, and screenshots. They are not deletion-only, tautological, or implementation-mirroring checks.

## scopeReview

- Todo 6-owned behavior source is limited to the artifact editor dirty state, parent Dashboard dirty guards, presentational Dashboard extraction, and CSS for the visible controls/warnings.
- No Todo 5 proof/server contract change is claimed by the Todo 6 post-fix artifacts. Existing `src/signoff/web.py`, `tests/test_web.py`, and `apps/web/src/api.ts` dirty state belongs to earlier Todo 5/proof work and is outside this Todo 6 verdict.
- No Todo 7 generated bundle rebuild is claimed. Generated `src/signoff/web_dist/**` and `apps/web/dist/**` dirt remains explicitly classified as Todo 7-owned in the generated ownership artifacts.
- The Dashboard split is cohesive and presentational: `Dashboard.tsx` keeps query/mutation, selected mission/tab state, dirty guard orchestration, and callbacks; extracted components render hero, proof, next-action/note, and start-mission sections without importing API/query state.

## removeAiSlopsProgrammingPass

Required skills consulted directly:

- `omo:remove-ai-slops`
- `omo:programming`
- `omo:programming` TypeScript reference

Direct pass result:

- Prior oversized-file blocker is resolved; no scoped TSX file remains above 250 pure LOC.
- No unnecessary production extraction/parsing/normalization was introduced by the split.
- No speculative abstraction found: each extracted component maps to one visible Dashboard section and receives explicit props.
- No duplicate client action policy found: `Dashboard.tsx` still owns action orchestration; `NextActionCard` renders callbacks.
- No new dependency, router/page split, compatibility shim, autosave, modal confirm, broad redesign, deletion-only test, tautological test, or implementation-mirroring test found.
- The code review report explicitly includes programming/type-safety and remove-ai-slops/overfit coverage, and its coverage is supported by direct source and evidence inspection.

## exactEvidenceGaps

None for Todo 6. Remaining generated bundle sync and final real-surface verification are Todo 7/final-wave work by plan.

## conclusion

Todo 6 is safe to check off. The user-visible dirty-edit loss behavior is covered across artifact switch, mission switch, tab switch, Save, and Discard; the prior tab-switch and file-size blockers are fixed; scoped gates pass; and no remaining Todo 6 blocker was found.
