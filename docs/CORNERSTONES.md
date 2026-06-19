# Cornerstones

The standing standards every Severino repo carries. One line each; the why lives
in the vault. This is the checklist `cordon-starter` exists to satisfy.

## Command surface

- [ ] Every CLI surface renders from one `describe_spec()` — no hand-written help.
- [ ] `<tool> --describe` emits a valid Cordon v4 contract; `-h` renders from the
      same spec. They cannot drift.
- [ ] Every tool/command declares an honest `effect`
      (`read < local_write < vault_write < remote_write < deploy`), plus
      `+network` / `+interactive` when true.
- [ ] The `describe.sh` emitter is **sourced** from `"$TOOLS_HOME/lib/describe.sh"`,
      not copied into the repo.
- [ ] The schema + validator come from cordon via `$CORDON_HOME` (referenced,
      not vendored); CI checks out the public cordon repo to provide it.
- [ ] The committed `contract/*.json` golden matches the live `--describe`
      (drift checked by `scripts/check.sh`).
- [ ] The README's command reference is *rendered* from `contract/*.json` by
      `scripts/gen-readme.mjs`, never hand-kept; `scripts/check.sh` runs
      `--check` so a drifted block fails CI.

## Git workflow

- [ ] Never commit to `main`. Branch from a freshly fetched `origin/main`:
      `git fetch origin && git checkout -b <feature> origin/main`.
- [ ] One feature = one branch name, if multipe features are arising, increasing the branch scope is justified and renaming, reused across repos when it spans them.
- [ ] Solo-authored: no `Co-Authored-By`, no AI attribution in commits or PRs.
- [ ] Hand back only on green CI with zero unresolved PR comments.
- [ ] Local hooks make it stick even offline: `scripts/setup-hooks.sh` sets
      `core.hooksPath=.githooks` — `pre-commit` blocks `main`, `commit-msg`
      rejects AI attribution, `pre-push` runs `scripts/check.sh`. Bypass:
      `ALLOW_MAIN_COMMIT=1` / `git … --no-verify`.

## GitHub governance (`scripts/setup-governance.sh`)

- [ ] `main` protected: required status check `cordon / gate` (strict),
      conversations resolved before merge.
- [ ] `enforce_admins: false` — admin bypass allowed; you review and merge.
- [ ] Force-push and branch deletion disabled.
- [ ] Vulnerability alerts + automated security fixes on.
- [ ] **Allow GitHub Actions to create and approve pull requests** (Settings →
      Actions → General → Workflow permissions) — required so release-please can
      open the release PR. The one toggle the release workflow needs.

## CI (`.github/workflows/ci.yml`)

- [ ] CI runs `scripts/check.sh --ci` — the same gate the hook + you run, so CI
      and local can't drift: shellcheck + schema conformance on every committed
      contract. (Drift needs `$TOOLS_HOME`, so it's a local-only step.)
- [ ] Repo invariants run through cordon's **checks engine** (`run_checks`,
      `$CORDON_HOME/checks/run.mjs` — referenced, never vendored): built-in
      invariants plus this repo's own `commands[]` specs, one verdict. Each check
      is capability-gated (`requires` git/macos/built-dir/`<binary>`), so it's
      lean by default and skips fail-soft what the environment can't satisfy.
- [ ] Add language lint/scanners to match the repo's narrative:
      - Security-focused (plugin, scanner, detection engine) → visible scanner
        (Semgrep for PHP/WordPress, CodeQL where supported) **and** a badge.
      - Plain CLI / library → lint-only, optional badge.
      - "No CI is the pitch" repos → skip the badge deliberately.
- [ ] Syntax-check matrix across every version the README claims to support.
- [ ] Run the exact CI command locally before pushing (`scripts/check.sh`);
      a dev-mode pass is not a CI pass.

## Release (`.github/workflows/release.yml`)

- [ ] Releases run through cordon's reusable `cordon-release.yml` (referenced,
      never vendored) — three lines, the sibling of the `ci.yml` gate call. The
      check is `cordon / release`.
- [ ] `release-type` defaults to `simple` (a tracked `version.txt`), so the repo
      is release-ready as scaffolded. A typed repo overrides it in one line
      (`with: { release-type: node }` — or python, go, …) and drops `version.txt`.
- [ ] Versioning is Conventional-Commit driven: every push to `main` keeps one
      standing `chore(main): release X.Y.Z` PR (computed bump + CHANGELOG);
      merging it cuts the `vX.Y.Z` tag + GitHub Release. Nothing ships until then.
- [ ] The one-time per-repo setting is enabled (see GitHub governance above);
      without it the release PR cannot be opened.

## Files

- [ ] `AGENTS.md` (+ `CLAUDE.md` symlink), `LICENSE` (MIT, Joe Severino),
      `README.md` with the `ci` badge, `SECURITY.md`, `CHANGELOG.md`
      (two-axis: starter SemVer + Cordon `schema_version`).
- [ ] Paths read from `~/.zshrc` vars (`$CODE_HOME`, `$TOOLS_HOME`, …) — never
      hardcode `$HOME/Documents/...`.
