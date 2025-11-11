# ============================================================================
# Release Script - Automate Release Process
# ============================================================================
# 
# This script automates the release process:
# 1. Validates current state
# 2. Creates release branch
# 3. Bumps version in files
# 4. Creates git tag
# 5. Builds Docker images
# 6. Pushes to registry
# 
# Usage:
#   .\scripts\release.ps1 -Version "1.3.0" -Type "minor"
#   .\scripts\release.ps1 -Version "1.2.1" -Type "patch"
#   .\scripts\release.ps1 -Version "2.0.0" -Type "major"
# 
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("major", "minor", "patch", "rc")]
    [string]$Type = "minor",
    
    [Parameter(Mandatory=$false)]
    [string]$DockerRegistry = "octavianissuemonitoring",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

# Colors
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"

Write-Host "🚀 Parser Law - Release Automation" -ForegroundColor $ColorInfo
Write-Host "====================================" -ForegroundColor $ColorInfo
Write-Host ""
Write-Host "Version: v$Version" -ForegroundColor White
Write-Host "Type:    $Type" -ForegroundColor White
Write-Host "Registry: $DockerRegistry" -ForegroundColor White
Write-Host ""

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+(-rc\.\d+)?$') {
    Write-Host "❌ Invalid version format: $Version" -ForegroundColor $ColorError
    Write-Host "   Expected: MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-rc.N" -ForegroundColor $ColorWarning
    Write-Host "   Examples: 1.3.0, 1.2.1, 2.0.0-rc.1" -ForegroundColor $ColorWarning
    exit 1
}

# Extract version components
if ($Version -match '^(\d+)\.(\d+)\.(\d+)(-rc\.(\d+))?$') {
    $MajorVersion = $Matches[1]
    $MinorVersion = $Matches[2]
    $PatchVersion = $Matches[3]
    $IsRC = $Matches[4] -ne $null
    $RCNumber = if ($IsRC) { $Matches[5] } else { $null }
} else {
    Write-Host "❌ Failed to parse version: $Version" -ForegroundColor $ColorError
    exit 1
}

Write-Host "📋 Step 1: Pre-Release Validation" -ForegroundColor $ColorWarning
Write-Host "===================================" -ForegroundColor $ColorWarning
Write-Host ""

# Check if on develop branch
$currentBranch = git branch --show-current
if ($currentBranch -ne "develop" -and -not $DryRun) {
    Write-Host "⚠️  Warning: Not on develop branch (current: $currentBranch)" -ForegroundColor $ColorWarning
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        Write-Host "❌ Aborted by user" -ForegroundColor $ColorError
        exit 1
    }
}
Write-Host "✅ Current branch: $currentBranch" -ForegroundColor $ColorSuccess

# Check for uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus -and -not $DryRun) {
    Write-Host "❌ Uncommitted changes detected:" -ForegroundColor $ColorError
    Write-Host $gitStatus -ForegroundColor $ColorWarning
    Write-Host "   Commit or stash changes before release" -ForegroundColor $ColorWarning
    exit 1
}
Write-Host "✅ No uncommitted changes" -ForegroundColor $ColorSuccess

# Check if tag already exists
$tagExists = git tag -l "v$Version"
if ($tagExists) {
    Write-Host "❌ Tag v$Version already exists" -ForegroundColor $ColorError
    Write-Host "   Use a different version number or delete the tag:" -ForegroundColor $ColorWarning
    Write-Host "   git tag -d v$Version && git push origin :refs/tags/v$Version" -ForegroundColor $ColorWarning
    exit 1
}
Write-Host "✅ Tag v$Version is available" -ForegroundColor $ColorSuccess

# Pull latest changes
Write-Host ""
Write-Host "Pulling latest changes..." -ForegroundColor $ColorInfo
git pull origin $currentBranch
Write-Host "✅ Up to date with remote" -ForegroundColor $ColorSuccess

Write-Host ""
Write-Host "📦 Step 2: Create Release Branch" -ForegroundColor $ColorWarning
Write-Host "==================================" -ForegroundColor $ColorWarning
Write-Host ""

$releaseBranch = "release/$Version"

if ($DryRun) {
    Write-Host "[DRY RUN] Would create branch: $releaseBranch" -ForegroundColor $ColorWarning
} else {
    git checkout -b $releaseBranch
    Write-Host "✅ Created branch: $releaseBranch" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🔢 Step 3: Bump Version Numbers" -ForegroundColor $ColorWarning
Write-Host "=================================" -ForegroundColor $ColorWarning
Write-Host ""

# Update version in main.py
$mainPyPath = "db_service\app\main.py"
if (Test-Path $mainPyPath) {
    $mainPyContent = Get-Content $mainPyPath -Raw
    $mainPyContent = $mainPyContent -replace '__version__ = "[^"]+"', "__version__ = `"$Version`""
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would update: $mainPyPath" -ForegroundColor $ColorWarning
    } else {
        Set-Content $mainPyPath -Value $mainPyContent -NoNewline
        Write-Host "✅ Updated: $mainPyPath" -ForegroundColor $ColorSuccess
    }
} else {
    Write-Host "⚠️  File not found: $mainPyPath" -ForegroundColor $ColorWarning
}

# Update version in pyproject.toml
$pyprojectPath = "pyproject.toml"
if (Test-Path $pyprojectPath) {
    $pyprojectContent = Get-Content $pyprojectPath -Raw
    $pyprojectContent = $pyprojectContent -replace 'version = "[^"]+"', "version = `"$Version`""
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would update: $pyprojectPath" -ForegroundColor $ColorWarning
    } else {
        Set-Content $pyprojectPath -Value $pyprojectContent -NoNewline
        Write-Host "✅ Updated: $pyprojectPath" -ForegroundColor $ColorSuccess
    }
} else {
    Write-Host "⚠️  File not found: $pyprojectPath" -ForegroundColor $ColorWarning
}

# Update CHANGELOG.md
$changelogPath = "CHANGELOG.md"
$releaseDate = Get-Date -Format "yyyy-MM-dd"

if (Test-Path $changelogPath) {
    $changelogContent = Get-Content $changelogPath -Raw
    
    # Add new version section after [Unreleased]
    $newSection = @"

## [$Version] - $releaseDate

### Added
- TODO: Document new features

### Changed
- TODO: Document changes

### Fixed
- TODO: Document bug fixes

"@
    
    $changelogContent = $changelogContent -replace '(## \[Unreleased\].*?)(\n\n##)', "`$1$newSection`$2"
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would update: $changelogPath" -ForegroundColor $ColorWarning
    } else {
        Set-Content $changelogPath -Value $changelogContent -NoNewline
        Write-Host "✅ Updated: $changelogPath" -ForegroundColor $ColorSuccess
        Write-Host "   ⚠️  Please edit CHANGELOG.md and document changes!" -ForegroundColor $ColorWarning
    }
} else {
    Write-Host "⚠️  File not found: $changelogPath (will create)" -ForegroundColor $ColorWarning
    
    $newChangelog = @"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [$Version] - $releaseDate

### Added
- Initial release

[$Version]: https://github.com/octavianissuemonitoring/parser-law/releases/tag/v$Version
"@
    
    if (-not $DryRun) {
        Set-Content $changelogPath -Value $newChangelog
        Write-Host "✅ Created: $changelogPath" -ForegroundColor $ColorSuccess
    }
}

Write-Host ""
Write-Host "📝 Step 4: Commit Version Bump" -ForegroundColor $ColorWarning
Write-Host "================================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would commit version bump changes" -ForegroundColor $ColorWarning
} else {
    git add $mainPyPath $pyprojectPath $changelogPath
    git commit -m "chore: Bump version to $Version"
    Write-Host "✅ Committed version bump" -ForegroundColor $ColorSuccess
    
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit CHANGELOG.md now!" -ForegroundColor $ColorWarning
    Write-Host "   Document what changed in this release" -ForegroundColor $ColorWarning
    Write-Host ""
    $continue = Read-Host "Press Enter when done, or 's' to skip"
    
    if ($continue -ne "s") {
        # Amend commit with changelog updates
        git add $changelogPath
        git commit --amend --no-edit
        Write-Host "✅ Updated commit with changelog" -ForegroundColor $ColorSuccess
    }
}

Write-Host ""
Write-Host "🧪 Step 5: Run Tests" -ForegroundColor $ColorWarning
Write-Host "=====================" -ForegroundColor $ColorWarning
Write-Host ""

if ($SkipTests) {
    Write-Host "⏭️  Skipped tests (--SkipTests flag)" -ForegroundColor $ColorWarning
} elseif ($DryRun) {
    Write-Host "[DRY RUN] Would run tests" -ForegroundColor $ColorWarning
} else {
    Write-Host "Running pytest..." -ForegroundColor $ColorInfo
    
    # Activate virtual environment
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
    }
    
    # Run tests
    $testResult = pytest tests/ -v
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Tests failed!" -ForegroundColor $ColorError
        Write-Host "   Fix tests before continuing release" -ForegroundColor $ColorWarning
        exit 1
    }
    
    Write-Host "✅ All tests passed" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🔀 Step 6: Merge to Master" -ForegroundColor $ColorWarning
Write-Host "============================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would merge to master" -ForegroundColor $ColorWarning
} else {
    # Push release branch
    git push -u origin $releaseBranch
    Write-Host "✅ Pushed release branch to remote" -ForegroundColor $ColorSuccess
    
    Write-Host ""
    Write-Host "Merging to master..." -ForegroundColor $ColorInfo
    git checkout master
    git pull origin master
    git merge --no-ff $releaseBranch -m "Release v$Version"
    Write-Host "✅ Merged to master" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🏷️  Step 7: Create Git Tag" -ForegroundColor $ColorWarning
Write-Host "============================" -ForegroundColor $ColorWarning
Write-Host ""

$tagMessage = @"
Release v$Version

Changes:
- See CHANGELOG.md for details

Type: $Type
Date: $releaseDate
"@

if ($DryRun) {
    Write-Host "[DRY RUN] Would create tag: v$Version" -ForegroundColor $ColorWarning
    Write-Host "Message:" -ForegroundColor $ColorWarning
    Write-Host $tagMessage -ForegroundColor Gray
} else {
    git tag -a "v$Version" -m $tagMessage
    Write-Host "✅ Created tag: v$Version" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🐳 Step 8: Build Docker Images" -ForegroundColor $ColorWarning
Write-Host "================================" -ForegroundColor $ColorWarning
Write-Host ""

$imageName = "$DockerRegistry/parser-law"

if ($DryRun) {
    Write-Host "[DRY RUN] Would build Docker images:" -ForegroundColor $ColorWarning
    Write-Host "  - $imageName:$Version" -ForegroundColor Gray
    Write-Host "  - $imageName:$MajorVersion.$MinorVersion" -ForegroundColor Gray
    Write-Host "  - $imageName:$MajorVersion" -ForegroundColor Gray
    if (-not $IsRC) {
        Write-Host "  - $imageName:latest" -ForegroundColor Gray
    }
} else {
    Write-Host "Building Docker image (this may take 2-3 minutes)..." -ForegroundColor $ColorInfo
    
    Push-Location db_service
    
    # Build with full version tag
    docker build -t "${imageName}:${Version}" .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed" -ForegroundColor $ColorError
        Pop-Location
        exit 1
    }
    
    Write-Host "✅ Built: ${imageName}:${Version}" -ForegroundColor $ColorSuccess
    
    # Create additional tags (not for RC versions)
    if (-not $IsRC) {
        docker tag "${imageName}:${Version}" "${imageName}:${MajorVersion}.${MinorVersion}"
        Write-Host "✅ Tagged: ${imageName}:${MajorVersion}.${MinorVersion}" -ForegroundColor $ColorSuccess
        
        docker tag "${imageName}:${Version}" "${imageName}:${MajorVersion}"
        Write-Host "✅ Tagged: ${imageName}:${MajorVersion}" -ForegroundColor $ColorSuccess
        
        docker tag "${imageName}:${Version}" "${imageName}:latest"
        Write-Host "✅ Tagged: ${imageName}:latest" -ForegroundColor $ColorSuccess
    }
    
    Pop-Location
}

Write-Host ""
Write-Host "📤 Step 9: Push to Registry" -ForegroundColor $ColorWarning
Write-Host "=============================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would push images to registry" -ForegroundColor $ColorWarning
} else {
    Write-Host "Pushing to Docker Hub..." -ForegroundColor $ColorInfo
    Write-Host "(Make sure you're logged in: docker login)" -ForegroundColor $ColorWarning
    Write-Host ""
    
    # Push full version
    docker push "${imageName}:${Version}"
    Write-Host "✅ Pushed: ${imageName}:${Version}" -ForegroundColor $ColorSuccess
    
    # Push rolling tags (not for RC)
    if (-not $IsRC) {
        docker push "${imageName}:${MajorVersion}.${MinorVersion}"
        Write-Host "✅ Pushed: ${imageName}:${MajorVersion}.${MinorVersion}" -ForegroundColor $ColorSuccess
        
        docker push "${imageName}:${MajorVersion}"
        Write-Host "✅ Pushed: ${imageName}:${MajorVersion}" -ForegroundColor $ColorSuccess
        
        docker push "${imageName}:latest"
        Write-Host "✅ Pushed: ${imageName}:latest" -ForegroundColor $ColorSuccess
    }
}

Write-Host ""
Write-Host "🔄 Step 10: Merge Back to Develop" -ForegroundColor $ColorWarning
Write-Host "===================================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would merge back to develop" -ForegroundColor $ColorWarning
} else {
    git checkout develop
    git pull origin develop
    git merge --no-ff master -m "Merge release v$Version back to develop"
    Write-Host "✅ Merged back to develop" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🗑️  Step 11: Cleanup Release Branch" -ForegroundColor $ColorWarning
Write-Host "=====================================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would delete release branch" -ForegroundColor $ColorWarning
} else {
    git branch -d $releaseBranch
    git push origin --delete $releaseBranch
    Write-Host "✅ Deleted release branch" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "☁️  Step 12: Push Everything" -ForegroundColor $ColorWarning
Write-Host "=============================" -ForegroundColor $ColorWarning
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would push master, develop, and tags" -ForegroundColor $ColorWarning
} else {
    git checkout master
    git push origin master
    git push origin "v$Version"
    
    git checkout develop
    git push origin develop
    
    Write-Host "✅ Pushed all changes to GitHub" -ForegroundColor $ColorSuccess
}

Write-Host ""
Write-Host "🎉 Release Complete!" -ForegroundColor $ColorSuccess
Write-Host "=====================" -ForegroundColor $ColorSuccess
Write-Host ""
Write-Host "📦 Release Information:" -ForegroundColor $ColorInfo
Write-Host "   Version:  v$Version" -ForegroundColor White
Write-Host "   Type:     $Type" -ForegroundColor White
Write-Host "   Date:     $releaseDate" -ForegroundColor White
Write-Host "   Branch:   master" -ForegroundColor White
Write-Host ""
Write-Host "🐳 Docker Images:" -ForegroundColor $ColorInfo
Write-Host "   ${imageName}:${Version}" -ForegroundColor White
if (-not $IsRC) {
    Write-Host "   ${imageName}:${MajorVersion}.${MinorVersion}" -ForegroundColor White
    Write-Host "   ${imageName}:${MajorVersion}" -ForegroundColor White
    Write-Host "   ${imageName}:latest" -ForegroundColor White
}
Write-Host ""
Write-Host "🔗 Next Steps:" -ForegroundColor $ColorInfo
Write-Host "   1. Create GitHub Release:" -ForegroundColor White
Write-Host "      https://github.com/octavianissuemonitoring/parser-law/releases/new?tag=v$Version" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Deploy to VPS:" -ForegroundColor White
Write-Host "      ssh root@vps" -ForegroundColor Gray
Write-Host "      cd /opt/parser-law" -ForegroundColor Gray
Write-Host "      nano docker-compose.yml  # Update image: ${imageName}:${Version}" -ForegroundColor Gray
Write-Host "      docker-compose pull" -ForegroundColor Gray
Write-Host "      docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Verify deployment:" -ForegroundColor White
Write-Host "      curl http://legislatie.issuemonitoring.ro/version" -ForegroundColor Gray
Write-Host ""
Write-Host "   4. Notify users about new version" -ForegroundColor White
Write-Host ""
Write-Host "Happy releasing! 🚀" -ForegroundColor $ColorSuccess
