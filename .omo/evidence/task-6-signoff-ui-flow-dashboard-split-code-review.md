PASS

# Dashboard Split Code Review

codeQualityStatus: WATCH
recommendation: APPROVE
reportPath: .omo/evidence/task-6-signoff-ui-flow-dashboard-split-code-review.md
blockers: []

## DoneClaim Reviewed

DoneClaim: Todo 6 gate blocker fix - Split oversized Dashboard component without changing dirty artifact behavior.

The claim is supported for the scoped Dashboard extraction. `Dashboard.tsx` is now below the 250 pure-LOC gate, the new component files are below the gate, dirty-protection ownership remains in the Dashboard/ArtifactPanel flow, and the rerun gates passed.

WATCH only because the broader worktree still contains unrelated dirty/generated and lockfile metadata changes. I did not treat those as blockers for this scoped extraction, but they must stay out of a Todo 6 source-only commit unless intentionally owned by a later Todo 7 build step.

## Severity Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

1. Broader worktree scope noise remains outside the scoped Dashboard split.
   - `git status --short` still shows dirty generated bundle files under `src/signoff/web_dist/**`, a modified `package-lock.json`, and other unrelated source/test files.
   - `git diff -- package.json apps/web/package.json --exit-code` is clean, and a package-lock scan found no package name/version/integrity/dependency stanza changes; the lockfile diff appears to be `resolved` URL churn only.
   - `git diff -- src/signoff/web_dist apps/web/dist` confirms generated bundle changes exist in the current worktree. This review accepts the Dashboard split only; Todo 7 still owns generated bundle regeneration.

## Pure LOC Gate

Command:

```sh
for f in apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/StartMissionCard.tsx apps/web/src/components/ArtifactPanel.tsx; do printf '%s ' "$f"; awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#|--)/' "$f" | wc -l; done
```

Result:

```text
apps/web/src/pages/Dashboard.tsx 245
apps/web/src/components/HeroPanel.tsx 56
apps/web/src/components/ProofCard.tsx 82
apps/web/src/components/NextActionCard.tsx 78
apps/web/src/components/StartMissionCard.tsx 37
apps/web/src/components/ArtifactPanel.tsx 155
```

The same pure LOC method from the prior REJECT is now green for the scoped Dashboard split and the related editor component.

## Presentational Split Review

Confirmed: the extracted components are presentational and cohesive.

- `Dashboard.tsx:37` still owns the page component.
- `Dashboard.tsx:39-47` still owns goal, selected tab, copied state, note state, selected mission state, artifact dirty state, and dirty warning state.
- `Dashboard.tsx:49-87` still owns overview query, mission creation mutation, and action mutation.
- `Dashboard.tsx:89-141` still owns action orchestration, note orchestration, dirty callback, mission switching guard, and tab switching guard.
- `Dashboard.tsx:181-260` passes typed values and callbacks into extracted components; no extracted component imports `api`, `useQuery`, `useMutation`, or owns query/mutation state.
- `ArtifactPanel.tsx:27-98` owns local artifact selection, draft, dirty path, save, and discard behavior, and reports dirty state upward through `onDirtyChange`.

The split did not introduce a router/page split. Existing router setup remains in `apps/web/src/main.tsx`, and no new router usage appears in the scoped component files.

## Dirty Protection Review

Confirmed by source and evidence:

- Artifact switch: `ArtifactPanel.tsx:85-92` blocks switching when `dirtyPath` points at a different artifact, and `.omo/evidence/task-6-signoff-ui-flow-editor.txt` reports `artifactSwitchBlocked: true`.
- Mission switch: `Dashboard.tsx:125-132` blocks mission changes while `artifactDirty` is true, and the editor evidence reports `missionSwitchBlocked: true`.
- Artifacts -> Timeline tab switch: `Dashboard.tsx:134-141` blocks tab changes while dirty, and `.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt` reports `tabSwitchPreservedDraft: true`, `timelineVisibleAfterClick: false`, and `warningCountAfterTimelineClick: 1`.
- Save: `ArtifactPanel.tsx:70-80` still calls `api.saveArtifact(selectedPath, draft)`, and `apps/web/src/api.ts:146-150` still uses `PUT /api/artifact`.
- Discard: `ArtifactPanel.tsx:93-98` explicitly resets the draft from the current artifact query and clears dirty state; the editor evidence reports `switchMissionAfterDiscard: true`.

## Scope Review

Confirmed for the scoped Dashboard extraction:

- No new dependency or manifest change: `git diff -- package.json apps/web/package.json --exit-code` returned 0.
- No new router/page split in the scoped component source.
- No server/proof contract changes are part of the named Dashboard split source files.
- No generated bundle work is required for this extraction; however generated bundle files are dirty in the broader worktree and remain a Todo 7 concern.

## TypeScript Review

Confirmed:

- No `any`, `as any`, `Record<string, any>`, `Array<any>`, `Promise<any>`, `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `type: ignore`, `window.confirm`, `confirm(`, `window.prompt`, `prompt(`, or `autosave` matches in the scoped UI/API files.
- New components use type-only imports for React/API types where appropriate.
- New components and helper functions have explicit return types:
  - `HeroPanel.tsx:15`, `HeroPanel.tsx:24`, `HeroPanel.tsx:29`, `HeroPanel.tsx:34`
  - `ProofCard.tsx:9`, `ProofCard.tsx:14`, `ProofCard.tsx:21`, `ProofCard.tsx:27`
  - `NextActionCard.tsx:20`, `NextActionCard.tsx:35`, `NextActionCard.tsx:40`
  - `StartMissionCard.tsx:11`, `StartMissionCard.tsx:12`, `StartMissionCard.tsx:17`
- `npm run typecheck` rerun passed.

## remove-ai-slops / programming Skill Perspective

Skill-perspective check ran. I loaded:

- `omo:remove-ai-slops` skill
- `omo:programming` skill
- `omo:programming` TypeScript reference

Result:

- No oversized scoped TSX file remains above 250 pure LOC.
- No deletion-only, tautological, implementation-mirroring, or removal-only tests were introduced by this split.
- No speculative abstraction found: each extracted component maps to one visible dashboard section.
- No duplicate client action policy found: `api.action` stays in `Dashboard.tsx`; `NextActionCard` only renders callbacks.
- No untyped loose prop bag found: props are explicit typed objects. `HeroPanel` receives the existing `Record<string, unknown>` `current` status field, but it is a single existing API-shaped value, not a catch-all prop bag.
- No unnecessary production data extraction/parsing/normalization added by the split.

No violation of either skill perspective blocks approval.

## Evidence Inspected

- `AGENTS.md`
- `.omo/plans/signoff-ui-flow.md`
- `.omo/evidence/task-6-signoff-ui-flow-gate-review.md`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-doneclaim.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-loc.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-typecheck.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-api.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-diff-check.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-forbidden-grep.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-qa.txt`
- `.omo/evidence/task-6-signoff-ui-flow-dashboard-split-listeners.txt`
- `.omo/evidence/task-6-signoff-ui-flow-editor.txt`
- `.omo/evidence/task-6-signoff-ui-flow-tab-switch.txt`
- `apps/web/src/pages/Dashboard.tsx`
- `apps/web/src/components/HeroPanel.tsx`
- `apps/web/src/components/ProofCard.tsx`
- `apps/web/src/components/NextActionCard.tsx`
- `apps/web/src/components/StartMissionCard.tsx`
- `apps/web/src/components/ArtifactPanel.tsx`
- `apps/web/src/api.ts`

## Commands Inspected / Run

```sh
sed -n '1,240p' /Users/termtek/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/remove-ai-slops/SKILL.md
sed -n '1,260p' /Users/termtek/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/SKILL.md
sed -n '1,260p' /Users/termtek/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/references/typescript/README.md
git status --short
git diff --stat -- apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/StartMissionCard.tsx apps/web/src/components/ArtifactPanel.tsx package.json package-lock.json apps/web/package.json src/signoff/web_dist apps/web/dist
git diff -- apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/StartMissionCard.tsx apps/web/src/components/ArtifactPanel.tsx
git diff -- package.json apps/web/package.json --exit-code
git diff -- package-lock.json
git diff -- src/signoff/web_dist apps/web/dist
rg -n "Record<string, any>|Array<any>|Promise<any>|: any\b|as any|unknown as|as unknown|@ts-ignore|@ts-expect-error|eslint-disable|type: ignore|window\.confirm|\bconfirm\(|window\.prompt|\bprompt\(|autosave" apps/web/src/pages/Dashboard.tsx apps/web/src/components/HeroPanel.tsx apps/web/src/components/ProofCard.tsx apps/web/src/components/NextActionCard.tsx apps/web/src/components/StartMissionCard.tsx apps/web/src/components/ArtifactPanel.tsx apps/web/src/api.ts
rg -n "router|BrowserRouter|createBrowserRouter|Route|Routes|react-router|@tanstack/router|from ['\"]react-router|from ['\"]@.*router" apps/web/src package.json apps/web/package.json
fd 'AGENTS\.md|CLAUDE\.md|frontend\.md' apps apps/web apps/web/src apps/web/src/components apps/web/src/pages -a
npm run typecheck
python3 scripts/test.py
```

## Verdict

APPROVE for the scoped Dashboard component extraction. No blockers remain for the Todo 6 file-size gate fix.
