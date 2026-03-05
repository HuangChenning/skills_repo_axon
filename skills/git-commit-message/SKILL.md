---
name: git-commit-message
description: Intelligent git commit message workflow that analyzes staged changes and generates structured commit messages following conventional commit format. Use when user needs to create a git commit message, asks about commit message format, or wants to generate commit messages from staged changes.
---

# Git Commit Message

## Overview

Generate structured, conventional commit messages by analyzing staged changes. The workflow follows the pattern: `type(scope): subject` with optional body for complex changes.

## Commit Types

- `feat`: New features, new commands, new endpoints
- `fix`: Bug fixes, error handling improvements
- `refactor`: Code restructuring without functional changes
- `docs`: Documentation updates only
- `chore`: Build process, dependencies, configuration
- `perf`: Performance improvements
- `test`: Test additions or improvements

## Scopes

- `cli`: CLI-related changes
- `backend`: Backend API changes
- `repl`: REPL interface changes
- `driver`: Database driver changes
- `sampler`: Sampling system changes
- `config`: Configuration changes

## Workflow

### 1. Analyze staged changes

```bash
git status
git diff --cached --stat
git diff --cached --name-only
```

### 2. Analyze change types and scope

```bash
git diff --cached --name-only | head -20
git diff --cached | head -50
```

### 3. Generate structured commit message

**Format:**

```
type(scope): concise subject

Major changes:
- Change 1: Brief description
- Change 2: Brief description

Minor improvements:
- Improvement 1: Brief description
```

**Examples:**

```
feat(cli): add DBeaver project import command

Major changes:
- Add import-dbeaver-project command with conflict resolution
- Implement profile filtering and credential encryption

Minor improvements:
- Update README with import examples
- Add driver manifest validation
```

```
fix(repl): resolve connection error message inconsistency

Major changes:
- Fix misleading "Connected successfully!" message on failed connections
- Add proper error handling for empty session IDs
```

## Commit Message Guidelines

**Subject Line:**

- Use `type(scope): subject` format
- Keep under 50 characters
- Use present tense, imperative mood ("add" not "added")
- Capitalize first letter

**Body:**

- Separate subject from body with blank line
- Use bullet points for multiple changes
- Wrap lines at 72 characters
- Focus on what and why, not how
- Use present tense ("fix" not "fixed")

**Flexibility:**

- For simple changes, body is optional
- Single-line commits are fine for minor changes: `fix(ci): correct SQL syntax`
- Only use detailed body when multiple changes or complex modifications
- Avoid over-structuring simple changes

**Include:**
- Major functional changes
- New features or commands
- Breaking changes
- Performance improvements
- Important refactoring

**Exclude:**
- File URLs or paths
- Implementation details
- Minor wording edits
- Trivial formatting changes
- Auto-generated content

## Issue 关联

在 Commit 消息中包含 Issue 编号可实现 PR 合并后自动关闭 Issue。

### 关闭 Issue 的关键字

| 关键字 | 效果 | 示例 |
|:---|:---|:---|
| `Closes` | PR 合并后自动关闭 Issue | `Closes #123` |
| `Fixes` | 同上 | `Fixes #123` |
| `Resolves` | 同上 | `Resolves #123` |

### 仅引用（不关闭）的关键字

| 关键字 | 效果 | 示例 |
|:---|:---|:---|
| `Refs` | 仅引用，不关闭 Issue | `Refs #123` |
| `Related to` | 仅引用，不关闭 Issue | `Related to #123` |

### 包含 Issue 的 Commit 模板

**格式 1：简洁版**
```
type(scope): concise subject

Closes #123
```

**格式 2：详细版**
```
type(scope): concise subject

Major changes:
- Change 1: Brief description
- Change 2: Brief description

Closes #123
```

**示例：**

```
feat(auth): add JWT token support

- Implement JWT generation and validation
- Add token refresh mechanism

Closes #123
```

```
fix(repl): resolve connection error message inconsistency

- Fix misleading "Connected successfully!" message on failed connections
- Add proper error handling for empty session IDs

Fixes #456
```

```
refactor(db): optimize query performance

- Add indexing to frequently queried columns
- Rewrite N+1 query patterns

Resolves #789
```

### ⚠️ 常见错误

| 错误写法 | 问题 | 正确写法 |
|:---|:---|:---|
| `Issue #123` | 不会自动关闭 Issue | `Closes #123` |
| `#123` | 不会自动关闭 Issue | `Fixes #123` |
| `for issue #123` | 不会自动关闭 Issue | `Resolves #123` |

## Output Format

Output ONLY the complete commit message without any additional text, explanations, or metadata.

**Correct:**
```
feat(cli): add profile filtering and sorting

Major changes:
- Add db_type and name filtering to list profiles
- Implement alphabetical sorting by db_type then name

Closes #123
```

**Incorrect:**
```
Here is the commit message:
feat(cli): add profile filtering and sorting
...
```
