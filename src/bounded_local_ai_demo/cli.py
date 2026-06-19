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
IMAGE = "bounded-local-ai-demo"
DOCKERFILE = ROOT / "container" / "Dockerfile"

GROUP = "Demos"
ORDER = 1
PARAS = [
    "Builds and runs the bounded-local-AI isolation demo: a container in which "
    "the MCP serves a sample vault that only the mcp user can read, and an "
    "unprivileged agent user can reach it only through the MCP sensitivity gate.",
]
EXAMPLES = [
    {"command": "bounded-local-ai-demo build", "comment": "build the demo image"},
    {"command": "bounded-local-ai-demo verify", "comment": "run the isolation checks"},
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
        description="Build and run the OS-enforced isolation demo.",
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

    p_build = sub.add_parser("build", help="Build the demo container image.")
    p_build.add_argument(
        "--mcp-ref", default="main", help="severino-vault-mcp git ref to build from"
    )
    sub.add_parser("verify", help="Run the isolation checks in a throwaway container.")
    sub.add_parser("clean", help="Remove the demo image.")

    # Blast radius on the Cordon ladder. build pulls the base image and clones the
    # MCP (network); verify and clean only touch local docker/container state.
    _set_effect(p_build, "local_write", network=True)
    _set_effect(sub.choices["verify"], "local_write")
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
        return _run(
            [
                "docker", "build",
                "-f", str(DOCKERFILE),
                "--build-arg", f"MCP_REF={args.mcp_ref}",
                "-t", IMAGE, str(ROOT),
            ]
        )
    if args.command == "verify":
        return _run(["docker", "run", "--rm", IMAGE])
    if args.command == "clean":
        return _run(["docker", "rmi", "-f", IMAGE])
    parser.error(f"unknown command: {args.command}")
    return 2
