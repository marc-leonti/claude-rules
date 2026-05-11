#!/usr/bin/env bash
# bootstrap.sh — one-shot setup of Marc's claude-rules in a new project.
#
# Usage (from inside the new project's root, after `git init` or `git clone`):
#   curl -s https://raw.githubusercontent.com/marc-leonti/claude-rules/main/bootstrap.sh | bash
#
# What it does:
#   1. Creates a `claude_rules/` directory at the project root.
#   2. Downloads the canonical rules files from marc-leonti/claude-rules into it.
#   3. Copies CLAUDE.md.template to the project root as CLAUDE.md (only if no
#      CLAUDE.md exists; will not overwrite an existing one).
#   4. Marks the sync script + this file executable.
#
# What it does NOT do:
#   - Commit or push. You decide when to commit, with what message, on which
#     branch.
#   - Edit any existing files (other than the no-overwrite CLAUDE.md case).
#   - Apply project-specific configuration. After running this, edit
#     CLAUDE.md and add project-specific rules below the standard preamble.

set -euo pipefail

REPO_OWNER="marc-leonti"
REPO_NAME="claude-rules"
BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}"

# Files that go inside the project's claude_rules/ directory.
RULES_FILES=(
  "claude_user_rules.md"
  "lessons_learned.md"
  "getting_started_with_claude.md"
  "README.md"
  "claude_rules_sync.py"
  "bootstrap.sh"
)

# The template that becomes the project's root CLAUDE.md.
TEMPLATE_FILE="CLAUDE.md.template"

echo "=== Bootstrapping Marc's claude-rules into $(pwd) ==="

# Sanity: refuse to run from inside an existing claude_rules/ to avoid recursion.
case "$(basename "$(pwd)")" in
  claude_rules|claude-rules)
    echo "ERROR: refusing to bootstrap from inside a claude_rules / claude-rules directory."
    echo "       Run from the project root instead."
    exit 1
    ;;
esac

mkdir -p claude_rules

for f in "${RULES_FILES[@]}"; do
  url="${RAW_BASE}/${f}"
  dest="claude_rules/${f}"
  echo "  fetching ${f}"
  if ! curl -fsSL "${url}" -o "${dest}"; then
    echo "  ERROR: failed to fetch ${url}"
    exit 1
  fi
done

# Make scripts executable
chmod +x claude_rules/claude_rules_sync.py claude_rules/bootstrap.sh

# Download the template; place at root as CLAUDE.md unless one already exists
echo "  fetching ${TEMPLATE_FILE}"
TEMPLATE_TMP=$(mktemp)
curl -fsSL "${RAW_BASE}/${TEMPLATE_FILE}" -o "${TEMPLATE_TMP}"

if [ -e "CLAUDE.md" ]; then
  echo "  CLAUDE.md already exists at the project root — leaving it alone."
  echo "  Reference template saved to claude_rules/${TEMPLATE_FILE} for manual merge."
  cp "${TEMPLATE_TMP}" "claude_rules/${TEMPLATE_FILE}"
else
  cp "${TEMPLATE_TMP}" "CLAUDE.md"
  cp "${TEMPLATE_TMP}" "claude_rules/${TEMPLATE_FILE}"
  echo "  installed CLAUDE.md at project root (and reference copy in claude_rules/)"
fi
rm -f "${TEMPLATE_TMP}"

cat <<'EOF'

=== Bootstrap complete ===

Next steps:
  1. Edit CLAUDE.md — fill in the project-specific section at the bottom.
  2. Commit:
       git add CLAUDE.md claude_rules/
       git commit -m "initial: Claude rules from marc-leonti/claude-rules"
       git push
  3. From here on, sessions will read rules from claude_rules/ in this repo.

To check sync status against the live rules repo at any time:
  python3 claude_rules/claude_rules_sync.py

To update rules from this project (after a new lesson is earned):
  Edit claude_rules/<file>, commit, then on a desktop with both repos:
    cp claude_rules/<file>  ../claude-rules/<file>
    cd ../claude-rules && git commit -am "sync from <project>" && git push
EOF
