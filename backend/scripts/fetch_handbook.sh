#!/usr/bin/env bash
# Clone the public GitLab handbook (markdown only, latest commit only) into backend/data/handbook.
#
# The handbook changes daily. This script records the commit it fetched in
# data/handbook/SNAPSHOT.txt so every eval result can name the exact corpus it ran on.
#
# The handbook is GitLab's content. Read the LICENSE file in the cloned repo
# before redistributing any of it; this project does not commit or republish it.
set -euo pipefail

REPO_URL="${HANDBOOK_REPO_URL:-https://gitlab.com/gitlab-com/content-sites/handbook.git}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/data/handbook"

if [ -d "$DEST/.git" ]; then
  echo "Updating existing clone in $DEST"
  git -C "$DEST" pull --depth 1 --ff-only
else
  mkdir -p "$(dirname "$DEST")"
  git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" "$DEST"
  git -C "$DEST" sparse-checkout set content/handbook
fi

{
  echo "repo:   $REPO_URL"
  echo "commit: $(git -C "$DEST" rev-parse HEAD)"
  echo "date:   $(git -C "$DEST" log -1 --format=%cI)"
} > "$DEST/SNAPSHOT.txt"

cat "$DEST/SNAPSHOT.txt"
if [ ! -d "$DEST/content/handbook" ]; then
  echo "Expected $DEST/content/handbook but it is missing. Top level of the clone:" >&2
  git -C "$DEST" ls-tree --name-only HEAD >&2
  exit 1
fi
echo "Markdown pages: $(find "$DEST/content/handbook" -name '*.md' | wc -l)"
echo "Next: python -m scripts.validate_golden_set && python -m scripts.ingest --dry-run"
