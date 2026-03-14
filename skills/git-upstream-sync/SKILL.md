---
name: git-upstream-sync
description: Configure upstream remote and create a new branch from latest upstream for open-source contribution. Use whenever the user has forked and cloned a repo and wants to sync with upstream, add the upstream remote, or start a new branch from the latest upstream (main/master). Triggers on requests like "configure upstream", "sync with upstream", "branch from latest upstream", "准备给开源项目贡献代码", "基于上游拉新分支", or after the user says they forked/cloned and are ready to contribute. Part of the open-source contribution flow with git-pr-creator and git-pr-cleanup.
---

# Git Upstream Sync

Configure the upstream remote and create a new branch from the latest upstream so you can contribute on a clean, up-to-date branch. Use this when you have already **forked** and **cloned your fork** and are ready to start making changes.

## When to Use

- User has forked a repo and cloned their fork; they want to add upstream and get a fresh branch.
- User says they want to "sync with upstream", "configure upstream", "branch from latest upstream", or "把本地分支更新到代码仓最新状态".
- User is preparing to contribute to an open-source project and needs the standard fork workflow (upstream + update local default to latest, then branch from it).

## Prerequisites

- Current directory is the repo root (or user has cloned their fork).
- User has already forked on GitHub and cloned **their fork** (e.g. `git clone https://github.com/yourname/repo.git`).

## Workflow

### Step 1: Ensure Upstream Remote Exists

Check if `upstream` is already configured:

```bash
git remote -v
```

If there is no `upstream` remote, add it. You need the **original (upstream) repo URL** — the repo the user forked from, not their fork.

- If the user provides the upstream URL (e.g. `https://github.com/owner/repo.git`), use it.
- If not, infer from `origin`: typically the fork is `yourname/repo` and upstream is `owner/repo`. You can try:
  - Ask the user: "What is the upstream repo URL (the original project you forked from)?"
  - Or derive from GitHub: fork's `parent` or `source` is upstream; if you have `gh` and the repo is on GitHub, you can run `gh repo view --json parent` and use `parent.cloneUrl` (or similar) for upstream.

Then:

```bash
git remote add upstream <upstream-repo-url>
```

Use HTTPS or SSH consistently with how `origin` is configured when possible.

### Step 2: Fetch Upstream

```bash
git fetch upstream
```

This updates remote-tracking branches for upstream only; it does not change your local branches yet.

### Step 3: Determine Default Branch

Many repos use `main`; some still use `master`. Detect from upstream:

```bash
git remote show upstream | grep "HEAD branch"
# or
git symbolic-ref refs/remotes/upstream/HEAD 2>/dev/null
```

If that fails, list upstream branches and assume `main` or `master`:

```bash
git branch -r | grep 'upstream/'
```

Use the branch name (e.g. `main` or `master`) as `DEFAULT_BRANCH` in the next steps.

### Step 4: Update Local Default Branch to Latest Upstream

若有未提交的修改，先 `git status` 检查；需要保留时可 `git stash`，再执行下面步骤，避免 checkout 时丢失或冲突。

**Always** bring your local default branch (main or master) in sync with upstream so both your repo and the new branch are at the repo's latest state:

```bash
git checkout main   # or master, use DEFAULT_BRANCH from Step 3
git merge upstream/main   # or upstream/master
```

If you prefer rebase: `git pull --rebase upstream main` (or master). Resolve any conflicts before continuing.

This step ensures "本地分支更新到代码仓的最新状态" — your local main/master matches the remote repo's latest.

### Step 5: Create New Branch from Updated Default

Create the contribution branch from the now-updated local default:

```bash
git checkout -b feature/your-feature
```

Use a short, descriptive branch name (e.g. `fix/123-login-error`); if the user has a name, use it. 若项目用 Issue 追踪，分支名建议带 Issue 号（如 `issue-123-xxx`），便于在 commit/PR 里用 `Closes #123` 关联。This branch is now at the same commit as upstream's latest.

### Step 6: Confirm and Report

Tell the user:

- Whether `upstream` was already present or was just added.
- The default branch used (`main` or `master`).
- The new branch name and that it is based on latest upstream.
- Remind them they can now make changes, commit, and push to **origin** (their fork); later they will open a PR from their fork to the upstream repo.

## Sync Information Output (Required)

**Always output sync-related information** so the user sees what happened. Both success and failure must produce clear output.

### Normal / Success

After each step, surface relevant output or a short summary to the user:

| Step | What to output |
|------|----------------|
| 1. Upstream remote | Result of `git remote -v` (or state "upstream already exists" / "added upstream <url>"). |
| 2. Fetch | Result of `git fetch upstream` (e.g. "Fetched …", or "Already up to date."). |
| 3. Default branch | Detected default branch (e.g. "Default branch: main"). |
| 4. Update local | Result of merge/rebase (e.g. "Already up to date." or "Updated main from upstream/main."). |
| 5. New branch | New branch name and that it is at latest upstream (e.g. "Created branch feature/xxx from main."). |
| 6. Report | Final summary: upstream status, branch used, new branch name, next steps. |

Do not run steps silently; show at least a one-line summary per step so the user has a clear sync log.

### Errors / Failures

When any command fails, **always output**:

1. **Exact error message** — the full stderr or command output (or a faithful summary if very long).
2. **Which step failed** — e.g. "Step 2: git fetch upstream failed."
3. **Likely cause** — e.g. "Network unreachable", "Permission denied", "Upstream URL invalid".
4. **What the user can do** — e.g. "Check network and run `git fetch upstream` again", or "Confirm upstream URL with `git remote -v`."

Common failure points and what to report:

- **No upstream URL** (Step 1): Output that upstream is missing; ask for the upstream repo URL or suggest `gh repo view --json parent`.
- **Fetch failed** (Step 2): Output the fetch error; suggest checking network, VPN, or `git remote -v` and credentials.
- **Merge/rebase conflict** (Step 4): Output the conflict message and list conflicted files; tell the user to resolve conflicts, then `git add` and `git commit` or `git rebase --continue`.
- **Branch create failed** (Step 5): Output the error (e.g. branch already exists); suggest another name or `git branch -d <name>` if replacing.

Never leave the user with no output after an error; always report the failure and next steps.

## Branch Naming

Suggest a short, descriptive name. If the contribution ties to an issue, include it (e.g. `fix/123-login-error` or `issue-123-add-export`). If the user already has a name, use it.

## Edge Cases

- **Upstream already added**: Skip adding; only fetch and proceed.
- **User is not on a fork**: If `origin` is the canonical repo (user has write access), they may not need upstream for contributing. Still offer to add upstream if they want to track the same repo under the name `upstream`.
- **Multiple remotes**: Only add `upstream` if it does not exist; do not overwrite.
- **Detached HEAD or wrong branch**: Before creating the new branch, ensure local default is updated (Step 4) and the new branch is created from it (Step 5).

## What This Skill Does Not Do

- Does not fork the repo (user does that on GitHub).
- Does not clone (user clones their fork).
- Does not make code changes or create commits; it only prepares the repo and branch.

## Integration with Other Skills

- After this, the user can edit code, then use **git-commit-message** for commits and **git-pr-creator** for PR title/description.
- For isolated work, they can use **using-git-worktrees** in the same repo; that skill creates a worktree and branch but does not configure upstream — use this skill first if they need upstream configured and a branch from latest upstream.

### 开源贡献完整流程（与其它 git skills 衔接）

完整流程表见 [references/open-source-workflow.md](../references/open-source-workflow.md)。本技能对应「开始贡献」阶段：配置 upstream、从最新上游拉分支。
