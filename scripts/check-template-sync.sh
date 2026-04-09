#!/usr/bin/env bash
# check-template-sync.sh — Verify that templates/ and src/cast_cli/templates/
# stay in sync. Exits 1 if any devsecops.yml template has drifted.
#
# Usage: bash scripts/check-template-sync.sh
#
# The templates/ directory is the canonical "curl-download" copy.
# The src/cast_cli/templates/ directory is the embedded CLI copy.
# They must remain identical for every devsecops.yml file.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL="$REPO_ROOT/templates"
EMBEDDED="$REPO_ROOT/src/cast_cli/templates"

drift=0

# Platforms and stacks to check
declare -a STACKS=("python" "nodejs" "go")
declare -a PLATFORMS=("" "gitlab/")  # "" = github (no subdirectory prefix in templates/)

for stack in "${STACKS[@]}"; do
    # GitHub templates: templates/<stack>/devsecops.yml vs src/cast_cli/templates/<stack>/devsecops.yml
    src="$CANONICAL/$stack/devsecops.yml"
    dst="$EMBEDDED/$stack/devsecops.yml"
    if ! diff -q "$src" "$dst" > /dev/null 2>&1; then
        echo "DRIFT: $stack/devsecops.yml (github)"
        echo "  canonical : $src"
        echo "  embedded  : $dst"
        drift=1
    fi

    # GitLab templates: templates/gitlab/<stack>/devsecops.yml vs src/cast_cli/templates/gitlab/<stack>/devsecops.yml
    src="$CANONICAL/gitlab/$stack/devsecops.yml"
    dst="$EMBEDDED/gitlab/$stack/devsecops.yml"
    if ! diff -q "$src" "$dst" > /dev/null 2>&1; then
        echo "DRIFT: gitlab/$stack/devsecops.yml"
        echo "  canonical : $src"
        echo "  embedded  : $dst"
        drift=1
    fi
done

if [ "$drift" -eq 0 ]; then
    echo "✓ All templates in sync (templates/ == src/cast_cli/templates/)"
    exit 0
else
    echo ""
    echo "✗ Template drift detected."
    echo "  Update the embedded copies to match the canonical templates/ directory."
    echo "  Run: diff -r templates/ src/cast_cli/templates/ --exclude='*.py' --exclude='__pycache__'"
    exit 1
fi
