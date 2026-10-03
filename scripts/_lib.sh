# shellcheck shell=bash
# shellcheck disable=SC2034  # palette vars are read by the scripts that source this
# _lib.sh — shared presentation for this scaffold's scripts. Sourced, not run.
#
# Lives INSIDE the starter on purpose: try.sh must render before $TOOLS_HOME
# exists, so the chrome carries no external dependency. The contract truth
# (schema, validator, checks engine) comes from the cordon-spec package.
#
# Palette voices: CY narrates the framework; tools keep their own GR/YE.

# TTY-aware: colors only when stdout is a terminal. Piped / CI output is clean
# plain text, so the showcase reads fine in a log too.
if [[ -t 1 ]]; then
    B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
    CY=$'\033[36m'; GR=$'\033[32m'; YE=$'\033[33m'; RD=$'\033[31m'; MA=$'\033[35m'
else
    B='' D='' R='' CY='' GR='' YE='' RD='' MA=''
fi
RULE='──────────────────────────────────────────────'

# rule — a dim full-width divider.
rule() { printf '%s%s%s\n' "$D" "$RULE" "$R"; }

# banner <mode-word> <tagline> — wordmark header + tagline + seating rule. Also
# sets the terminal title to "cordon-starter · <mode-word>".
banner() {
    [[ -t 1 ]] && printf '\033]0;cordon-starter · %s\007' "$1"
    printf '\n%scordon-starter%s %s· %s%s\n' "$B$MA" "$R" "$D" "$1" "$R"
    printf '%s%s%s\n' "$D" "$2" "$R"
    rule
}

# step <n> <title> <caption> — a numbered walkthrough header (try.sh). Reads an
# optional $STEPS for the "/N" total; the caption sits dim beneath the title.
step() {
    local suffix=""
    [[ -n "${STEPS:-}" ]] && suffix="/$STEPS"
    printf '\n%s%s ▍ %s%s · %s%s\n' "$B" "$CY" "$1" "$suffix" "$2" "$R"
    printf '     %s%s%s\n' "$D" "$3" "$R"
}

# run <cmd...> — echo the command as a prompt line, then run it. Makes the
# walkthrough self-documenting: the reader sees exactly what produced each block.
run() {
    printf '     %s$%s %s%s%s\n\n' "$D" "$R" "$B" "$*" "$R"
    "$@"
}

# section <title> [caption] — an un-numbered section header (check.sh). Same
# accent as step, but no trailing blank line: the gate's lines follow it tight.
section() {
    printf '\n%s%s ▍ %s%s\n' "$B" "$CY" "$1" "$R"
    [[ -n "${2:-}" ]] && printf '     %s%s%s\n' "$D" "$2" "$R"
    return 0   # never let a missing caption (&&-false) abort the caller under set -e
}

# Per-line status. pass/skip print to stdout; the caller routes failures to
# stderr where CI expects them (e.g. `bad "..." >&2`).
pass() { printf '   %s✓%s %s\n' "$GR" "$R" "$1"; }
skip() { printf '   %s○%s %s%s%s\n' "$YE" "$R" "$D" "$1" "$R"; }
warn() { printf '   %s!%s %s%s%s\n' "$YE" "$R" "$D" "$1" "$R"; }
bad()  { printf '   %s✗ %s%s\n' "$RD" "$1" "$R"; }
note() { printf '       %s%s%s\n' "$D" "$1" "$R"; }

# cline <status> <label> [note] — one compact, aligned result line (check.sh's
# default output). status ∈ pass|skip|fail drives the symbol/colour/word; the
# optional note trails dim. Clean enough for a pre-push hook or a CI log.
cline() {
    local status="$1" label="$2" note="${3:-}" sym col word
    case "$status" in
        pass) sym='✓'; col="$GR"; word='ok'   ;;
        skip) sym='○'; col="$YE"; word='skip' ;;
        *)    sym='✗'; col="$RD"; word='fail' ;;
    esac
    if [[ -n "$note" ]]; then
        printf '  %s%s%s %-20s %s%-4s%s  %s%s%s\n' "$col" "$sym" "$R" "$label" "$col" "$word" "$R" "$D" "$note" "$R"
    else
        printf '  %s%s%s %-20s %s%s%s\n' "$col" "$sym" "$R" "$label" "$col" "$word" "$R"
    fi
}

# Verdicts. <mode> is the run mode, shown in dim parens.
allgreen() { printf '\n%s%s✓ ALL GREEN%s %s(%s)%s\n' "$B" "$GR" "$R" "$D" "$1" "$R"; }
failures() { printf '\n%s%s✗ FAILURES (%s)%s%s — fix before pushing%s\n' "$B" "$RD" "$1" "$R" "$D" "$R"; }
