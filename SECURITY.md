# Security

## Reporting

Found something? Open a private security advisory on the repo (Security →
Advisories → "Report a vulnerability"), or email the address on the GitHub
profile. Don't file a public issue for a vulnerability.

## What this scaffold gives a repo

- **CI conformance gate** — the emitted Cordon contract must validate against
  cordon's own schema, referenced via `$CORDON_HOME` (never vendored), on every
  push and PR.
- **Branch protection** (`scripts/setup-governance.sh`) — `main` merges require a
  green `ci` check and resolved conversations; force-push and deletion are off.
- **Repo security settings** — vulnerability alerts and automated security fixes
  are turned on by the same script.

## What it does NOT do

It does not add a static-analysis scanner. Security-focused repos (a plugin,
detection engine, scanner) should add one and surface its badge — Semgrep for
PHP/WordPress, CodeQL where supported. A plain CLI stays lint-only. See
`docs/CORNERSTONES.md`.

## Effect is the security signal

Every command declares an `effect`
(`read < local_write < vault_write < remote_write < deploy`). It is the one fact
a flag can't tell you: what happens if this runs. Declare it honestly — a
consumer (a runtime gate, an AI session) risk-gates on it before acting. A
`deploy` mislabeled `read` defeats the gate.
