#!/usr/bin/env node
// gen-readme.mjs — render the CLI reference block in README.md from the
// committed Cordon contracts (contract/*.json). The README's command surface is
// therefore a *render* of the contract, not a hand-maintained copy that drifts:
//
//   node scripts/gen-readme.mjs            rewrite the block in place
//   node scripts/gen-readme.mjs --check    write nothing; exit 1 if it would change
//
// Zero dependencies — Node stdlib over the committed JSON — so it needs nothing
// installed and runs in CI as-is. Deterministic output (contracts sorted by
// `order` then name) so the gate can diff it.
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const README = join(ROOT, 'README.md');
const CONTRACTS = join(ROOT, 'contract');
const BEGIN = '<!-- BEGIN GENERATED: cli-reference (scripts/gen-readme.mjs — do not edit by hand) -->';
const END = '<!-- END GENERATED: cli-reference -->';

const esc = (s) => String(s).replace(/\|/g, '\\|'); // keep table cells one column

function effectLine(node) {
  const parts = [`effect: \`${node.effect}\``];
  if (node.network) parts.push('`network`');
  if (node.interactive) parts.push('`interactive`');
  return parts.join(' · ');
}

function commandsTable(cmds) {
  if (!cmds || cmds.length === 0) return null;
  const rows = cmds.map((c) => `| \`${esc(c.name)}\` | \`${c.effect}\` | ${esc(c.summary || '')} |`);
  return ['**Commands**', '', '| command | effect | summary |', '|---|---|---|', ...rows].join('\n');
}

function optionsTable(opts) {
  if (!opts || opts.length === 0) return null;
  const rows = opts.map((o) => {
    const flags = (o.flags && o.flags.length ? o.flags : [o.name]).join(', ');
    const value = o.takes_value ? (o.metavar ? `\`${o.metavar}\`` : 'yes') : 'no';
    return `| \`${esc(flags)}\` | ${value} | ${o.required ? 'yes' : 'no'} | ${esc(o.help || '')} |`;
  });
  return ['**Options**', '', '| flag | value | required | help |', '|---|---|---|---|', ...rows].join('\n');
}

function argsTable(pos) {
  if (!pos || pos.length === 0) return null;
  const rows = pos.map((p) => {
    const name = p.variadic ? `${p.name}…` : p.name;
    return `| \`${esc(name)}\` | ${p.required ? 'yes' : 'no'} | ${esc(p.help || '')} |`;
  });
  return ['**Arguments**', '', '| arg | required | help |', '|---|---|---|', ...rows].join('\n');
}

function examplesList(ex) {
  if (!ex || ex.length === 0) return null;
  const rows = ex.map((e) => (e.comment ? `- \`${e.command}\` — ${e.comment}` : `- \`${e.command}\``));
  return ['**Examples**', '', ...rows].join('\n');
}

function renderTool(c) {
  const blocks = [
    `### \`${c.name}\``,
    effectLine(c),
    c.description || '',
    commandsTable(c.commands),
    optionsTable(c.global_options),
    argsTable(c.positionals),
    examplesList(c.examples),
  ].filter(Boolean);
  return blocks.join('\n\n');
}

function render() {
  const contracts = readdirSync(CONTRACTS)
    .filter((f) => f.endsWith('.json'))
    .map((f) => JSON.parse(readFileSync(join(CONTRACTS, f), 'utf8')))
    .sort((a, b) => (a.order - b.order) || a.name.localeCompare(b.name));
  if (contracts.length === 0) return '_No contracts in `contract/` yet._';
  return contracts.map(renderTool).join('\n\n---\n\n');
}

const check = process.argv.includes('--check');
const md = readFileSync(README, 'utf8');
const i = md.indexOf(BEGIN);
const j = md.indexOf(END);
if (i === -1 || j === -1) {
  console.error(`gen-readme: markers not found in README.md — add:\n${BEGIN}\n${END}`);
  process.exit(1);
}
const next = md.slice(0, i) + `${BEGIN}\n\n${render()}\n\n${END}` + md.slice(j + END.length);

if (check) {
  if (next !== md) {
    console.error('  DRIFT: README CLI reference != contract/  (regenerate: node scripts/gen-readme.mjs)');
    process.exit(1);
  }
  console.log('  ok: README CLI reference matches contract/');
} else {
  writeFileSync(README, next);
  console.log('wrote README.md CLI reference from contract/');
}
