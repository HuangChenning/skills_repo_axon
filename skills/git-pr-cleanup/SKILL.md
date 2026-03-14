---
name: git-pr-cleanup
description: After your PR is merged upstream, sync your local repo and fork and remove the merged branch. Use when the user says their PR was merged, they want to "clean up after merge", "sync fork with upstream", "删除已合并的分支", or "合并后收尾". Triggers on requests like "my PR was merged what do I do next", "update my fork after merge", or "clean up merged branch". Part of the open-source contribution flow with git-upstream-sync and git-pr-creator.
---

# Git PR Cleanup

After the **upstream maintainer** has merged your PR, you (as contributor) clean up on **your own** local repo and **your own** fork. You have full permission on your fork; no upstream write access is needed.

## When to Use

- User says their pull request was just merged upstream.
- User wants to "clean up after merge", "sync fork with upstream", "删除已合并的分支", or "合并后收尾".
- User asks what to do after their PR is merged.

## Prerequisites

- The user's PR has been merged into the upstream default branch (main or master).
- Current directory is the repo root (their clone of their fork).
- Remote `upstream` is configured (same as in **git-upstream-sync**).
- User knows the **feature branch name** that was merged (e.g. `feature/xxx` or `issue-123-fix`). If not, detect from `git branch` or ask.

## Workflow

### Step 1: Confirm Context

**请确认**：PR 已在上游仓库合并后再执行本流程；否则 `git pull upstream` 不会包含你的提交，后续删分支可能误删未合并工作。

- Confirm the merged branch name (e.g. from user or from `git branch --show-current` if they are still on it). 若用户已切到其他分支，可用 `git branch` 列出本地分支，让用户指出刚合并的分支名。
- Detect default branch: `git symbolic-ref refs/remotes/upstream/HEAD` or `git remote show upstream | grep "HEAD branch"`, fallback to `main` or `master`.

Output to user: which branch was merged and which default branch will be updated.

### Step 2: Switch to Default and Pull from Upstream

```bash
git checkout main   # or master
git pull upstream main   # or master
```

This brings your local default branch to the same state as upstream (including the merged PR).

**Output**: Show the result of `git pull` (e.g. "Already up to date." or "Updated … from upstream/main.").

### Step 3: Optional — Push Your Fork’s Default Branch

Pushing updates your fork’s main/master on GitHub so it matches upstream. This is **optional**.

**Do not run this automatically.** Ask the user:

- "是否将本地 main 推送到你的 fork（origin），使 fork 与上游一致？(y/n)"
- Or in English: "Push local main to your fork (origin) so your fork matches upstream? (y/n)"

If the user says yes: run `git push origin main` (or master) and output the push result.  
If no or skip: say "已跳过。你的 fork 上的 main 未更新。" and continue.

### Step 4: Delete Local Merged Branch

```bash
git branch -d feature/xxx   # use the actual merged branch name
```

If Git reports that the branch is not fully merged, do **not** force-delete without asking. Tell the user and ask: "Branch may not be fully merged. Force delete with `git branch -D feature/xxx`? (y/n)".

**Output**: Show the command result (e.g. "Deleted branch feature/xxx.").

### Step 5: Optional — Delete Remote Branch on Your Fork

Deleting the branch on `origin` (your fork) keeps the fork tidy. This is **optional**.

**Do not run this automatically.** Ask the user:

- "是否删除你 fork 上已合并的远程分支 origin/feature/xxx？(y/n)"
- Or in English: "Delete the merged branch on your fork (origin/feature/xxx)? (y/n)"

If the user says yes: run `git push origin --delete feature/xxx` and output the result.  
If no or skip: say "已跳过。远程分支 origin/feature/xxx 保留。" and continue.

### Step 6: Final Summary

Tell the user what was done:

- Local default branch updated from upstream (and optionally pushed to fork).
- Local branch feature/xxx deleted (and optionally remote branch on fork deleted).
- Remind: next time they contribute, they can use **git-upstream-sync** to get a new branch from latest upstream.
- 平时也可偶尔只执行本流程的 **Step 2 + Step 3**（`git pull upstream main`、可选 `git push origin main`），不删分支，让 fork 与上游保持同步。

## Process Output (Required)

**Always output cleanup-related information.** Both success and failure must produce clear output.

### Normal / Success

After each step, show relevant output or a one-line summary:

| Step | What to output |
|------|----------------|
| 1. Context | Merged branch name, default branch (main/master). |
| 2. Pull upstream | Result of `git pull upstream main` (or master). |
| 3. Push origin (optional) | User choice; if yes, result of `git push origin main`. If no, "已跳过". |
| 4. Delete local branch | Result of `git branch -d` (e.g. "Deleted branch feature/xxx."). |
| 5. Delete remote branch (optional) | User choice; if yes, result of `git push origin --delete`. If no, "已跳过". |
| 6. Summary | What was done and optional steps skipped. |

Do not run steps silently; at least one-line summary per step.

### Errors / Failures

When any command fails, **always output**:

1. **Exact error message** — full stderr or command output (or faithful summary if very long).
2. **Which step failed** — e.g. "Step 2: git pull upstream main failed."
3. **Likely cause** — e.g. "No upstream remote", "Branch not merged", "Network error".
4. **What the user can do** — concrete next step or command.

Common cases:

- **No upstream remote**: Output "upstream not configured"; suggest adding it (see **git-upstream-sync**) or `git remote -v`.
- **Pull failed** (e.g. network): Output the error; suggest retry or check VPN/credentials.
- **Branch not fully merged** (`branch -d` refuses): Output the message; ask user whether to force-delete with `-D` or leave the branch.
- **Push failed** (Step 3 or 5): Output the error; suggest checking `origin` URL and permissions.

Never leave the user with no output after an error; always report failure and next steps.

## Optional Steps — Always Ask

For **Step 3** (push origin main) and **Step 5** (delete remote branch on fork):

- **Do not** assume yes or no.
- **Before** running the command, ask the user in clear language (e.g. 是否… / Do you want to…).
- Proceed only after the user confirms; if they skip, say "已跳过" and continue to the next step.

## What This Skill Does Not Do

- Does not merge the PR (the upstream maintainer does that on GitHub).
- Does not touch the upstream repo; all operations are on the user’s local clone and their fork (origin).

## Integration with Other Skills

- **git-upstream-sync**: Use when starting a new contribution (configure upstream, update local default, create new branch).
- **git-pr-cleanup**: Use after a PR is merged to sync and remove the merged branch (this skill).

### 开源贡献完整流程（与其它 git skills 衔接）

完整流程表见 [references/open-source-workflow.md](../references/open-source-workflow.md)。本技能对应「收尾」阶段：同步 fork、删已合并分支。
