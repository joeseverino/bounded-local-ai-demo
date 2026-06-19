[![ci](https://github.com/joeseverino/bounded-local-ai-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/joeseverino/bounded-local-ai-demo/actions/workflows/ci.yml)

# bounded-local-ai-demo

A small, reproducible demo that makes one security claim concrete: a local AI
assistant can be given useful context from a private documentation vault **and**
be unable to read what it should not, because the surrounding system gives it no
path around the gate.

It is the isolation companion to the *Bounded Local AI Workflows* write-up. The
local deployment described there is *mediation* (the agent could reach the files
directly but is asked to route through the gate); this container demonstrates
*isolation* (the agent has no other path), enforced by the operating system, not
by prompts or good behavior.

## What it proves

A throwaway container runs the [`severino-vault-mcp`](https://github.com/joeseverino/severino-vault-mcp)
server over a sample vault. Inside it, two users exist: `mcp` owns the vault and
runs the server; `agent` is the unprivileged client. Running the demo executes
four checks **as the `agent` user**:

| Property | How it is enforced |
|---|---|
| Agent cannot read the vault directly | vault is `mcp`-owned, mode `go-rwx`; agent gets permission denied |
| Agent cannot borrow `mcp` another way | sudoers lets agent run *only* the launcher, not `cat`/`ls`/a shell as `mcp` |
| Internal content IS reachable | only through the MCP, which releases `internal` bodies |
| Restricted content is withheld | the MCP sensitivity gate holds back the `restricted` doc |

All four must pass; the runner exits non-zero otherwise, so it doubles as a CI
assertion.

## Requirements

- A container runtime exposing the `docker` CLI (Docker Desktop, Colima, OrbStack, …).
- Network access on first build (pulls the base image and clones the MCP).

The demo uses the MCP's bundled **sample vault** (fake data). No real vault, no
credentials, and no host paths are baked into the image.

## Quick start

```sh
bin/bounded-local-ai-demo build     # build the image
bin/bounded-local-ai-demo verify    # run the isolation checks
bin/bounded-local-ai-demo clean     # remove the image
```

Or with raw Docker:

```sh
docker build -f container/Dockerfile -t bounded-local-ai-demo .
docker run --rm bounded-local-ai-demo
```

Expected tail of a passing run:

```
  [PASS] direct filesystem read blocked    listdir=denied, open=denied
  [PASS] sudo bypass blocked               mcp:denied, mcp:denied, mcp:denied
  [PASS] internal doc released via MCP      rb-generate-internal-cert: body=... chars
  [PASS] restricted doc withheld via MCP    infra-offline-ca: body=0 chars; advisory=...
  RESULT: all properties hold
```

## How it works

Everything lives in [`container/`](container/):

| File | Role |
|---|---|
| `Dockerfile` | builds the image: installs the MCP as `mcp`, copies the sample vault to `/vault` (mode `go-rwx`), wires the launcher and sudoers |
| `run-mcp` | the single channel to the vault: runs the MCP as `mcp` over stdio with the vault path fixed |
| `agent.sudoers` | the lock: `agent` may run only `run-mcp` (no args) as `mcp` |
| `verify.py` | the four checks, run as `agent` |

The key idea is that "reachable only through the server" is enforced by file
permissions plus a single, argument-locked `sudo` entry, not by trusting the
agent to behave. Knowing a file's path is not enough; there is no readable path.

## CLI reference

The command surface below is generated from the committed Cordon contract
([`contract/bounded-local-ai-demo.json`](contract/bounded-local-ai-demo.json)),
so it cannot drift from the tool. Each command declares its effect on the Cordon
blast-radius ladder.

<!-- BEGIN GENERATED: cli-reference (scripts/gen-readme.mjs — do not edit by hand) -->

### `bounded-local-ai-demo`

effect: `read`

Build and run the OS-enforced isolation demo.

**Commands**

| command | effect | summary |
|---|---|---|
| `build` | `local_write` | Build the demo container image. |
| `verify` | `local_write` | Run the isolation checks in a throwaway container. |
| `clean` | `local_write` | Remove the demo image. |

**Options**

| flag | value | required | help |
|---|---|---|---|
| `--describe` | no | no | Emit the Cordon v4 command-surface contract as JSON and exit. |
| `--pretty` | no | no | With --describe, pretty-print the JSON (default: compact). |

**Examples**

- `bounded-local-ai-demo build` — build the demo image
- `bounded-local-ai-demo verify` — run the isolation checks

<!-- END GENERATED: cli-reference -->

## Built with

Scaffolded from [cordon-starter](https://github.com/joeseverino/cordon-starter):
the Cordon command-surface contract, the green-gating CI (`cordon / gate`),
release automation, and the governance setup all come from there.

## License

MIT. See [LICENSE](LICENSE).
