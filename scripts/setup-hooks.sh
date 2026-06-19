#!/usr/bin/env bash
# setup-hooks.sh — enable the tracked git hooks. Run once per clone: the hooks
# live in .githooks/ (so they travel with the repo), but core.hooksPath is local
# config and does not. Idempotent.
set -euo pipefail

# shellcheck source=scripts/_lib.sh
source "$(dirname "$0")/_lib.sh"   # in-repo presentation; no external dependency
cd "$(git rev-parse --show-toplevel)"

git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true

# Use the tracked commit template (solo-authored guidance) if present.
[ -f .gitmessage ] && git config commit.template .gitmessage

banner "hooks" "local guardrails enabled — core.hooksPath=.githooks"
pass "pre-commit   refuses commits on main/master   $(printf '%s(bypass: ALLOW_MAIN_COMMIT=1)%s' "$D" "$R")"
pass "commit-msg   rejects AI attribution           $(printf '%s(bypass: git commit --no-verify)%s' "$D" "$R")"
pass "pre-push     runs scripts/check.sh            $(printf '%s(bypass: git push --no-verify)%s' "$D" "$R")"
[ -f .gitmessage ] && pass "commit.template  .gitmessage                  $(printf '%s(solo-authored guidance)%s' "$D" "$R")"
