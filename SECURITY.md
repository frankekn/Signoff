# Security policy

## Reporting

Report suspected vulnerabilities privately through the repository's GitHub security advisory feature. Do not include secrets, private repositories, or proprietary model outputs in a public issue.

## Supported version

The latest alpha release is supported on a best-effort basis. There is no production security SLA yet.

## Important boundary

Traction executes repository-declared verification commands and shares a filesystem with the coding agent. Treat those commands as code and use an OS or container sandbox for untrusted repositories.

The UI binds to `127.0.0.1` by default and has no authentication. Do not expose it to a network without an external authenticated reverse proxy and sandbox boundary.

Traction is tamper-evident, not a secure enclave. A process with arbitrary local access can patch the runtime, rewrite Git objects, forge provider/context metadata, or replace the interpreter. Strong hidden-test secrecy and trustworthy identity attestation require a separately isolated evaluator.

See [`docs/threat-model.md`](docs/threat-model.md).
