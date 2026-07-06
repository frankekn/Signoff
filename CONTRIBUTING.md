# Contributing

Traction is alpha software. Contributions should make one invariant clearer, more enforceable, or easier to use.

## Development

Runtime-only changes:

```sh
python3 scripts/test.py
python3 scripts/check_repo.py
```

UI changes:

```sh
npm ci
npm run typecheck
npm run build:web
python3 scripts/test.py
python3 scripts/check_repo.py
```

The runtime must remain Python 3.10+ standard-library-only unless a proposal demonstrates that a dependency materially improves the one-path installation experience. End users must not need Node.js; commit the rebuilt packaged UI under `src/traction/web_dist/`.

## Protocol changes

A protocol change needs:

1. the failure mode it prevents;
2. why a prompt-only instruction is insufficient;
3. a deterministic adversarial test that fails before the change;
4. migration and compatibility impact on stored artifacts;
5. an honest claim boundary.

Do not weaken a gate only to make an agent transcript proceed. `STOPPED`, `PIVOT`, and `BLOCKED` are valid outcomes.

## Pull requests

Keep changes bounded. Include tests, update linked docs and schemas, and preserve the mirrored packaged skills under `src/traction/assets/skills/`.

By contributing, you agree that your contribution is licensed under Apache-2.0.
