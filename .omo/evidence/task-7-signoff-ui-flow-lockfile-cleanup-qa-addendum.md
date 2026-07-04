# Todo 7 Lockfile Cleanup QA Addendum

DoneClaim: Todo 7 package-lock cleanup did not change the Todo 7 generated UI ownership or release-surface proof.

Verdict: PASS. No blockers found.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| LC-S1 | package-lock clean after cleanup | CLI git path filter | `git status --short -- package-lock.json` | PASS | LC-AR1, LC-AR6 |
| LC-S2 | generated asset diff still Todo 7-owned | CLI git path filter | `git status --short -- apps/web/dist src/signoff/web_dist` | PASS | LC-AR2, LC-AR7 |
| LC-S3 | typecheck after cleanup PASS | CLI | `npm run typecheck 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-typecheck-rerun.txt` | PASS | LC-AR3, LC-AR8 |
| LC-S4 | check_repo after cleanup PASS | CLI | `python3 scripts/check_repo.py 2>&1 \| tee .omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-check-rerun.txt` | PASS | LC-AR4, LC-AR9 |
| LC-S5 | generated asset refs still exist | CLI data audit | `node <<'NODE' ... NODE \| tee .omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-generated-refs-rerun.txt` | PASS | LC-AR5, LC-AR10 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| LC-A1 | package-lock clean after cleanup | unrelated lockfile churn reintroduced | `package-lock.json` must not appear in `git status --short` after cleanup. | PASS | LC-AR1, LC-AR6 |
| LC-A2 | generated asset diff still Todo 7-owned | generated bundle churn misclassified as unrelated | Remaining generated bundle adds/removals must match the Todo 7 ownership report. | PASS | LC-AR2, LC-AR7 |
| LC-A3 | typecheck after cleanup PASS | cleanup broke TypeScript build | `npm run typecheck` must exit 0 after cleanup. | PASS | LC-AR3, LC-AR8 |
| LC-A4 | check_repo after cleanup PASS | cleanup broke repository policy gate | `python3 scripts/check_repo.py` must exit 0 after cleanup. | PASS | LC-AR4, LC-AR9 |
| LC-A5 | generated asset refs still exist | stale generated HTML references missing assets | Every `/assets/...` reference in both generated `index.html` files must resolve to an existing file. | PASS | LC-AR5, LC-AR10 |

## manualQa.artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| LC-AR1 | CLI transcript | Fresh package-lock path-filter audit; records PASS with no `package-lock.json` status output. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-package-lock-clean.txt` |
| LC-AR2 | CLI transcript | Fresh generated path-filter audit showing only Todo 7 rebuilt packaged UI generated files. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-generated-diff.txt` |
| LC-AR3 | CLI transcript | Fresh `npm run typecheck` rerun after cleanup; command exited 0. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-typecheck-rerun.txt` |
| LC-AR4 | CLI transcript | Fresh `python3 scripts/check_repo.py` rerun after cleanup; command exited 0. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-check-rerun.txt` |
| LC-AR5 | CLI data audit transcript | Fresh generated HTML asset-reference audit for `apps/web/dist` and `src/signoff/web_dist`; records PASS. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-generated-refs-rerun.txt` |
| LC-AR6 | Existing CLI transcript | Preexisting package-lock cleanup status showing no package-lock diff and the expected generated status. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-status.txt` |
| LC-AR7 | Existing ownership report | Todo 7 generated/release-surface ownership report classifying the rebuilt generated files as Todo 7-owned. | `.omo/evidence/task-7-signoff-ui-flow-generated-ownership.txt` |
| LC-AR8 | Existing CLI transcript | Preexisting post-cleanup `npm run typecheck` transcript. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-typecheck.txt` |
| LC-AR9 | Existing CLI transcript | Preexisting post-cleanup `python3 scripts/check_repo.py` transcript. | `.omo/evidence/task-7-signoff-ui-flow-lockfile-cleanup-check.txt` |
| LC-AR10 | Existing data audit transcript | Preexisting Todo 7 generated asset reference audit with `result: PASS`. | `.omo/evidence/task-7-signoff-ui-flow-generated-status.txt` |

## Blockers

None.
