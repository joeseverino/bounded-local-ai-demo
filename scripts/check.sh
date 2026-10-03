#!/usr/bin/env sh
# check.sh: the gate CI runs, run locally (cordon's checks engine over this
# repo). Engine flags pass through, e.g. `scripts/check.sh --json`.
exec npx --yes --package cordon-spec@2 cordon-checks --root "$(cd "$(dirname "$0")/.." && pwd)" "$@"
