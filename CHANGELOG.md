# Changelog

Two axes, kept distinct:

- **Starter release** — this repo, on [SemVer](https://semver.org). Bump when the
  scaffold's own shape changes.
- **Cordon `schema_version`** — the contract revision the emitted JSON targets
  (currently `4`, schema `cordon-v4.json`). Tracked separately because a project
  can stay on the starter while the contract revs.

## 1.0.0 (2026-06-16)


### Features

* local git hooks — pre-commit blocks main, pre-push gates ([#3](https://github.com/joeseverino/cordon-starter/issues/3)) ([80fcd30](https://github.com/joeseverino/cordon-starter/commit/80fcd30456a035e4cba37ebbcc62652995aaf1e2))
* self-documenting cordon.checks.json + check.sh report() redesign ([#9](https://github.com/joeseverino/cordon-starter/issues/9)) ([a420db9](https://github.com/joeseverino/cordon-starter/commit/a420db9bdc69af3d539bbb74a24abde1f17d391c))
* single-source verification gate + commit-msg hook ([#4](https://github.com/joeseverino/cordon-starter/issues/4)) ([bcea631](https://github.com/joeseverino/cordon-starter/commit/bcea631970a3c067c3cbe4b98b76bc8080ed753c))
* validate against cordon itself via $CORDON_HOME (drop vendored schema) ([#5](https://github.com/joeseverino/cordon-starter/issues/5)) ([eca96e1](https://github.com/joeseverino/cordon-starter/commit/eca96e173f3d668425764a304860c816fe18830a))
* wire scripts/check.sh to cordon's repo-checks runner ([#7](https://github.com/joeseverino/cordon-starter/issues/7)) ([0233388](https://github.com/joeseverino/cordon-starter/commit/023338861e466a0c40d49732edc2c5aa72500430))


### Bug Fixes

* self-contained CI + hardened governance, add smoke test ([d3c0ed3](https://github.com/joeseverino/cordon-starter/commit/d3c0ed30ac052adae8a8325f31dd8e1e4157c482))

## [Unreleased]

### Changed
- **Checks engine model documented.** The `run_checks` gate step now runs
  cordon's full checks *engine*: built-in invariants plus this repo's own
  `commands[]` specs (a test suite, a type check, a bespoke audit — declared as
  data in `cordon.checks.json`, spec code stays home), folded into one verdict.
  Each check is capability-gated (`requires` git/macos/built-dir/`<binary>`, with
  `!` negation), so the scaffold is lean by default and skips fail-soft what the
  environment can't satisfy. `cordon.checks.json` ships an explicit `commands: []`
  (schema-autocompleted) alongside the off-by-default `idempotence`. See AGENTS.md
  → "Repo checks config" and CORNERSTONES.md → CI.

### Added
- Initial scaffold: Cordon emit-once example tool, CI conformance gate,
  `scripts/check.sh` pre-push gate, `scripts/setup-governance.sh` branch
  protection + security, AGENTS.md cornerstone playbook, optional design tokens.

  Targets Cordon `schema_version: 4`.
