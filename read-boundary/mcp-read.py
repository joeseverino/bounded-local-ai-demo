#!/usr/bin/env python3
"""mcp-read <doc_id> — read a vault doc through the MCP gate, as the agent user.

The agent has no direct read access to the vault (try `cat` and you get Permission
denied). This is the only path that works, and it still enforces the sensitivity
gate: internal/sensitive bodies come back (sensitive with an advisory), restricted
bodies are withheld.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

LAUNCHER = ["sudo", "-u", "mcp", "/usr/local/bin/run-mcp"]


def _data(result) -> dict:
    data = getattr(result, "structuredContent", None)
    if isinstance(data, dict):
        if "result" in data and isinstance(data["result"], dict):
            return data["result"]
        return data
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    return {}


async def _read(doc_id: str) -> dict:
    params = StdioServerParameters(command=LAUNCHER[0], args=LAUNCHER[1:])
    with open(os.devnull, "w") as errlog:
        async with stdio_client(params, errlog=errlog) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                result = await session.call_tool("read_doc", {"doc_id": doc_id})
                return _data(result)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: mcp-read <doc_id>", file=sys.stderr)
        return 2
    doc_id = sys.argv[1]
    data = asyncio.run(_read(doc_id))
    sens = data.get("sensitivity", "?")
    body = (data.get("body") or "").strip()
    advisory = (data.get("advisory") or "").strip()
    if body:
        print(f"released via MCP  ·  {doc_id}  ·  sensitivity={sens}")
        if advisory:
            print(f"advisory: {advisory}")
        print("-" * 56)
        print(body)
    else:
        print(f"withheld via MCP  ·  {doc_id}  ·  sensitivity={sens}")
        if advisory:
            print(f"advisory: {advisory}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
