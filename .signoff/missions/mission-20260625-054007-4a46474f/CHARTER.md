# Mission Charter

- Mission: `mission-20260625-054007-4a46474f`
- Exact user outcome (immutable):

> Make contributor UI first-run install reproducible from the public npm lockfile, keep generated outputs ignored, and ensure Signoff patch receipts exclude control artifacts

## User-visible success

A fresh contributor can clone the repository, run the public npm lockfile path, typecheck the UI, and produce the UI build without private registry URLs or untracked generated dependency/build/cache noise. Signoff receipts for the slice show only the authorized product patch and exclude `.signoff` control artifacts.

## Hard constraints

- Preserve the one-path non-technical install experience.
- Keep Python runtime dependencies at zero.
- Do not change UI behavior, package manager, install flow, protocol semantics, services, or agent quorum.
- Do not weaken any Signoff gate; add an adversarial conformance test before changing receipt behavior.
- Keep the implementation bounded to repository metadata, receipt path filtering, and the matching regression test.

## Non-goals

- UI redesign or frontend feature work.
- New package managers, services, provider routing, Docker, databases, authentication, or cloud infrastructure.
- Broad cleanup, formatting churn, dependency upgrades, or version changes.
- Changing reviewer, Council, Roast, lock, or finish semantics beyond keeping generated receipts scoped to product files.

## Stop / pivot conditions

- Stop if public npm install remains blocked by external registry/network state after lockfile normalization.
- Pivot if receipt correctness requires a protocol semantic change rather than applying existing control-path filtering consistently.
- Stop if verification requires private credentials, private registries, or generated/ignored outputs to be committed.
- Stop if the patch would need to touch files outside the contract.

## Evidence standard

- `npm ci`
- `npm run typecheck`
- `npm run build:web`
- `python3 scripts/test.py`
- `python3 scripts/check_repo.py`
- Scope/status evidence that generated dependency/build/cache outputs are ignored.
- A conformance test proving sealed `PATCH.diff` excludes `.signoff` control artifacts.
