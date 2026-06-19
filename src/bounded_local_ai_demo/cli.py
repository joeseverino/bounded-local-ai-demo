"""The bounded-local-ai-demo command surface.

One declaration, two views: `--describe` emits the Cordon v4 command-surface
contract (the same spec `-h` renders from), so the human help and the machine
contract cannot drift. Each subcommand declares its blast radius on the Cordon
effect ladder, so a risk-gating consumer can reason about it before running.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE_READ = "bounded-local-ai-demo-read"
IMAGE_GATE = "bounded-local-ai-demo-gate"
DOCKERFILE_READ = ROOT / "read-boundary" / "Dockerfile"
DOCKERFILE_GATE = ROOT / "action-boundary" / "Dockerfile"

GROUP = "Demos"
ORDER = 1
PARAS = [
    "Builds and runs the two bounded-local-AI demos. The read boundary is a "
    "container where the MCP serves a sample vault that only the mcp user can "
    "read, and an unprivileged agent reaches it only through the sensitivity "
    "gate. The action boundary runs Cordon's effect gate over a sample tool to "
    "show allow / confirm / block decisions per deployment posture.",
]
EXAMPLES = [
    {"command": "bounded-local-ai-demo verify", "comment": "read boundary: isolation checks"},
    {"command": "bounded-local-ai-demo gate", "comment": "action boundary: effect-gate matrix"},
]


def _noop_set_effect(parser, effect, **kwargs):
    """Fallback when cordon-emit is absent: effects matter only for --describe."""
    return parser


# cordon-emit is a dev-only tool (for regenerating the contract). Running the
# demo needs only Docker, so its absence degrades to a no-op annotation.
try:
    from cordon_emit import set_effect as _set_effect
except ModuleNotFoundError:
    _set_effect = _noop_set_effect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bounded-local-ai-demo",
        description="Build and run the bounded-local-AI demos (read + action boundary).",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Emit the Cordon v4 command-surface contract as JSON and exit.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="With --describe, pretty-print the JSON (default: compact).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_build = sub.add_parser("build", help="Build both demo images (read + action boundary).")
    p_build.add_argument(
        "--mcp-ref", default="main", help="severino-vault-mcp git ref for the read-boundary image"
    )
    sub.add_parser("verify", help="Read boundary: run the isolation checks in a throwaway container.")
    sub.add_parser("gate", help="Action boundary: print the Cordon effect-gate decision matrix.")
    sub.add_parser("clean", help="Remove both demo images.")

    # Blast radius on the Cordon ladder. build pulls base images and clones the
    # MCP and cordon (network); verify/gate/clean only touch local docker state.
    _set_effect(p_build, "local_write", network=True)
    _set_effect(sub.choices["verify"], "local_write")
    _set_effect(sub.choices["gate"], "local_write")
    _set_effect(sub.choices["clean"], "local_write")
    return parser


def describe(pretty: bool) -> int:
    try:
        from cordon_emit import describe_parser
    except ModuleNotFoundError:
        sys.stderr.write(
            "cordon-emit not installed (it is a dev dependency). Run `uv sync`, "
            "then `uv run bin/bounded-local-ai-demo --describe`.\n"
        )
        return 1
    doc = describe_parser(
        build_parser(), group=GROUP, order=ORDER, paras=PARAS, examples=EXAMPLES
    )
    indent = 2 if pretty else None
    separators = (",", ": ") if pretty else (",", ":")
    print(json.dumps(doc, indent=indent, separators=separators))
    return 0


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd).returncode


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.describe:
        return describe(args.pretty)
    if not args.command:
        parser.print_help()
        return 0
    if args.command == "build":
        rc = _run(
            [
                "docker", "build",
                "-f", str(DOCKERFILE_READ),
                "--build-arg", f"MCP_REF={args.mcp_ref}",
                "-t", IMAGE_READ, str(ROOT),
            ]
        )
        if rc:
            return rc
        return _run(
            ["docker", "build", "-f", str(DOCKERFILE_GATE), "-t", IMAGE_GATE, str(ROOT)]
        )
    if args.command == "verify":
        return _run(["docker", "run", "--rm", IMAGE_READ])
    if args.command == "gate":
        return _run(["docker", "run", "--rm", IMAGE_GATE])
    if args.command == "clean":
        rc = _run(["docker", "rmi", "-f", IMAGE_READ])
        return _run(["docker", "rmi", "-f", IMAGE_GATE]) or rc
    parser.error(f"unknown command: {args.command}")
    return 2
