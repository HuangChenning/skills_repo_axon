---
name: git-pr-creator
description: 'Generate PR title and description by analyzing git commits and code changes. Reads differences between current branch and master/main, extracts commit messages, reviews modified files, and produces a structured PR description for user review. Does NOT automatically create the PR - returns content for manual review. Part of the open-source contribution flow with git-upstream-sync and git-pr-cleanup.'
---

# Git PR Creator

Analyze git commits and code changes to automatically generate PR title and description.

## What I Do

1. **Analyze commits** - Read all commits in current branch that differ from `master` or `main`
2. **Extract commit context** - Parse commit messages and identify scope of changes
3. **Review code changes** - Examine modified files to understand implementation details
4. **Generate PR content** - Create structured PR title and description
5. **Return for review** - Present the generated content to user for approval before creating PR

## When to Use Me

Triggers on requests like:
- "Generate a PR for my changes"
- "Create PR description from commits"
- "Summarize my branch as a PR"
- "Draft PR for current branch"
- "Generate PR title and description"

## 提 PR 前：先 Push 到 origin

本技能只生成 PR 标题和描述，**不执行**创建 PR。提 PR 前请先确保当前分支已推送到你的 fork：

```bash
# 查看当前分支名
git branch --show-current

# 推送到你的 fork
git push -u origin <当前分支名>
```

**建议**：Push 前在本地跑一遍测试（如 `npm test` / `pytest` / `cargo test`），通过后再 push，可减少 CI 失败和往返修改。

生成内容后，在 GitHub 上创建 PR：可用 `gh pr create --title "..." --body "..."`，或将生成的内容粘贴到网页「Create pull request」中。

## 在已有 PR 上继续修改（本项目通用流程）

当**已有现成 PR**、在作者审查意见基础上继续修改时，按以下顺序操作，适用于本项目后续所有 PR：

1. **在现有 PR 所在分支上**完成本次代码修改与验证。
2. **先 commit**：在本地执行 `git add` 与 `git commit`。commit message 可写为针对审查意见的修复，例如：`address review: centralize git version in gitutil, downgrade doctor git check to warning`。
3. **再 push**：将分支 push 到远程，即可更新该 PR，**无需新建 PR**。

## Workflow

### Step 1: Detect Current Branch and Target Branch

```bash
# Get current branch name
git rev-parse --abbrev-ref HEAD

# Identify default branch (master or main)
git symbolic-ref refs/remotes/origin/HEAD
```

若 `git log main..HEAD` 或 `git log master..HEAD` 为空，说明当前分支相对默认分支没有新提交，**暂无内容可提 PR**。应提示用户：「当前分支相对 main/master 无新提交，请先完成修改并 commit 后再生成 PR 描述。」

### Step 2: Get Commit Differences

```bash
# List all commits not in target branch
git log master..HEAD --oneline
# or
git log main..HEAD --oneline

# Get detailed commit info
git log master..HEAD --format="%H|%an|%ae|%ad|%s|%b"
```

### Step 3: Analyze Code Changes

```bash
# Get list of changed files
git diff master..HEAD --name-status

# Get diff stats
git diff master..HEAD --stat

# View specific file changes for context
git show <commit>:<file>
```

### Step 4: Generate PR Content

#### PR Title Generation Rules

1. **Type prefix** (optional): `[Feature]`, `[Fix]`, `[Refactor]`, `[Docs]`, `[Test]`
2. **Subject**: Clear, concise description of main change
3. **Length**: Keep under 72 characters
4. **Format**: `[Type] Short description` or just `Short description`

**Examples:**
- `[Feature] Add PostgreSQL 15 collector YAML support`
- `[Fix] Correct execution plan query for pg_stat_statements`
- `Refactor sampler initialization logic`

#### PR Description Structure

```markdown
## Description
[One-paragraph summary of changes and their purpose]

## Changes
- [Bullet point for each major change]
- [Group related changes together]

## Type of Change
- [ ] Bug fix (non-breaking fix)
- [ ] New feature (non-breaking addition)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## How to Test
[Optional: Steps to verify the changes work correctly]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated (if applicable)

## Related Issues
[使用关闭关键字引用 Issue，见下方说明]
Closes #123

## Commits
[List of commits included:]
- commit_hash: commit_message
```

### Step 5: Present for User Review

1. Display generated PR title
2. Display full PR description
3. Show list of commits included
4. Show summary of files changed
5. Ask user to review and approve
6. **Do NOT** automatically create the PR - wait for explicit user confirmation

## Example Workflow

**User**: "Generate a PR for my changes"

**Process**:
1. Check current branch (e.g., `feature/pg-collectors`)
2. Find commits since `main`:
   - `a1b2c3d: Add PostgreSQL 15 collector-top.yaml`
   - `d4e5f6g: Add PostgreSQL 15 swiss-15.yaml`
   - `h7i8j9k: Fix sqlplan query for PostgreSQL`
3. Analyze changed files:
   - `swissql-backend/jdbc_drivers/postgres/collector-15-top.yaml` (new)
   - `swissql-backend/jdbc_drivers/postgres/swiss-15.yaml` (new)
   - `swissql-backend/jdbc_drivers/postgres/collector-15.yaml` (modified)
4. Generate:
   ```
   PR Title: [Feature] Add PostgreSQL 15 TOP and Swiss collectors
   
   PR Description:
   ## Description
   Adds PostgreSQL 15 database collectors configuration following the 4-layer performance metrics model (Context, Resource, Wait, Load Attribution). Splits collector-15.yaml into two YAML files: collector-15-top.yaml for TOP metrics and swiss-15.yaml for Swiss sampler queries.
   
   ## Changes
   - Created collector-15-top.yaml with 6-layer TOP collector (context, cpu, sessions, waits, topSessions, io)
   - Created swiss-15.yaml with 13 Swiss sampler queries (sqltext, sqlplan, active_transactions, locks, etc.)
   - Added YAML schema completeness (order, render_hint fields)
   - Verified all SQL queries execute correctly on PostgreSQL 15
   
   ## Type of Change
   - [x] New feature (non-breaking addition)
   - [x] Documentation update
   
   Files changed (3):
   - swissql-backend/jdbc_drivers/postgres/collector-15-top.yaml (new)
   - swissql-backend/jdbc_drivers/postgres/swiss-15.yaml (new)
   - swissql-backend/jdbc_drivers/postgres/collector-15.yaml (modified)
   
   Commits included (3):
   - a1b2c3d Add PostgreSQL 15 collector-top.yaml
   - d4e5f6g Add PostgreSQL 15 swiss-15.yaml
   - h7i8j9k Fix sqlplan query for PostgreSQL
   ```

5. Return to user for review and approval

## Issue 关联

### 关闭 Issue 的关键字

在 PR 描述中使用特定关键字，合并后可自动关闭 Issue：

| 关键字 | 效果 | 示例 |
|:---|:---|:---|
| `Closes` | PR 合并后自动关闭 Issue | `Closes #123` |
| `Fixes` | 同上 | `Fixes #123` |
| `Resolves` | 同上 | `Resolves #123` |
| `Refs` | 仅引用，不关闭 Issue | `Refs #123` |
| `Related to` | 仅引用，不关闭 Issue | `Related to #123` |

**⚠️ 注意**：仅在 PR 描述中使用 `Issue #123` 或 `#123` 不会自动关闭 Issue！

### 从分支名解析 Issue

如果分支名包含 Issue 编号，自动提取并关联：

**常见分支命名格式：**
- `issue-123-fix-bug` → Issue #123
- `fix/123-login-error` → Issue #123
- `feat-456-add-export` → Issue #456

**检测命令：**
```bash
# 从分支名提取 Issue 编号
git branch --show-current | grep -oE '[0-9]+'
```

**工作流：**
1. 检测当前分支名
2. 如果包含 `issue-XXX` 或 `XXX` 数字格式，提取 Issue 编号
3. 在 PR 描述的 "Related Issues" 部分自动添加 `Closes #XXX`

### PR 描述中的 Issue 关联示例

```markdown
## Related Issues
Closes #123
```

或多个 Issue：

```markdown
## Related Issues
Closes #123
Closes #456
Refs #789
```

## Important Notes

- **Does NOT create PR automatically** - Only generates content
- **Updating an existing PR** - When addressing review feedback: complete changes on the PR branch → commit (e.g. `address review: ...`) → push to update that PR; do not open a new PR (see section above).
- **Respects user's review** - User must explicitly approve before any PR action
- **Handles multiple commits** - Aggregates messages from all commits in branch
- **Identifies default branch** - Automatically detects `master` or `main`
- **Shows commit context** - Displays commits included for transparency
- **Lists changed files** - Shows all modified/added/deleted files
- **Markdown formatted** - Returns properly formatted PR description ready for GitHub
- **Auto-detects Issue numbers** - Extracts Issue numbers from branch names when available

## Technical Details

### Git Commands Used

| Command | Purpose |
|---------|---------|
| `git rev-parse --abbrev-ref HEAD` | Get current branch name |
| `git symbolic-ref refs/remotes/origin/HEAD` | Detect default branch |
| `git log master..HEAD` | List commits in current branch |
| `git diff master..HEAD` | Get file changes |
| `git show <commit>:<file>` | View specific file content |

### Commit Message Parsing

- **First line**: Commit summary (becomes part of description)
- **Blank line**: Separator
- **Body**: Additional context (included if present)

### File Change Analysis

- **Added files** (`A`): New functionality
- **Modified files** (`M`): Changes to existing code
- **Deleted files** (`D`): Removed functionality
- **Renamed files** (`R`): Code reorganization

## Information Output (Required)

Always surface to the user:

- **Success path**: Current branch, target branch (main/master), list of commits included, list of files changed (name-status), generated PR title, and full PR description. Do not skip any of these.
- **Failure path**: Which step failed (e.g. "Step 2: no commits found"), the exact error or command output, and what the user should do (e.g. commit first, specify target branch, stash changes).

Never present only the PR body without branch/commits/files context, and never fail silently.

## Error Handling

- If no commits found: Inform user branch is even with target and output that clearly (no PR content to generate).
- If working directory dirty: Suggest stashing changes first; report uncommitted files.
- If default branch detection fails: Ask user to specify target branch; report the failure.
- If commit parsing fails: Show raw commit output for manual review.

## Test cases (eval prompts)

以下为 2～3 条可转为 evals 的测试场景说明，仅作文档；实际评测时可填入 `evals/evals.json` 并运行 skill-creator 流程。

| ID | Prompt（用户原话） | Expected output / 验收要点 |
|----|-------------------|----------------------------|
| 1 | "帮我生成当前分支的 PR 标题和描述"（当前分支相对 main 有 2～3 个 commit，有代码变更） | 输出包含：当前分支名、目标分支、commits 列表、文件变更列表、PR 标题、完整 PR 描述（含 Description / Changes / Type of Change 等）；且明确说明需用户自行执行 `gh pr create` 或网页创建。 |
| 2 | "给这个分支写个 PR description"（分支名含数字，如 `issue-42-fix-timeout`） | 生成的 PR 描述中 Related Issues 处应出现 `Closes #42`（或等价）；其余同 ID 1。 |
| 3 | "生成 PR 描述"（当前分支与 main 无差异，无新 commit） | **不**输出 PR 正文；明确提示「当前分支相对 main 无新提交」，并建议先 commit 后再生成。 |
