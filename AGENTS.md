# Repository instructions

This repository implements Traction itself.

- Run `python3 scripts/test.py` after runtime, schema, installer, or skill changes.
- Run `python3 scripts/check_repo.py` before committing.
- Keep runtime dependencies at zero.
- Keep top-level skills mirrored exactly under `src/traction/assets/skills/`.
- Add an adversarial test before relaxing or adding a protocol gate.
- Do not claim real-agent efficacy from the conformance suite.
- Preserve the one-path non-technical installation experience.
