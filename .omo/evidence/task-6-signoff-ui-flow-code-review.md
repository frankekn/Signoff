PASS

# Todo 6 Code Review

codeQualityStatus: WATCH
recommendation: APPROVE
reportPath: .omo/evidence/task-6-signoff-ui-flow-code-review.md
blockers: none

DoneClaim reviewed: `Todo 6 blocker fix - Prevent dirty artifact loss across artifact and mission tab switches`.

## Post-Fix Re-Review Final Verdict

The previous blocker is fixed for the reviewed Todo 6 behavior. A dirty `CHARTER.md` draft is no longer silently lost when clicking `Artifacts -> Timeline -> Artifacts`: the tab switch is blocked, the selected tab remains `Artifacts`, the draft marker remains in the textarea, and inline dirty warnings are visible.

Scope caveat: the current worktree still contains broader UI-flow changes, including `src/signoff/web.py`, `src/signoff/runtime.py`, and `src/signoff/web_dist/**`. I did not treat those as part of the post-fix Dashboard claim because the fix DoneClaim is scoped to `apps/web/src/pages/Dashboard.tsx`, and the direct review found the tab-switch fix itself did not require server/proof contracts, generated bundles, dependencies, routing, autosave, or modal confirms. A full-worktree Todo 7/release review still needs to own the generated bundle state.

## Findings By Severity

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

- `apps/web/src/pages/Dashboard.tsx:65` is 373 pure LOC, above the `omo:programming` 250 pure-LOC ceiling. This is existing cumulative UI-flow debt, not a blocker for this narrow tab-switch fix: splitting Dashboard here would be a broad refactor outside Todo 6.
- `apps/web/src/components/ArtifactPanel.tsx:5`, `apps/web/src/components/ArtifactPanel.tsx:11`, and `apps/web/src/components/ArtifactPanel.tsx:27` still have implicit return types on existing functions/components. The new Todo 6 handlers have explicit `: void` returns, and `tsc` passes, so this remains type-discipline debt rather than a blocker for the post-fix review.

## Behavior Checks

- Tab switch dirty guard: PASS. `selectTab` blocks before `setTab` when `artifactDirty` is true at `apps/web/src/pages/Dashboard.tsx:151`, and the segmented buttons route through it at `apps/web/src/pages/Dashboard.tsx:385`.
- User stays on Artifacts: PASS. The stdout-only browser probe reported `activeTabAfterTimelineClick: "Artifacts"` and `timelineVisibleAfterDirtyClick: false`.
- Inline warning appears: PASS. The workspace warning renders at `apps/web/src/pages/Dashboard.tsx:390`; the browser probe reported `warningCountAfterTimelineClick: 2`.
- Draft marker remains visible: PASS. The browser probe reported `markerVisibleAfterTabClick: true`.
- Dirty artifact row switch still blocks: PASS. `selectArtifact` blocks on a different path while dirty at `apps/web/src/components/ArtifactPanel.tsx:85`; the browser probe reported `artifactSwitchBlocked: true`.
- Dirty mission switch still blocks: PASS. `selectMission` blocks while dirty at `apps/web/src/pages/Dashboard.tsx:142`; the browser probe reported `missionSwitchBlocked: true`.
- Save still uses the existing PUT path: PASS. `ArtifactPanel` calls `api.saveArtifact(selectedPath, draft)` at `apps/web/src/components/ArtifactPanel.tsx:71`, and `api.saveArtifact` still uses `PUT /api/artifact` at `apps/web/src/api.ts:146`.
- Discard is explicit: PASS. `Discard draft` is a visible button wired to `discardDraft` at `apps/web/src/components/ArtifactPanel.tsx:93` and `apps/web/src/components/ArtifactPanel.tsx:131`; the browser probe reported `switchMissionAfterDiscard: true`.
- No `window.confirm`, no autosave, no router/dependency redesign: PASS. Scoped grep found no forbidden matches in the reviewed UI/API files, and no package dependency was needed for the post-fix guard.

## Skill-Perspective Check

Skill-perspective check ran before judging tests and maintainability:

- Loaded `omo:remove-ai-slops`.
- Loaded `omo:programming`.
- Loaded `omo:programming` TypeScript reference.

Remove-ai-slops result: no Todo 6 blocker found. The fix is one local dirty-state gate in the parent tab switch path, with no new abstraction, compatibility shim, dependency, router, autosave, modal confirm, generated source edit, deletion-only test, tautological test, or implementation-constant-only test.

Programming result: WATCH, not BLOCK. The new handlers are typed (`selectTab`, `selectMission`, `updateArtifactDirty`, `selectArtifact`, `discardDraft`), no `any`/`as any`/suppression was found in the scoped search, and TypeScript passes. The perspective does flag the oversized Dashboard file as debt, recorded above under LOW.

## Verification

Commands inspected/run:

- `sed -n '1,260p' /Users/termtek/Github/Signoff/AGENTS.md`
- `rg -n "Todo 6|dirty artifact|artifact switch|mission switch|tab|Artifacts|Timeline|dirty" .omo/plans/signoff-ui-flow.md`
- `sed -n '1,260p' .omo/evidence/task-6-signoff-ui-flow-gate-review.md`
- `sed -n '1,260p' .omo/evidence/task-6-signoff-ui-flow-fix-doneclaim.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-tab-switch-red.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-tab-switch.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-api.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-diff-check.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-forbidden-grep.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-listeners.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-no-excuse.txt`
- `sed -n '1,220p' .omo/evidence/task-6-signoff-ui-flow-fix-typecheck.txt`
- `git status --short`
- `git diff --stat`
- `git diff --name-only`
- `git diff -- apps/web/src/pages/Dashboard.tsx apps/web/src/components/ArtifactPanel.tsx apps/web/src/styles.css apps/web/src/api.ts`
- `nl -ba apps/web/src/pages/Dashboard.tsx`
- `nl -ba apps/web/src/components/ArtifactPanel.tsx`
- `nl -ba apps/web/src/api.ts`
- `sed -n '1,260p' /tmp/signoff-ui-flow-tab-switch-qa.mjs`
- `sed -n '1,320p' /tmp/signoff-ui-flow-editor-qa.mjs`
- `rg -n "window\\.confirm|\\bconfirm\\(|window\\.prompt|autosave|auto-save|@ts-ignore|@ts-expect-error|eslint-disable|as any|:\\s*any\\b|Promise<any>|Array<any>|Record<string, any>" apps/web/src/components/ArtifactPanel.tsx apps/web/src/pages/Dashboard.tsx apps/web/src/styles.css apps/web/src/api.ts` (exit 1, no matches)
- `git diff --check -- apps/web/src/components/ArtifactPanel.tsx apps/web/src/pages/Dashboard.tsx apps/web/src/styles.css` (PASS)
- `./node_modules/.bin/tsc --noEmit --pretty false -p apps/web/tsconfig.json` (PASS)
- `python3 scripts/test.py` (PASS, 35/35 conformance)
- stdout-only Playwright dirty-switch matrix derived from `/tmp/signoff-ui-flow-editor-qa.mjs` without writing evidence files (PASS: `artifactSwitchBlocked=true`, `tabSwitchBlocked=true`, `missionSwitchBlocked=true`, `markerVisibleAfterTabClick=true`, `switchAfterSave=true`, `switchMissionAfterDiscard=true`, `savedAfterClick=true`)
- `lsof -nP -iTCP:5176 -sTCP:LISTEN; lsof -nP -iTCP:5177 -sTCP:LISTEN; lsof -nP -iTCP:8765 -sTCP:LISTEN` (no listeners)

## Remaining Blockers

None.
