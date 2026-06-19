# AGENTS.md

This repo was started from **cordon-starter** — the canonical scaffold every
Severino repo begins from. The rules below are the standing cornerstones. They
override anything an older repo's docs imply.

> Rename the placeholders (`<repo>`, the example tool) and delete what a given
> project doesn't need. The cornerstones stay.

## How a command surface is documented here

The single source of truth for any CLI surface is **one declaration**, not prose.
This repo's tool, `bin/bounded-local-ai-demo`, builds an `argparse` parser and
emits the contract JSON from it with cordon's Python emitter (`cordon_emit`), so
the human help and the machine JSON are two pure renders of the same parser and
cannot drift.

- **Emitter:** `cordon_emit.describe_parser(parser, group=…, order=…)` returns a
  Cordon v4 document; `cordon_emit.set_effect(subparser, effect, …)` annotates a
  command's blast radius. It is a dev-group dependency in `pyproject.toml`
  (synced by default with `uv sync`); running the demo itself needs only Docker.
- **The schema:** `https://jseverino.com/schemas/cordon-v4.json`
  (`schema_version: 4`). The contract is `additionalProperties: false` and
  byte-deterministic — no timestamps, stable ordering.
- **Effect ladder** (every tool/command declares one, default `read`):
  `read < local_write < vault_write < remote_write < deploy`, plus optional
  `+network` / `+interactive`. Declare it on anything that mutates, reaches
  off-box, or blocks on a TTY.

Regenerate the golden contract after a surface change (compact, to match the
drift check): `uv run bin/bounded-local-ai-demo --describe > contract/bounded-local-ai-demo.json`.

## Introspect via the contract, never by parsing source

To learn what a tool does, **call its contract** — `<tool> --describe` (or
`tools describe <name>` for the toolchain). Read the JSON; risk-gate on `effect`.
Do not read the implementation to reconstruct flags or behavior.

If a tool has **no `--describe`**, that is the bug: give it a `describe_spec()`
(source the canonical `describe.sh`), then call it. A surface without a contract
is unfinished.

## Git workflow — branch → PR → review → merge

Never commit to `main`. Never branch from a stale local tree.

```sh
git fetch origin
git checkout -b <feature> origin/main
# work, commit, push
gh pr create
```

- One feature = one branch name, reused across repos when the change spans them.
- Hand back only on **green CI** with **zero unresolved PR comments**.
- **Solo-authored.** No `Co-Authored-By`, no "Claude/AI" mentions in commits or
  PR bodies.

On a new repo, run `scripts/setup-governance.sh` to protect `main` (required
`ci` green, conversations resolved, admin bypass — you review and merge) and
switch on the security settings. Branch protection needs a public repo or
GitHub Pro; on a private free repo the script skips it and "never commit to
`main`" holds by discipline.

Make that discipline enforceable offline too: `scripts/setup-hooks.sh` points
git at the tracked `.githooks/` (`core.hooksPath`). `pre-commit` refuses commits
on `main`; `commit-msg` rejects AI attribution (the solo-authored rule above);
`pre-push` runs `scripts/check.sh` so red never leaves the machine. Bypass
deliberately with `ALLOW_MAIN_COMMIT=1` / `git … --no-verify`.

## CI and security

- `.github/workflows/ci.yml` runs **`scripts/check.sh --ci`** — the *same* gate
  the pre-push hook and you run, in its no-toolchain mode (shellcheck + schema
  conformance via cordon's own harness at `$CORDON_HOME` — cordon is
  referenced, never vendored). One definition, so CI and local can't drift.
- Add language-specific lint/scanners per the repo's narrative. Security-focused
  repos get a visible scanner (Semgrep/CodeQL) + badge; a plain CLI gets
  lint-only. See `docs/CORNERSTONES.md`.
- **Contract drift is a CI failure waiting to happen — catch it locally.** Run
  `scripts/check.sh` before pushing: the engine's `drift` check re-emits each
  tool's `--describe` and diffs it against the committed `contract/*.json`
  (it's `!ci`-gated — local only; here it needs the `describe` extra, so run it
  under `uv run`). Regenerate and commit the golden when the surface changes.
- `scripts/check.sh` is the identical wrapper every cordon repo ships; it runs
  cordon's checks engine over `cordon.checks.json`. Pass engine flags through —
  **`--json`** for a machine-readable result object (prefer it as an agent).

## Repo checks config (`cordon.checks.json`)

cordon's **checks engine** (`$CORDON_HOME/checks/run.mjs`, the `run_checks` step)
runs two kinds of check over the repo through one loop:

- **invariants** — cordon's built-in, portable rules (no secrets/build output
  tracked, Actions pinned, internal links resolve, …). They run with zero config.
- **commands** — *your* repo's own spawned specs (a test suite, a type check, a
  bespoke audit), declared as data in `cordon.checks.json` `commands[]`. The spec
  code stays in your repo; the engine just runs it and folds it into one verdict.

The whole flow at a glance — two kinds in, capability gate, one verdict out — is
the [checks-engine diagram](https://github.com/joeseverino/cordon/blob/main/checks/README.md)
in cordon's test-suite docs.

It takes an optional **`cordon.checks.json`** at the repo root. This template
ships one with its `$schema` wired to the published, *derived* schema — so your
editor autocompletes every key (including each `commands[]` entry), documents it
on hover, and flags typos as you type. No shape to memorize.

**Most checks are off until the repo earns them.** Each check declares the
capabilities it `requires` (`git` / `macos` / `ci` / `built-dir` / any `<binary>`
like `playwright`, plus `!cap` to negate); the engine detects what's present and
**skips fail-soft** what isn't. So a `playwright` command runs only where
playwright is installed, a `built-dir` check only after a build — the default
posture is lean, and you opt in by adding the capability, not by flipping a flag.

- See what applies to this repo: `node "$CORDON_HOME/checks/run.mjs" --list`
  (or open `cordon.checks.json` and let the schema prompt you). `--json` is the
  agent contract; `--phase pre-build|build|post-build` runs one phase.
- The `idempotence` knob ships **off** (`"command": null`). When you add a
  build/generate step, set it — e.g. `"command": "scripts/gen-readme.mjs"` — and
  the check fails if that command ever dirties the worktree.
- Add a spec as a command (every spec carries an honest `effect`, like a tool):

  ```json
  "commands": [
    { "id": "types", "name": "Type check", "effect": "read",
      "requires": ["tsc"], "exec": { "cmd": "npx", "args": ["tsc", "--noEmit"] } }
  ]
  ```

- Omit a key to use a check's defaults; absent file → all defaults. The *rules and
  the engine* are cordon's; the *parameters and the specs* are yours.

## Environment it assumes

These repos live in the Severino Code tree and read paths from `~/.zshrc`
(single source of truth — don't hardcode `$HOME/Documents/...`):

| var | is |
|---|---|
| `$CODE_HOME` | `~/Documents/Code` |
| `$PROJECTS_HOME` | `$CODE_HOME/Projects` |
| `$ASSETS_HOME` | `$CODE_HOME/Assets` |
| `$TOOLS_HOME` | `$ASSETS_HOME/tools` — the canonical `describe.sh` lives here |
| `$CORDON_HOME` | `$ASSETS_HOME/cordon` — the schema + conformance harness this validates against |
| `$NOTES_HOME` | the Obsidian vault |

## Verify before handing back

```sh
scripts/check.sh        # shellcheck + contract drift + schema conformance
git diff --check        # no whitespace damage
```
