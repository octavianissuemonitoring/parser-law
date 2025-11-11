# Git Branching Strategy & Workflow

**Problem**: Tot codul este pe `master`. Risky - bug-uri ajung direct în production.

**Solution**: Git Flow cu branches separate pentru development și production.

---

## Branch Structure

```
master (production)
  ↑ merge only stable releases
develop (integration)
  ↑ merge features when done
feature/xyz (active development)
bugfix/xyz (bug fixes)
hotfix/xyz (urgent production fixes)
```

---

## Branch Roles

### `master` - Production Branch

**Purpose**: Only stable, tested, production-ready code

**Rules**:
- ✅ Protected (no direct commits)
- ✅ Only merges from `develop` or `hotfix/*`
- ✅ Every merge = new version tag (v1.0.0, v1.1.0)
- ✅ Automatically deployed to VPS

**Current Code on VPS**: Always from `master`

---

### `develop` - Integration Branch

**Purpose**: Integration of all features, testing ground before production

**Rules**:
- ✅ Semi-protected (PR required)
- ✅ Merges from `feature/*` branches
- ✅ Continuous testing happens here
- ✅ When stable → merge to `master`

**Current Status**: We need to create this!

---

### `feature/*` - Feature Development Branches

**Purpose**: Individual features or improvements

**Naming**: `feature/<short-description>`
- `feature/categories-api`
- `feature/metadata-extractor`
- `feature/export-endpoint`

**Rules**:
- ✅ Branch from `develop`
- ✅ One feature per branch
- ✅ Delete after merge

**Workflow**:
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
# ... develop ...
git add .
git commit -m "feat: My feature"
git push origin feature/my-feature
# Create PR to develop
```

---

### `bugfix/*` - Bug Fix Branches

**Purpose**: Fix non-critical bugs found in `develop`

**Naming**: `bugfix/<issue-number>-<description>`
- `bugfix/42-parser-encoding`
- `bugfix/metadata-extraction-fail`

**Rules**:
- ✅ Branch from `develop`
- ✅ Fix specific bug
- ✅ Include tests
- ✅ Delete after merge

---

### `hotfix/*` - Emergency Production Fixes

**Purpose**: Critical bugs found in production (on `master`)

**Naming**: `hotfix/<version>-<critical-issue>`
- `hotfix/1.0.1-database-connection`
- `hotfix/1.0.2-security-patch`

**Rules**:
- ⚠️ Branch from `master` (not develop!)
- ⚠️ Fix ASAP
- ⚠️ Merge to BOTH `master` AND `develop`
- ⚠️ Bump version immediately

**Workflow**:
```powershell
git checkout master
git pull origin master
git checkout -b hotfix/1.0.1-critical-bug
# ... fix ...
git commit -m "fix: Critical bug"
git push origin hotfix/1.0.1-critical-bug
# Merge to master (bump version to 1.0.1)
# Merge to develop (keep in sync)
```

---

## Complete Workflow Examples

### Scenario 1: New Feature Development

```powershell
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/search-by-category

# 3. Develop locally (with docker-compose.dev.yml running)
# Edit code, test locally, iterate

# 4. Commit small, logical changes
git add db_service/app/routes/acte.py
git commit -m "feat(acte): Add category search endpoint"

git add tests/test_acte_search.py
git commit -m "test(acte): Add tests for category search"

# 5. Push to GitHub
git push origin feature/search-by-category

# 6. Create Pull Request (GitHub UI)
# Title: "feat: Add category search endpoint"
# Base: develop
# Compare: feature/search-by-category

# 7. Code review, feedback, adjustments
git add .
git commit -m "refactor: Address review feedback"
git push origin feature/search-by-category

# 8. Merge to develop (GitHub UI or CLI)
# After merge, delete feature branch

# 9. Delete local branch
git checkout develop
git pull origin develop
git branch -d feature/search-by-category
```

---

### Scenario 2: Bug Fix

```powershell
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create bugfix branch
git checkout -b bugfix/42-metadata-extraction

# 3. Fix bug locally
# Edit code, test locally

# 4. Write test to prevent regression
# Add test in tests/

# 5. Commit
git add metadata_extractor.py tests/test_metadata_extractor.py
git commit -m "fix(parser): Fix metadata extraction for ORDIN

- Handle missing publication date
- Add test for edge case
- Closes #42"

# 6. Push and create PR to develop
git push origin bugfix/42-metadata-extraction

# 7. After merge, delete branch
git checkout develop
git pull origin develop
git branch -d bugfix/42-metadata-extraction
```

---

### Scenario 3: Release to Production

```powershell
# 1. Ensure develop is stable
git checkout develop
git pull origin develop

# Run all tests locally
pytest tests/ -v
# All green? Proceed.

# 2. Merge develop → master
git checkout master
git pull origin master
git merge develop --no-ff -m "release: Version 1.1.0"

# 3. Tag the release
git tag -a v1.1.0 -m "Release v1.1.0

Features:
- Category search endpoint
- Improved metadata extraction
- Export for analysis

Fixes:
- Parser encoding issues
- Database connection stability

Database migrations:
- Add category_id column to acte

Deployment notes:
- Run 'alembic upgrade head' on VPS
- Restart API service"

# 4. Push to GitHub
git push origin master
git push origin master --tags

# 5. Deploy to VPS
ssh root@77.237.235.158
cd /opt/parser-law
git fetch --all
git checkout v1.1.0
docker-compose restart api
curl http://localhost:8000/health

# 6. Sync develop with master (in case of hotfixes)
git checkout develop
git merge master --no-ff -m "chore: Sync develop with master v1.1.0"
git push origin develop
```

---

### Scenario 4: Hotfix (Critical Production Bug)

```powershell
# URGENT: Production is down!

# 1. Branch from master
git checkout master
git pull origin master
git checkout -b hotfix/1.1.1-api-crash

# 2. Fix critical bug
# Edit code, test locally

# 3. Commit immediately
git add db_service/app/main.py
git commit -m "fix: Prevent API crash on null category

Critical fix for production issue.
Error was caused by unhandled null in category filter."

# 4. Push
git push origin hotfix/1.1.1-api-crash

# 5. Merge to master ASAP
git checkout master
git merge hotfix/1.1.1-api-crash --no-ff -m "hotfix: v1.1.1 - Fix API crash"

# 6. Tag hotfix version
git tag -a v1.1.1 -m "Hotfix v1.1.1 - Fix API crash"

# 7. Push to production
git push origin master
git push origin master --tags

# 8. Deploy to VPS immediately
ssh root@77.237.235.158
cd /opt/parser-law
git fetch --all
git checkout v1.1.1
docker-compose restart api

# 9. IMPORTANT: Merge to develop too!
git checkout develop
git merge hotfix/1.1.1-api-crash --no-ff -m "hotfix: Merge v1.1.1 to develop"
git push origin develop

# 10. Delete hotfix branch
git branch -d hotfix/1.1.1-api-crash
git push origin --delete hotfix/1.1.1-api-crash
```

---

## Setting Up Branch Protection

### On GitHub (Recommended)

1. Go to: `https://github.com/octavianissuemonitoring/parser-law/settings/branches`

2. **Protect `master` branch**:
   ```
   ✅ Require pull request before merging
   ✅ Require approvals (1)
   ✅ Require status checks to pass
   ✅ Require branches to be up to date
   ✅ Do not allow bypassing the above settings
   ```

3. **Protect `develop` branch** (semi-protected):
   ```
   ✅ Require pull request before merging
   ⚪ Require approvals (optional for solo dev)
   ✅ Require status checks to pass
   ```

---

## Initial Migration (From Current State)

### Current State
```
master (has all code, latest commit 3bdaaff)
  ↓
No other branches
```

### Migration Steps

```powershell
# 1. Current master becomes our baseline
git checkout master
git pull origin master

# 2. Create develop branch from master
git checkout -b develop
git push origin develop

# 3. Set develop as default branch (GitHub UI)
# Settings → Branches → Default branch → develop

# 4. From now on, all new work branches from develop
git checkout develop
git checkout -b feature/my-first-feature

# 5. Master is now protected (only releases)
```

**Timeline**:
- **Now**: Both `master` and `develop` are identical (v1.0-stable)
- **Future**: `develop` gets new features, `master` only gets releases

---

## Commit Message Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance (dependencies, config)
- `perf`: Performance improvement
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples

**Feature**:
```
feat(acte): Add category search endpoint

Implement GET /api/v1/acte?category=<id> endpoint.
Returns filtered acte by category with pagination.

Closes #42
```

**Bug Fix**:
```
fix(parser): Handle missing publication date

Parser crashed when MOF HTML didn't contain publication date.
Now returns None and logs warning instead.

Fixes #58
```

**Refactor**:
```
refactor(metadata): Extract metadata logic to separate class

Move metadata extraction from hybrid_parser.py to metadata_extractor.py.
Reduces code duplication by 150 lines.

Part of refactoring initiative.
```

**Documentation**:
```
docs: Add local development setup guide

Create LOCAL_DEVELOPMENT.md with:
- Docker Compose setup
- VS Code integration
- Troubleshooting guide

Helps onboard new developers.
```

---

## Version Numbering (Semantic Versioning)

### Format: `MAJOR.MINOR.PATCH[-PRERELEASE]`

- **MAJOR** (1.x.x): Breaking changes, API incompatible
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes only
- **PRERELEASE** (x.x.x-rc.N): Release candidates for testing

### Examples

- `v1.0.0` → `v1.1.0`: Added category search (new feature)
- `v1.1.0` → `v1.1.1`: Fixed parser bug (bugfix)
- `v1.1.1` → `v1.2.0-rc.1`: Testing new export feature (release candidate)
- `v1.2.0-rc.1` → `v1.2.0`: Stable release after testing
- `v1.2.0` → `v2.0.0`: Changed API response format (breaking)

### Current Version
```
v1.0.0 (stable baseline)
  ↓
v1.1.0-rc.1 (release candidate)
  ↓
v1.1.0 (next release with refactoring)
  ↓
v1.2.0 (categories + export features)
  ↓
v2.0.0 (future: API v2)
```

### Multi-Version Deployment

See **`RELEASE_MANAGEMENT.md`** for complete strategy:
- Multiple clients on different versions simultaneously
- Docker image tagging strategy
- Rollback procedures
- Database schema versioning
- Automated release process

**Example**:
- Client A → `v1.2.0` (stable, conservative)
- Client B → `v1.3.0` (latest features)
- Staging → `v1.4.0-rc.1` (testing next release)

---

## Visual Workflow Diagram

```
Time →

develop:   ─●─────●─────●─────●─────────────●─────────→
            │     │     │     │             │
            │     │     │     └─ bugfix     │
            │     │     └─ feature 2        │
            │     └─ feature 1              │
            │                                │
            └─ initial                       └─ merge to master
                                             ↓
master:    ─────────────────────────────────●─────────→
                                         v1.1.0 tag


hotfix:                                  ●───●
                                         │   │
                                         │   └─ merge back to develop
                                         │
                                         └─ merge to master (v1.1.1)
```

---

## Branch Cleanup

### Delete Merged Branches (Local)
```powershell
# List merged branches
git branch --merged develop

# Delete specific branch
git branch -d feature/my-feature

# Delete all merged branches (except develop/master)
git branch --merged develop | Select-String -Pattern "develop|master" -NotMatch | ForEach-Object { git branch -d $_.ToString().Trim() }
```

### Delete Remote Branches
```powershell
# Delete on GitHub
git push origin --delete feature/my-feature

# Prune deleted remote branches locally
git fetch --prune
```

---

## Daily Workflow Summary

### Morning (Start Work)
```powershell
# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/my-task

# 3. Start local env
docker-compose -f docker-compose.dev.yml up -d
```

### During Day (Iterate)
```powershell
# Edit code → Test locally → Commit
git add .
git commit -m "feat: Add feature X"

# Push periodically (backup)
git push origin feature/my-task
```

### End of Day (Checkpoint)
```powershell
# Push all commits
git push origin feature/my-task

# Stop local env
docker-compose -f docker-compose.dev.yml down
```

### When Feature Done
```powershell
# Create PR on GitHub
# Title: "feat: My feature"
# Base: develop
# Review, merge, delete branch
```

### Weekly (Release)
```powershell
# Merge develop → master
# Tag version
# Deploy to VPS
```

---

## FAQ

### Q: Do I always need to branch from develop?

**A**: Yes, except for hotfixes (branch from master).

---

### Q: Can I commit directly to develop?

**A**: No (if protected). Always create feature branch → PR → merge.

---

### Q: What if I forgot to create a branch?

**A**:
```powershell
# You're on develop with uncommitted changes
git stash
git checkout -b feature/my-feature
git stash pop
# Now commit to feature branch
```

---

### Q: How do I test a colleague's feature branch?

**A**:
```powershell
git fetch origin
git checkout feature/colleague-feature
docker-compose -f docker-compose.dev.yml up -d
# Test locally
```

---

### Q: Can I work on multiple features simultaneously?

**A**: Yes!
```powershell
# Feature 1
git checkout -b feature/task-1
# ... work ...
git stash

# Feature 2
git checkout develop
git checkout -b feature/task-2
# ... work ...

# Back to feature 1
git checkout feature/task-1
git stash pop
```

---

## Summary: Why This Workflow?

### Benefits

1. **Safety**: Master is always stable
2. **Parallel Work**: Multiple features in progress
3. **Review**: PRs catch issues before merge
4. **Rollback**: Easy to revert bad features
5. **History**: Clear what changed when
6. **CI/CD**: Can automate tests on PR
7. **Team Ready**: Scales to 5-10 developers

### Comparison

| Aspect | Current (Master Only) | New (Git Flow) |
|--------|----------------------|----------------|
| **Safety** | ❌ Risk breaking prod | ✅ Protected master |
| **Parallel** | ❌ Hard to work together | ✅ Feature branches |
| **Review** | ❌ No review process | ✅ PR required |
| **Rollback** | ❌ Revert commits messy | ✅ Merge whole feature |
| **Testing** | ❌ Test în production | ✅ Test in develop first |
| **History** | ❌ Mixed WIP + stable | ✅ Clear releases |

---

## Next Steps

### Immediate (Today)

1. **Create `develop` branch**:
```powershell
git checkout master
git checkout -b develop
git push origin develop
```

2. **Set branch protection** on GitHub

3. **Create first feature branch**:
```powershell
git checkout -b feature/local-dev-setup
# Test local development setup
git commit -m "docs: Add local development guide"
git push origin feature/local-dev-setup
```

### This Week

- ✅ All new work in feature branches
- ✅ PRs to develop
- ✅ Test locally before pushing

### Going Forward

- ✅ Weekly releases: develop → master
- ✅ Version tags (v1.1.0, v1.2.0)
- ✅ VPS deploys from master only

---

**Created**: 2025-11-11  
**Version**: 1.0.0  
**Status**: ✅ Ready to implement  
**Priority**: 🔴 HIGH - Implement before next feature
