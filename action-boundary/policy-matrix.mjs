#!/usr/bin/env node
// policy-matrix.mjs — the action-boundary decision matrix.
//
// Reads a tool's declared effects from its `--describe` contract and prints what
// Cordon's gate would decide for each command under the `local` (trusted
// single-operator, fail open) and `strict` (multi-tenant / remote, fail closed)
// presets. Pure decision logic from cordon's policy.mjs — no command is run.
import { execFileSync } from 'node:child_process';
import { PRESETS, verdict, resolveEffect } from '/opt/cordon/harness/policy.mjs';

const TOOL = process.argv[2] || 'sample-tool';
const contract = JSON.parse(execFileSync(TOOL, ['--describe'], { encoding: 'utf8' }));
const commands = (contract.commands || []).map((c) => c.name);

const decide = (effect, preset) => verdict(effect, preset).decision;
const pad = (s, n) => String(s).padEnd(n);

const out = [];
out.push('');
out.push("  Bounded Local AI Workflows — action-boundary gate (Cordon)");
out.push('');
out.push(`  ${pad('command', 10)}${pad('effect', 14)}${pad('local', 10)}strict`);
out.push(`  ${pad('-'.repeat(7), 10)}${pad('-'.repeat(11), 14)}${pad('-'.repeat(7), 10)}${'-'.repeat(6)}`);
for (const name of commands) {
  const effect = resolveEffect(contract, name);
  out.push(`  ${pad(name, 10)}${pad(effect, 14)}${pad(decide(effect, PRESETS.local), 10)}${decide(effect, PRESETS.strict)}`);
}
out.push('');
out.push('  local  = trusted single-operator   (unannotated -> allow)');
out.push('  strict = multi-tenant / remote     (unannotated -> block)');
out.push('');
console.log(out.join('\n'));
