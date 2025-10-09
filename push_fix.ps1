# push_fix.ps1
# Usage: Open PowerShell in the project root and run: .\push_fix.ps1

function Bail($msg) {
    Write-Host $msg -ForegroundColor Red
    exit 1
}

# Check for git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Bail "Git is not installed or not in PATH. Install Git for Windows (https://git-scm.com/download/win) and re-run this script."
}

# Show current branch
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if ($LASTEXITCODE -ne 0) { Bail "Failed to determine current git branch." }
Write-Host "Current branch: $branch"

# Stage the file
git add generate_documents.py
if ($LASTEXITCODE -ne 0) { Bail "Failed to stage generate_documents.py" }

# Commit
$commitMsg = "Fix: remove accidental code fence wrapper from generate_documents.py"
# Only commit if there are staged changes
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "No staged changes to commit." -ForegroundColor Yellow
} else {
    git commit -m "$commitMsg"
    if ($LASTEXITCODE -ne 0) { Bail "git commit failed." }
    Write-Host "Committed: $commitMsg" -ForegroundColor Green
}

# Push to origin (current branch)
Write-Host "Pushing to origin/$branch..."
git push origin $branch
if ($LASTEXITCODE -ne 0) { Bail "git push failed. Check your remote and credentials." }
Write-Host "Push complete." -ForegroundColor Green
