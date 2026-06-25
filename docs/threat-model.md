# Threat model

## Protected properties

Signoff aims to make these failures detectable:

- the user's goal or acceptance criteria change silently;
- implementation escapes the authorized file/line budget;
- a builder counts as its own reviewer or judge;
- multiple alleged reviewers are the same recorded context;
- advisors answer different decision questions;
- disagreement closes by popularity rather than evidence;
- prose claims tests passed when commands did not run or failed;
- verification changes the patch after evidence collection began;
- findings disappear from the lead judgment;
- receipts or ledger records are edited afterward;
- a non-cumulative slice is declared final.

## In-scope adversaries

- accidental or model-induced drift;
- eager adjacent cleanup;
- optimistic self-review;
- malformed/fabricated artifact fields detectable from local metadata;
- casual post-hoc editing of artifacts;
- mid-iteration Git commits that would hide a diff from a naive `HEAD` comparison.

## Out-of-scope adversaries

A process with arbitrary local access can patch the runtime, rewrite Git objects, forge provider/context metadata, intercept commands, or replace the interpreter. Local Signoff is tamper-evident, not a secure enclave.

The runtime also cannot prove that two external model calls were psychologically independent; it validates distinct asserted context identities and honest host behavior. Provider-signed call receipts are a possible future extension.

## Command execution

Contract commands are executable code. Signoff uses argument arrays and `shell=False`, but an explicitly selected shell binary can still execute arbitrary shell input. Run untrusted repositories in an OS/container sandbox with restricted secrets and network.

## Hidden tests

Hidden evaluators stored in the same writable filesystem are not hidden from a sufficiently capable agent. Strong benchmark secrecy requires evaluator separation after the agent process exits.

## Privacy

Prompts, model outputs, patches, and command outputs may contain sensitive data. Do not include secrets. A production hosted version should offer redaction, configurable retention, encryption, and organization policy.
