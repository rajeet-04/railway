# PowerShell script to enable Git LFS for this repository
# Usage: .\scripts\enable_git_lfs.ps1

param()

function Ensure-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error 'git not found. Please install Git.'
        exit 1
    }
}

function Ensure-GitLfs {
    if (-not (Get-Command git-lfs -ErrorAction SilentlyContinue)) {
        Write-Output 'Git LFS not found. Installing via package manager if available...'
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            choco install git-lfs -y
        } elseif (Get-Command winget -ErrorAction SilentlyContinue) {
            winget install --id Git.GitLFS -e --source winget
        } else {
            Write-Error 'Please install Git LFS manually: https://git-lfs.github.com/'
            exit 1
        }
    }
}

Ensure-Git
Ensure-GitLfs

# Initialize LFS for repo
git lfs install --local

if (-not (Test-Path .gitattributes)) {
    Write-Error '.gitattributes not found in repository root. Add it before running this script.'
    exit 1
}

# Stage .gitattributes
git add .gitattributes
try {
    git commit -m "chore: add .gitattributes for Git LFS tracking" -q
} catch {
    # ignore commit failure (nothing to commit)
}

Write-Output 'Git LFS enabled locally. To migrate existing large files into LFS pointers consider running:'
Write-Output '  git lfs migrate import --include="database/*.db,data/*.json,public/assets/*"'
