# Lead judgment

The lead judge is a fresh context distinct from the builder and counted reviewers. It does not edit the patch.

The judge must:

1. decide every active acceptance ID;
2. account for every finding exactly once;
3. preserve `ACT_ON`, `CONSIDER`, `NOTED`, `DISMISSED`, or `OUT_OF_SCOPE` explicitly;
4. cite passed evidence before dismissing critical/high findings;
5. turn material reviewer conflict into a discriminating experiment or cite existing evidence, locked spec, or explicit user decision;
6. never use vote, majority, confidence, consensus, authority, or model brand as arbitration;
7. emit `PASS`, `REWORK`, or `BLOCKED` in `JUDGMENT.json`.

A unanimous opinion cannot override a failed command, wrong artifact hash, scope breach, or patch mutation.
