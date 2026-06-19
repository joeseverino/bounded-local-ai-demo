#!/usr/bin/env bash
# setup-governance.sh — apply the standing GitHub cornerstones to a repo, once,
# right after `gh repo create`. Idempotent, re-runnable, and it VERIFIES what it
# sets rather than trusting a 2xx.
#
#   <branch> protection (the repo's default branch):
#     - required status check `cordon / gate` must pass (strict: branch up to
#       date) — the context the reusable gate produces, uniform across repos
#     - conversations must be resolved before merge (no unresolved comments)
#     - a pull request is required, 0 required approvals (solo can't self-approve)
#     - enforce_admins: true   → admins are held to the rules too (no red-check
#       bypass); you still merge, but only once the gate is green
#   security (free on private repos):
#     - vulnerability alerts on
#     - automated security fixes (Dependabot security updates) on
#   actions:
#     - GitHub Actions may create + approve PRs, so release-please can open the
#       standing release PR (default token perms stay read; workflows escalate
#       per-job). Without this the release workflow fails at PR creation.
#
# Branch protection on a PRIVATE repo needs GitHub Pro; on the free plan it is
# only available for PUBLIC repos. When that is the blocker this script SKIPS
# protection with guidance and STILL applies the security settings — it never
# leaves the repo half-configured because one step is gated by plan tier.
#
# Usage: scripts/setup-governance.sh [owner/repo] [required-check]
#   owner/repo     defaults to the current repo (gh repo view)
#   required-check defaults to "cordon / gate" (the reusable gate's check context)
set -euo pipefail

# shellcheck source=scripts/_lib.sh
source "$(dirname "$0")/_lib.sh"   # in-repo presentation; no external dependency

# ── preflight ────────────────────────────────────────────────────────────────
command -v gh >/dev/null 2>&1 || { bad "gh CLI not installed" >&2; exit 1; }
gh auth token   >/dev/null 2>&1 || { bad "gh not authenticated — run: gh auth login" >&2; exit 1; }

REPO="${1:-}"
[[ -n "$REPO" ]] || REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
[[ -n "$REPO" ]] || { bad "no repo — pass owner/repo or run inside a gh repo" >&2; exit 1; }
CHECK="${2:-cordon / gate}"

# Confirm access and read live facts — never assume the branch is "main".
BRANCH="$(gh api "repos/$REPO" -q .default_branch 2>/dev/null || true)"
[[ -n "$BRANCH" ]] || { bad "repo not found or no access: $REPO" >&2; exit 1; }
VISIBILITY="$(gh api "repos/$REPO" -q .visibility 2>/dev/null || echo unknown)"

banner "governance" "branch protection + security — verified, not assumed"
section "target"
printf '   %s%-15s%s %s\n' "$D" "repo" "$R" "$REPO"
printf '   %s%-15s%s %s\n' "$D" "default branch" "$R" "$BRANCH"
printf '   %s%-15s%s %s\n' "$D" "visibility" "$R" "$VISIBILITY"
printf '   %s%-15s%s %s\n' "$D" "required check" "$R" "$CHECK"

# The required check must be a context the workflow actually produces, or
# protection wedges every PR. The standard is the reusable gate's `cordon / gate`;
# warn only if ci.yml neither calls the gate nor defines a matching job.
script_dir="$(cd "$(dirname "$0")/.." && pwd)"
ci_yml="$script_dir/.github/workflows/ci.yml"
if [[ -f "$ci_yml" ]] \
   && ! grep -q "cordon-gate.yml" "$ci_yml" \
   && ! grep -qE "^[[:space:]]+${CHECK%% *}:[[:space:]]*$" "$ci_yml"; then
    warn "ci.yml neither calls cordon's gate nor has a job for '$CHECK' — a required check that never reports blocks every merge" >&2
fi

# ── branch protection ────────────────────────────────────────────────────────
section "branch protection"
protection_payload="$(cat <<JSON
{
  "required_status_checks": { "strict": true, "contexts": ["$CHECK"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "dismiss_stale_reviews": true, "required_approving_review_count": 0 },
  "required_conversation_resolution": true,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
)"

protect_rc=0
perr="$(gh api -X PUT "repos/$REPO/branches/$BRANCH/protection" \
          --input - <<<"$protection_payload" 2>&1 >/dev/null)" || protect_rc=$?

if [[ $protect_rc -eq 0 ]]; then
    # Read it back — trust the state, not the status code.
    verify="$(gh api "repos/$REPO/branches/$BRANCH/protection" \
        -q '"\(.required_status_checks.contexts|join(",")) \(.required_conversation_resolution.enabled) \(.enforce_admins.enabled)"' \
        2>/dev/null || true)"
    read -r got_ctx got_conv got_admins <<<"$verify"
    if [[ ",$got_ctx," == *",$CHECK,"* && "$got_conv" == "true" && "$got_admins" == "true" ]]; then
        pass "on  (checks=[$got_ctx] conversations_resolved=yes admins_enforced=yes)"
    else
        bad "applied but verification mismatched — checks=[$got_ctx] conv=$got_conv enforce_admins=$got_admins" >&2
        exit 1
    fi
elif printf '%s' "$perr" | grep -qiE "Upgrade to GitHub Pro|make this repository public"; then
    skip "SKIPPED — needs a public repo or GitHub Pro (this repo is $VISIBILITY)"
    note "make public:  gh repo edit $REPO --visibility public --accept-visibility-change-consequences"
    note "or upgrade to GitHub Pro, then re-run this script."
    note "until then, 'never commit to $BRANCH' holds by discipline, not the platform."
else
    bad "FAILED" >&2
    note "$perr" >&2
    exit 1
fi

# ── security settings (free on private repos) ────────────────────────────────
section "security"
sec_fail=0
if gh api -X PUT "repos/$REPO/vulnerability-alerts" >/dev/null 2>&1; then
    pass "vulnerability alerts: on"
else
    bad "vulnerability alerts: FAILED — token likely missing the 'repo' scope (gh auth refresh -s repo)" >&2
    sec_fail=1
fi
if gh api -X PUT "repos/$REPO/automated-security-fixes" >/dev/null 2>&1; then
    pass "automated security fixes: on"
else
    bad "automated security fixes: FAILED — token likely missing the 'repo' scope" >&2
    sec_fail=1
fi

# ── actions: let release-please open the release PR ──────────────────────────
section "actions"
actions_payload='{ "default_workflow_permissions": "read", "can_approve_pull_request_reviews": true }'
if gh api -X PUT "repos/$REPO/actions/permissions/workflow" --input - <<<"$actions_payload" >/dev/null 2>&1 \
   && [[ "$(gh api "repos/$REPO/actions/permissions/workflow" -q .can_approve_pull_request_reviews 2>/dev/null)" == "true" ]]; then
    pass "Actions may create + approve PRs (release-please can open the release PR)"
else
    bad "Actions PR-create: FAILED — token likely missing admin on the repo" >&2
    sec_fail=1
fi

if [[ $sec_fail -eq 0 ]]; then
    printf '\n%s%s✓ governance applied%s\n' "$B" "$GR" "$R"
else
    bad "done with errors — see above" >&2
    exit 1
fi
