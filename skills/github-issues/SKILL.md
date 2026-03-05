---
name: github-issues
description: 'Create, update, and manage GitHub issues using MCP tools. Use this skill when users want to create bug reports, feature requests, or task issues, update existing issues, add labels/assignees/milestones, or manage issue workflows. Triggers on requests like "create an issue", "file a bug", "request a feature", "update issue X", or any GitHub issue management task.'
---

# GitHub Issues

Manage GitHub issues using the `github` MCP server.

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `mcp_issue_write` (create) | Create new issues |
| `mcp_issue_write` (update) | Update existing issues |
| `mcp_issue_read` | Fetch issue details |
| `mcp_search_issues` | Search issues |
| `mcp_add_issue_comment` | Add comments |
| `mcp_list_issues` | List repository issues |

## Workflow

1. **Determine action**: Create, update, or query?
2. **Gather context**: Get repo info, existing labels, milestones if needed
3. **Structure content**: Use appropriate template from [references/templates.md](references/templates.md)
4. **Execute**: Call the appropriate MCP tool
5. **Confirm**: Report the issue URL to user

## Creating Issues

### Required Parameters

```
owner: repository owner (org or user)
repo: repository name  
title: clear, actionable title
body: structured markdown content
```

### Optional Parameters

```
labels: ["bug", "enhancement", "documentation", ...]
assignees: ["username1", "username2"]
milestone: milestone number (integer)
```

### Title Guidelines

- Start with type prefix when useful: `[Bug]`, `[Feature]`, `[Docs]`
- Be specific and actionable
- Keep under 72 characters
- Examples:
  - `[Bug] Login fails with SSO enabled`
  - `[Feature] Add dark mode support`
  - `Add unit tests for auth module`

### Body Structure

Always use the templates in [references/templates.md](references/templates.md). Choose based on issue type:

| User Request | Template |
|--------------|----------|
| Bug, error, broken, not working | Bug Report |
| Feature, enhancement, add, new | Feature Request |
| Task, chore, refactor, update | Task |

## Updating Issues

Use `mcp_issue_write` (update) with:

```
owner, repo, issue_number (required)
title, body, state, labels, assignees, milestone (optional - only changed fields)
```

State values: `open`, `closed`

## Examples

### Example 1: Bug Report

**User**: "Create a bug issue - the login page crashes when using SSO"

**Action**: Call `mcp_issue_write` (create) with:
```json
{
  "owner": "github",
  "repo": "awesome-copilot",
  "title": "[Bug] Login page crashes when using SSO",
  "body": "## Description\nThe login page crashes when users attempt to authenticate using SSO.\n\n## Steps to Reproduce\n1. Navigate to login page\n2. Click 'Sign in with SSO'\n3. Page crashes\n\n## Expected Behavior\nSSO authentication should complete and redirect to dashboard.\n\n## Actual Behavior\nPage becomes unresponsive and displays error.\n\n## Environment\n- Browser: [To be filled]\n- OS: [To be filled]\n\n## Additional Context\nReported by user.",
  "labels": ["bug"]
}
```

### Example 2: Feature Request

**User**: "Create a feature request for dark mode with high priority"

**Action**: Call `mcp_issue_write` (create) with:
```json
{
  "owner": "github",
  "repo": "awesome-copilot",
  "title": "[Feature] Add dark mode support",
  "body": "## Summary\nAdd dark mode theme option for improved user experience and accessibility.\n\n## Motivation\n- Reduces eye strain in low-light environments\n- Increasingly expected by users\n- Improves accessibility\n\n## Proposed Solution\nImplement theme toggle with system preference detection.\n\n## Acceptance Criteria\n- [ ] Toggle switch in settings\n- [ ] Persists user preference\n- [ ] Respects system preference by default\n- [ ] All UI components support both themes\n\n## Alternatives Considered\nNone specified.\n\n## Additional Context\nHigh priority request.",
  "labels": ["enhancement", "high-priority"]
}
```

## Common Labels

Use these standard labels when applicable:

| Label | Use For |
|-------|---------|
| `bug` | Something isn't working |
| `enhancement` | New feature or improvement |
| `documentation` | Documentation updates |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `question` | Further information requested |
| `wontfix` | Will not be addressed |
| `duplicate` | Already exists |
| `high-priority` | Urgent issues |

## Tips

- Always confirm the repository context before creating issues
- Ask for missing critical information rather than guessing
- Link related issues when known: `Related to #123`
- For updates, fetch current issue first to preserve unchanged fields

## Issue 后续工作流

创建 Issue 后，建议遵循以下工作流以实现 Issue → Commit → PR 的自动关联：

### 1. 创建关联分支

**推荐分支命名格式：**

| 格式 | 示例 | 说明 |
|:---|:---|:---|
| `issue-<number>-<action>` | `issue-123-fix-login` | 清晰关联 Issue #123 |
| `fix/<number>-<description>` | `fix/123-timeout-error` | 类型前缀格式 |
| `feat/<number>-<feature>` | `feat/456-user-export` | 功能分支格式 |

**使用 GitHub CLI 自动创建分支：**

```bash
# 自动从 Issue 创建分支并 checkout
gh issue develop 123 --checkout

# 自动生成分支名: issue-123-fix-bug
# 自动添加到本地: git checkout -b issue-123-fix-bug
```

### 2. 开发并提交（使用关闭关键字）

在 Commit 消息中使用关闭关键字：

```bash
git commit -m "fix: resolve login timeout error

Closes #123"
```

**支持的关闭关键字：**
- `Closes #123` - 合并后自动关闭 Issue
- `Fixes #123` - 同上
- `Resolves #123` - 同上

**仅引用（不关闭）的关键字：**
- `Refs #123` - 仅引用，不关闭
- `Related to #123` - 仅引用，不关闭

### 3. 创建 PR（自动关联）

```bash
# 创建 PR，会自动关联 Issue（如果分支名包含 Issue 编号或 Commit 中有关闭关键字）
gh pr create --fill
```

### 完整工作流示例

```bash
# 1. 创建 Issue
gh issue create --title "Fix: Login timeout error" --body "..."
# 输出: Issue #123 created

# 2. 创建关联分支
git checkout -b issue-123-fix-timeout
# 或使用: gh issue develop 123 --checkout

# 3. 开发并提交
git add .
git commit -m "fix: resolve login timeout error

- Increase timeout to 30 seconds
- Add retry logic

Closes #123"

# 4. 推送并创建 PR
git push -u origin issue-123-fix-timeout
gh pr create --fill
```

**结果：** PR 合并后，Issue #123 会自动关闭！
