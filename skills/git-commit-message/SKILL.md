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

## Output Format

Output ONLY the complete commit message without any additional text, explanations, or metadata.

**Correct:**
```
feat(cli): add profile filtering and sorting

Major changes:
- Add db_type and name filtering to list profiles
- Implement alphabetical sorting by db_type then name
```

**Incorrect:**
```
Here is the commit message:
feat(cli): add profile filtering and sorting
...
```
