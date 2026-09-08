---
name: using-codegraph
description: Code intelligence and AST knowledge graph CLI & MCP tools for exploring architecture, call graphs, symbol implementations, and blast radius. Use BEFORE grep/read_file when investigating code, understanding flows, or before refactoring.
---

# CodeGraph Skill

Use `codegraph` CLI or CodeGraph MCP tools to query the codebase's AST and dependency knowledge graph instead of running multi-turn grep/file-read loops.

## Execution Prerequisite (Working Directory & Repo Path)

**CRITICAL**: `codegraph` operates on `.codegraph/` SQLite index generated inside each Git repository worktree. It must be executed **against the checked-out repository directory (worktree)**, NOT in the task's root workdir parent directory.

1. **Check out repository** (if not yet checked out):
   ```bash
   mopheus repo checkout <url> --output json
   ```
2. **Tool Selection (CLI vs MCP)**:
   - **CLI Mode (Preferred)**: Change into the checked-out repository path (`cd <repo_name>`, e.g. `cd mopheus`) and run `codegraph` commands directly.
   - **MCP Tool Mode**: If `codegraph` CLI is not available in PATH, check if CodeGraph MCP server tools (`codegraph_explore`, `codegraph_callers`, etc.) are provided in your available tools. When calling MCP tools, always specify `projectPath: "./<repo_name>"` (or the absolute repository worktree path).

---

## Core Capabilities & Commands

### 1. Explore Flow & Implementation (Primary Action)
Get verbatim source code, call paths, and blast radius in one shot with natural language or key symbol/file names:
- **CLI**:
  ```bash
  codegraph explore "<symbol names, flow or question>"
  # Examples:
  # codegraph explore "TicketCommentService CreateComment"
  # codegraph explore "how does agent task get dispatched to daemon runtime"
  ```
- **MCP Tool**: Call `codegraph_explore` (or `explore`) with `{"query": "...", "projectPath": "./<repo_name>"}`.

### 2. Check Callers & Callees
Find upstream callers or downstream dependencies of a specific function or method:
- **CLI**:
  ```bash
  codegraph callers <symbol_name>
  codegraph callees <symbol_name>
  ```
- **MCP Tool**: Call `codegraph_callers` / `codegraph_callees` with `{"symbol": "<symbol_name>", "projectPath": "./<repo_name>"}`.

### 3. Impact Analysis & Blast Radius (Before Modifying Code)
Evaluate what code is affected before changing a function, struct, or interface:
- **CLI**:
  ```bash
  codegraph impact <symbol_name>
  ```
- **MCP Tool**: Call `codegraph_impact` with `{"symbol": "<symbol_name>", "projectPath": "./<repo_name>"}`.

### 4. Locate Affected Tests
Find which test files are affected by modified source files:
- **CLI**:
  ```bash
  codegraph affected [file_paths...]
  ```
- **MCP Tool**: Call `codegraph_affected` with `{"files": ["..."], "projectPath": "./<repo_name>"}`.

### 5. Incremental Sync
Sync changes after editing code:
- **CLI**:
  ```bash
  codegraph sync
  ```
- **MCP Tool**: Call `codegraph_sync` with `{"projectPath": "./<repo_name>"}`.

---

## Agent Usage Rules & Best Practices

1. **Reach for CodeGraph FIRST**: Do NOT start with `grep` or reading full files when investigating how a feature works or locating symbols. CodeGraph returns the exact line-numbered source across multiple files in a single execution.
2. **Treat Output as Read**: Code shown in CodeGraph exploration is current and byte-for-byte identical to the files on disk. Do NOT re-read those files.
3. **Trace Complex Flows**: Name the two endpoints of a flow (e.g., `codegraph explore "mutateElement renderScene"`) to reveal dynamic dispatch and intermediate hops.
4. **Fallback & Tool Priority**:
   - **Step 1**: Check if `codegraph` CLI is available in PATH. If available, `cd <repo_name>` and use CLI commands.
   - **Step 2**: If CLI is not available, check for CodeGraph MCP tools and invoke with `projectPath`.
   - **Step 3**: If neither is available or index fails after verifying the directory, fall back to standard text search tools (`grep` / `read_file`).
   - **NEVER** run `codegraph init` in the task root parent directory. Only run `codegraph init` inside the repository directory (`<repo_name>`) if `.codegraph/` is genuinely missing.
