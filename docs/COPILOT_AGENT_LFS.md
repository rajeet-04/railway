# Copilot Agent: Git LFS Rule & Setup

This document explains how to enable Git Large File Storage (LFS) for this repository and provides guidance for Copilot Agents and automation to ensure large files are handled correctly on git push.

Why Git LFS
- This repo contains large artifacts (for example `database/railway.db`, large JSON datasets, or static assets). Tracking these files with Git LFS avoids blowing up repository history and helps with efficient transfers.

What to add to the repo
1. `.gitattributes` (already present) contains patterns to track files with Git LFS, e.g. `database/*.db`, `data/*.json`, `public/assets/*`.
2. `scripts/enable_git_lfs.sh` and `scripts/enable_git_lfs.ps1` provide a portable way to enable Git LFS and commit `.gitattributes`.

Agent rule (how Copilot Agents should behave)
- Before any `git push`, the agent must ensure Git LFS is installed and initialized in the environment. Steps:
  1. Run `git lfs install --local` in the repository root.
  2. Ensure `.gitattributes` is present and staged/committed.
  3. If the agent is adding new large files, it should either:
     - Rely on `.gitattributes` to mark them on next `git add`/`git commit`, or
     - Run `git lfs track "pattern"` for new patterns and commit the `.gitattributes` change.
  4. For pre-existing large files that must be converted to LFS pointers, run (manual/destructive):
     `git lfs migrate import --include="database/*.db,data/*.json,public/assets/*"`
     Note: this rewrites local history and should be used with care.

Example agent workflow (pseudo):

- Setup:
  - Run: `./scripts/enable_git_lfs.sh` (Unix) or `./scripts/enable_git_lfs.ps1` (Windows PowerShell).

- On add/commit/push:
  - Ensure files matching `.gitattributes` are added normally (git will create LFS pointer files automatically on commit).
  - Commit the changes. The agent should not try to upload large files directly via API; normal `git push` will handle LFS objects.


GitHub Actions preconfiguration for Copilot Agents
-------------------------------------------------
To preconfigure Copilot's environment before an agent runs, add a special workflow file at `.github/workflows/copilot-setup-steps.yml`.
This repo includes such a workflow which checks out the repository with `lfs: true` and ensures `git-lfs` is installed and initialized.

The workflow is simple and uses `actions/checkout@v5` with `with: lfs: true` and a step to run `git lfs install --system`.
This guarantees that Copilot Agents launched by GitHub will have access to LFS objects.

Example (already added to this repo): `.github/workflows/copilot-setup-steps.yml`

CI/Runner notes:
- Many GitHub-hosted runners already have `git-lfs` installed. The workflow includes an install step for safety.
- If your organization uses self-hosted runners, ensure `git-lfs` is installed on the runner images and that the runner user can `git lfs install`.

References
- GitHub Copilot Agents customization: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment#enabling-git-large-file-storage-lfs
- Git LFS official: https://git-lfs.github.com/

Support
- If you want, I can add a CI job snippet to verify LFS is enabled and `.gitattributes` is committed before pushes.
