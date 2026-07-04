# signoff-ui-flow Start-Work Notepad

## Active Work
- Plan: `.omo/plans/signoff-ui-flow.md`
- Boulder state: `.omo/boulder.json`
- Ledger: `.omo/start-work/ledger.jsonl`
- Current checkbox: Final verification wave F1-F4.
- Tier: HEAVY, because final verification audits the whole diff, packaged UI QA, and scope fidelity before completion.

## Completed Checkboxes
- Todo 1: confirmed and checked.
- Todo 2: confirmed and checked.
- Todo 3: confirmed and checked.
- Todo 4: confirmed and checked.
- Todo 5: confirmed and checked.
- Todo 6: confirmed and checked.
- Todo 7: confirmed and checked.

## Current Checkbox
- Final verification wave F1-F4: plan compliance, code quality, real manual QA, and scope fidelity.
- First final wave rejected; repair workers completed and F1-F4 must be rerun.
- F1/F2 blockers: `src/signoff/web.py` and `tests/test_web.py` crossed the programming/remove-ai-slops file-size gate.
- F3 blockers: packaged DONE proof must visibly expose final receipt hash proof; inspecting historical missions must keep the active DONE start-next-mission affordance visibly active-scoped.
- F4 blockers: out-of-scope untracked `PRODUCT.md` and `apps/web/.impeccable/live/config.json` must be explicitly excluded/handled before final scope approval.
- Scope decision: `PRODUCT.md` and `apps/web/.impeccable/**` are local/tool artifacts outside this plan. Keep them uncommitted and exclude from final staging; do not treat them as product patch evidence.

## Dirty Worktree Scope Note
- Pre-existing or unrelated dirty/generated files were present before Todo 1 orchestration, including generated `src/signoff/web_dist/**` assets and other UI polish changes from earlier work.
- Todo 1 scope was limited to `src/signoff/runtime.py`, `src/signoff/web.py`, `tests/test_web.py`, and `apps/web/src/api.ts`.
- Todo 2 scope was limited to `apps/web/src/components/PhaseRail.tsx`, `apps/web/src/pages/Dashboard.tsx`, and `apps/web/src/styles.css`.
- Todo 3 scope was limited to `apps/web/src/pages/Dashboard.tsx` and `apps/web/src/styles.css`.
- Todo 4 scope is limited to `src/signoff/web.py`, `tests/test_web.py`, `apps/web/src/pages/Dashboard.tsx`, and `apps/web/src/styles.css`.
- Todo 5 scope was limited to `src/signoff/web.py`, `tests/test_web.py`, `apps/web/src/api.ts`, `apps/web/src/pages/Dashboard.tsx`, and `apps/web/src/styles.css`.
- Todo 6 scope is limited to `apps/web/src/components/ArtifactPanel.tsx`, `apps/web/src/pages/Dashboard.tsx`, and `apps/web/src/styles.css`.
- Todo 6 also extracted Dashboard presentation sections into `apps/web/src/components/HeroPanel.tsx`, `ProofCard.tsx`, `NextActionCard.tsx`, and `StartMissionCard.tsx` to close the file-size gate without changing behavior.
- Generated bundle changes were rebuilt through `npm run build:web` and confirmed by Todo 7 gate.
