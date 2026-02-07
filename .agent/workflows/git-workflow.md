---
description: Git version control workflow with branching strategies and best practices
---

# Git Workflow & Best Practices

## Initial Setup

### 1. Configure Git Identity
// turbo
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Useful Aliases
```powershell
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm "commit -m"
git config --global alias.lg "log --oneline --graph --decorate -20"
git config --global alias.last "log -1 HEAD --stat"
```

---

## Daily Workflow

### Starting New Work

1. **Sync with remote**
// turbo
```powershell
git fetch origin
git pull origin main
```

2. **Create feature branch**
```powershell
git checkout -b feature/descriptive-name
# Naming conventions:
# - feature/add-user-auth
# - bugfix/fix-login-error
# - hotfix/critical-security-patch
# - refactor/cleanup-api-layer
# - docs/update-readme
```

### Making Changes

3. **Check status frequently**
// turbo
```powershell
git status
git diff
```

4. **Stage changes**
```powershell
# Stage specific files
git add path/to/file.py

# Stage all changes
git add .

# Interactive staging (pick specific hunks)
git add -p
```

5. **Commit with meaningful messages**
```powershell
git commit -m "type(scope): brief description

- Detailed bullet point 1
- Detailed bullet point 2

Closes #123"
```

**Commit Message Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Syncing & Pushing

6. **Stay updated with main**
```powershell
git fetch origin
git rebase origin/main
# OR if you prefer merge
git merge origin/main
```

7. **Push changes**
```powershell
git push origin feature/descriptive-name

# First push of new branch
git push -u origin feature/descriptive-name
```

---

## Branching Strategy (Git Flow Simplified)

```
main ────────────────●───────────●───────────●
                    /           /           /
develop ──────●────●───●───────●───────────●
             /        \       /
feature/a ──●          \     /
                        \   /
feature/b ──────────●────●
```

### Main Branches
- `main`: Production-ready code
- `develop`: Integration branch for features (optional)

### Supporting Branches
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes
- `release/*`: Release preparation

---

## Common Operations

### Undo Last Commit (Keep Changes)
```powershell
git reset --soft HEAD~1
```

### Undo Last Commit (Discard Changes)
```powershell
git reset --hard HEAD~1
```

### Discard Uncommitted Changes
```powershell
# Specific file
git checkout -- path/to/file

# All files
git checkout -- .

# Modern alternative
git restore path/to/file
```

### Stash Changes
```powershell
# Stash current changes
git stash

# Stash with message
git stash save "WIP: working on feature X"

# List stashes
git stash list

# Apply latest stash
git stash pop

# Apply specific stash
git stash apply stash@{2}
```

### Cherry-pick Commits
```powershell
git cherry-pick <commit-hash>
```

### Interactive Rebase (Clean Up History)
```powershell
git rebase -i HEAD~5

# Commands:
# pick = use commit
# reword = edit commit message
# squash = combine with previous
# drop = remove commit
```

### View History
```powershell
# Compact log
git log --oneline -20

# Graph view
git log --oneline --graph --all -20

# Detailed log with stats
git log --stat -5

# Search commits
git log --grep="keyword"
git log -S "code_snippet"
```

---

## Merge vs Rebase

### When to Merge
- Public/shared branches
- Preserving complete history
- Feature branch into main

```powershell
git checkout main
git merge feature/my-feature
```

### When to Rebase
- Private/local branches
- Clean, linear history
- Updating feature branch with main

```powershell
git checkout feature/my-feature
git rebase main
```

---

## Handling Conflicts

1. **Identify conflicts**
```powershell
git status
# Look for "both modified" files
```

2. **Open conflicting files and resolve**
```
<<<<<<< HEAD
Your changes
=======
Their changes
>>>>>>> branch-name
```

3. **Mark as resolved**
```powershell
git add path/to/resolved-file
```

4. **Continue rebase/merge**
```powershell
git rebase --continue
# OR
git merge --continue
```

5. **Abort if needed**
```powershell
git rebase --abort
git merge --abort
```

---

## Pull Request Checklist

Before creating PR:
- [ ] Code compiles/runs without errors
- [ ] All tests pass
- [ ] No debug prints or commented code
- [ ] Meaningful commit messages
- [ ] Branch is up-to-date with main
- [ ] Self-review completed
- [ ] Documentation updated if needed

---

## Git Hooks (Automation)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/sh
# Run linting before commit
python -m ruff check .
if [ $? -ne 0 ]; then
    echo "Linting failed. Fix issues before committing."
    exit 1
fi
```

Or use pre-commit framework (see python-setup.md)

---

## Emergency Commands

### Force Push (Use with Caution!)
```powershell
git push --force-with-lease origin branch-name
# Safer than --force, fails if remote has new commits
```

### Recover Deleted Branch
```powershell
git reflog
git checkout -b recovered-branch <commit-hash>
```

### Find Who Changed What
```powershell
git blame path/to/file
```

### Search All Commits for Code
```powershell
git log -S "search_string" --all
```
