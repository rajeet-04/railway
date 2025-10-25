#!/usr/bin/env bash
set -euo pipefail

# Enable Git LFS for this repository and track configured patterns
# Usage: ./scripts/enable_git_lfs.sh

if ! command -v git > /dev/null 2>&1; then
  echo "git not found. Install git first." >&2
  exit 1
fi

if ! command -v git-lfs > /dev/null 2>&1; then
  echo "Git LFS not found. Attempting to install..."
  if command -v apt-get > /dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y git-lfs
  elif command -v brew > /dev/null 2>&1; then
    brew install git-lfs
  else
    echo "Please install Git LFS manually: https://git-lfs.github.com/" >&2
    exit 1
  fi
fi

# Initialize Git LFS for the current user
git lfs install --local

# Ensure .gitattributes is present
if [ ! -f .gitattributes ]; then
  echo ".gitattributes not found in repo root. Please add patterns to .gitattributes before running this script." >&2
  exit 1
fi

# Add tracked patterns from .gitattributes (git lfs will read it automatically)
# But we also ensure files already matched are added to LFS tracking
# Find files that match patterns and re-add them to trigger LFS pointer tracking

# Add all files and let Git determine which are LFS-tracked according to .gitattributes
git add .gitattributes
# Re-add repository files to convert to LFS pointers where appropriate
# Use git lfs migrate import to rewrite history for existing large files (optional and destructive)
# Here we only add and commit current state; for rewriting history, run 'git lfs migrate import --include="database/*.db,data/*.json,public/assets/*"'

# Commit .gitattributes (if not already committed)
if ! git diff --cached --quiet; then
  git commit -m "chore: add .gitattributes for Git LFS tracking" || true
fi

echo "Git LFS enabled (local). Patterns from .gitattributes will be tracked on push."
echo "If you need to rewrite history to convert existing files to LFS pointers, run:\n  git lfs migrate import --include=\"database/*.db,data/*.json,public/assets/*\"\n(This rewrites local history)"
