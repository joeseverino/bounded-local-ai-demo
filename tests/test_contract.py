"""The committed contract must match what the tool emits, and stay on the ladder.

This doubles as a drift guard: if someone edits the CLI surface without
regenerating contract/bounded-local-ai-demo.json, this test fails.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "bounded-local-ai-demo"
CONTRACT = ROOT / "contract" / "bounded-local-ai-demo.json"
LADDER = {"read", "local_write", "vault_write", "remote_write", "deploy"}


def _emit() -> dict:
    out = subprocess.run(
        [sys.executable, str(TOOL), "--describe"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)


def test_committed_contract_matches_emit():
    assert _emit() == json.loads(CONTRACT.read_text())


def test_every_effect_is_on_the_ladder():
    doc = json.loads(CONTRACT.read_text())
    assert doc["effect"] in LADDER
    for command in doc["commands"]:
        assert command["effect"] in LADDER


def test_schema_version_is_v4():
    doc = json.loads(CONTRACT.read_text())
    assert doc["ok"] is True
    assert doc["schema_version"] == 4
