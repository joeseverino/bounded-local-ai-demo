#!/usr/bin/env python3
"""Isolation checks, run as the unprivileged `agent` user.

Proves four properties of the bounded-local-AI isolation deployment:

  1. The agent cannot read the vault directly       (filesystem permission denied)
  2. The agent cannot borrow mcp's read another way (sudo refuses anything but the launcher)
  3. Internal content IS reachable through the MCP   (the gate releases it)
  4. Restricted content is withheld through the MCP  (the gate holds it back)

Exit code is non-zero if any property fails, so this doubles as a CI assertion.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

VAULT = "/vault"
# A path that exists in the MCP's public sample vault; knowing it is fair game
# (the layout is public), which is the point: knowing the path is not enough.
KNOWN_RESTRICTED_PATH = f"{VAULT}/02 Infrastructure/Local PKI/Offline CA.md"
LAUNCHER = ["sudo", "-u", "mcp", "/usr/local/bin/run-mcp"]

INTERNAL_DOC = "rb-generate-internal-cert"  # internal -> body released
RESTRICTED_DOC = "infra-offline-ca"          # restricted -> body withheld

results: list[tuple[bool, str, str]] = []


def record(ok: bool, name: str, detail: str) -> None:
    results.append((ok, name, detail))


def check_direct_read_denied() -> None:
    listed = None
    opened = None
    try:
        os.listdir(VAULT)
        listed = "listed"  # should not happen
    except PermissionError:
        listed = "denied"
    except Exception as exc:  # noqa: BLE001
        listed = f"error:{type(exc).__name__}"
    try:
        with open(KNOWN_RESTRICTED_PATH, encoding="utf-8") as fh:
            fh.read(1)
        opened = "read"  # should not happen
    except PermissionError:
        opened = "denied"
    except FileNotFoundError:
        opened = "denied(traversal)"  # cannot even traverse the locked dir
    except Exception as exc:  # noqa: BLE001
        opened = f"error:{type(exc).__name__}"
    ok = listed == "denied" and opened.startswith("denied")
    record(ok, "direct filesystem read blocked", f"listdir={listed}, open={opened}")


def check_sudo_bypass_denied() -> None:
    # Try to abuse sudo to read the vault as mcp without going through the gate.
    attempts = [
        ["sudo", "-n", "-u", "mcp", "cat", KNOWN_RESTRICTED_PATH],
        ["sudo", "-n", "-u", "mcp", "ls", VAULT],
        ["sudo", "-n", "-u", "mcp", "/bin/sh", "-c", f"cat '{KNOWN_RESTRICTED_PATH}'"],
    ]
    all_denied = True
    detail = []
    for cmd in attempts:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        denied = proc.returncode != 0
        all_denied = all_denied and denied
        detail.append(f"{cmd[3]}:{'denied' if denied else 'ALLOWED'}")
    record(all_denied, "sudo bypass blocked", ", ".join(detail))


def _data_from_result(result) -> dict:
    data = getattr(result, "structuredContent", None)
    if isinstance(data, dict):
        # FastMCP wraps a dict return under "result" when it is not already a model.
        return data.get("result", data) if "result" in data and isinstance(data["result"], dict) else data
    import json

    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    return {}


async def mcp_read(doc_id: str, *, include_restricted: bool = False) -> dict:
    params = StdioServerParameters(command=LAUNCHER[0], args=LAUNCHER[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "read_doc",
                {"doc_id": doc_id, "include_restricted": include_restricted},
            )
            return _data_from_result(result)


async def check_mcp_internal_released() -> None:
    data = await mcp_read(INTERNAL_DOC)
    body = data.get("body") or ""
    ok = bool(body.strip())
    record(ok, "internal doc released via MCP", f"{INTERNAL_DOC}: body={len(body)} chars")


async def check_mcp_restricted_withheld() -> None:
    data = await mcp_read(RESTRICTED_DOC)
    body = data.get("body") or ""
    withheld = not body.strip()
    advisory = (data.get("advisory") or "")[:48]
    record(withheld, "restricted doc withheld via MCP", f"{RESTRICTED_DOC}: body={len(body)} chars; advisory={advisory!r}")


async def main() -> int:
    check_direct_read_denied()
    check_sudo_bypass_denied()
    try:
        await check_mcp_internal_released()
    except Exception as exc:  # noqa: BLE001
        record(False, "internal doc released via MCP", f"client error: {exc}")
    try:
        await check_mcp_restricted_withheld()
    except Exception as exc:  # noqa: BLE001
        record(False, "restricted doc withheld via MCP", f"client error: {exc}")

    print("\n  Bounded Local AI Workflows — isolation checks (running as 'agent')\n")
    width = max(len(name) for _, name, _ in results)
    all_ok = True
    for ok, name, detail in results:
        all_ok = all_ok and ok
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name.ljust(width)}   {detail}")
    print()
    print("  RESULT:", "all properties hold" if all_ok else "ISOLATION VIOLATED")
    print()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
