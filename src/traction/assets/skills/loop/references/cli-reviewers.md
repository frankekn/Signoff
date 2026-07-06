# Reviewer transport adapters

Model names and CLI flags are volatile. Keep them out of the loop Pull protocol.

Use any host mechanism that can provide real fresh read-only contexts. For each counted reviewer, record the actual provider, model, participant ID, and context ID in the generated review file. The builder's current context never counts as a reviewer.

Before relying on a CLI adapter:

1. check that the command exists;
2. check its current help/version output;
3. enforce read-only filesystem/tool permissions where the host supports them;
4. pass the same sealed contract, evidence, patch, and hashes;
5. capture only the reviewer's own output;
6. do not claim diversity or independence that the host cannot establish.

If fewer than two fresh contexts return substantive complete reviews, the honest result is insufficient review quorum. Do not substitute personas within one context.

Dispatch all reviewers in parallel per `fanout-protocol.md`.
