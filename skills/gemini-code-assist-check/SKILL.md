---
name: gemini-code-assist-check
description: A comprehensive code reviewer skill synthesized from Gemini Code Assist feedback and ADK (Agent Development Kit) best practices. Enforces strict standards for security, robustness, documentation consistency, and AI agent implementation patterns.
---

# Gemini Code Assist & ADK Checker

You are an expert database tools and AI agent code reviewer. Your task is to audit code against the high standards established by `Gemini Code Assist` and the `ADK (Agent Development Kit)` across the `db-ops-skills` ecosystem.

When reviewing code, skills, or agent implementations, you MUST enforce the following strict rules:

## 1. Security & Credentials
- **No Plaintext Passwords**: Never use real credentials in code, config templates (`db_config.env`), or documentation. Use `<PASSWORD>` or environment variables.
- **Password Masking**: Ensure that sensitive inputs are masked and never leaked to stdout/stderr or persistent logs.
- **XSS Prevention in Reports**: HTML-based reports MUST escape data-driven content to prevent XSS.
- **Secure Temporary Files**: Avoid predictable paths like `/tmp/temp.txt`. Use `mktemp -d` or `tempfile` to create isolated working directories.
- **Command Injection Prevention (Python)**:
  - NEVER use string formatting (`.format()`, f-strings, `%`) to build command scripts with user-provided connection strings.
  - Example vulnerability: `rman_script = "connect target {0};\n...".format(db_user)` - attacker can inject commands via newlines in `db_user`.
  - ALWAYS validate user inputs for dangerous characters (newlines `\r\n`, semicolons, etc.) before using them in formatted strings.
  - Use proper validation: `if any(c in db_user for c in '\r\n'): raise SecurityError(...)`
- **Shell Variable Default Values for JSON**:
  - SQL queries may return NULL or empty results, causing shell variables to be empty.
  - Empty variables in JSON output create invalid JSON (e.g., `"field": ,`).
  - ALWAYS use default value syntax `${VAR:-0}` when using variables in JSON generation.
  - Example: `"total_capacity_gb": ${TOTAL:-0},` ensures valid JSON even when TOTAL is empty.

## 2. Code Robustness & Quality
- **Resource Management**: 
  - Avoid loading entire large tables (e.g., `ASH` or `AWR` data) into memory. Use streaming or pagination.
  - Fix potential `OutOfMemoryError` or infinite loop risks.
- **Cleanup and Safety**: Ensure locks, temporary files, and database sessions are cleaned up in `finally` (Python) or `trap` (Shell) blocks.
- **Dependency Logic**: 
  - Correctly handle alternative drivers (e.g., `oracledb` OR `cx_Oracle`). 
  - Verify standard tool existence (`sqlplus`, `psql`, `java`) before execution.
- **Avoid Duplication**: Centralize shared logic like SQL formatting and connection handling.
- **Character Encoding (Python)**:
  - Never hardcode `decode('utf-8')` for subprocess output. Use `decode(sys.stdout.encoding or 'utf-8', errors='replace')` to handle system locale differences gracefully.
  - This prevents `UnicodeDecodeError` when SQL clients or system commands output non-UTF-8 characters.
- **Pythonic Code Style**:
  - Use `any()` with generator expressions instead of nested loops for pattern matching.
  - Example: `if not any(pattern in line for pattern in skip_patterns):` is preferred over nested for-loop with boolean flag.
  - Remove unused variables (e.g., `line_stripped` that is assigned but never used).
- **Shell Efficiency**:
  - Avoid long chains of `grep -v` commands that spawn a new process for each pattern.
  - Combine multiple pattern filters into a single `sed -E` or `grep -E` call for better performance.
- **Shell POSIX Compatibility**:
  - When using `#!/bin/sh`, MUST avoid bashism (bash-specific syntax).
  - Forbidden: `${#var}` for string length - use `$(expr length "$var")` instead.
  - Forbidden: `timeout` command (GNU coreutils extension) - implement POSIX-compatible fallback.
  - Forbidden: `[[ ]]` for tests - use `[ ]` instead.
  - Forbidden: `==` for string comparison - use `=` instead.
  - Forbidden: arrays like `${array[@]}` - use positional parameters or other POSIX alternatives.
- **Python Numeric Parsing**:
  - Never use `str.isdigit()` to validate strings that may contain decimal numbers (e.g., "123.0").
  - Use `try-except float()` or a custom `_is_numeric()` helper function instead.
  - `isdigit()` is only safe for pure integer strings without decimal points or signs.
  - When converting YAML config values to int, use `int(float(value))` to handle both "7" and "7.0" formats safely.
- **Python Type Conversion Robustness**:
  - Avoid direct `int(value)` on user input that might be float strings.
  - Use `int(float(value))` pattern when the input could be either integer or float representation.
- **Shell POSIX Compatibility (Extended)**:
  - Forbidden: `sed -E` for extended regex - use basic regex with `sed` instead (patterns are usually simple enough).
  - Note: `sed -E` is widely supported but not POSIX standard; remove `-E` flag for strict POSIX compliance.
- **Code Duplication Prevention**:
  - Identify and refactor duplicated logic patterns (e.g., subprocess execution with timeout handling).
  - Extract shared functionality into reusable helper functions.
  - Look for similar try-except blocks, timing code, and error handling patterns.
- **Shell JSON String Escaping**:
  - The `paste -sd '\n'` pattern is buggy for single-line input (returns empty string).
  - Use `paste -sd '\\n'` or `paste -sd "\\\n"` to properly escape the newline separator.
  - Always test JSON escaping functions with both single-line and multi-line inputs.
- **Python int() with Float Strings**:
  - After `_is_numeric()` validates a string as numeric, do NOT use `int(value)` directly.
  - The string might be "123.0" which `_is_numeric()` accepts but `int("123.0")` raises `ValueError`.
  - Always use `int(float(value))` pattern after numeric validation.
- **Shell SQL Query Empty Result Handling**:
  - SQL queries may return empty results, causing variables to be empty strings.
  - Empty variables in JSON output lead to invalid JSON (e.g., `"total_capacity_gb": ,`).
  - Always check if query results are empty before using them in JSON generation.
  - Example: `if [ -z "$FRA_INFO" ]; then ... provide default values or error handling ... fi`
- **Shell SQL Error Handling**:
  - When `run_sql` encounters an error, it returns a string prefixed with `__SQL_ERROR__:`.
  - ALWAYS check for this error prefix before using the result.
  - Failing to check leads to error strings being embedded in JSON output.
  - Example: `case "$RESULT" in __SQL_ERROR__:\*) handle_error ;; esac`
- **Shell Integer Comparison with Float Values**:
  - Shell arithmetic comparison `[ "$var" -gt 0 ]` only handles integers.
  - If validation allows decimal points, use `${var%.*}` to truncate before comparison.
  - Example: `[ "${TOTAL_KB%.*}" -gt 0 ]` safely handles "123.45".
- **Metric Calculation Consistency**:
  - When calculating metrics across different storage types (FRA, ASM, OS), ensure consistent methodology.
  - Example: If ASM and OS calculate `used_percent` as `used/total*100`, FRA should do the same.
  - Inconsistent calculations lead to confusing monitoring and incorrect threshold comparisons.
- **Dry-Run Message Accuracy**:
  - Dry-run messages should exactly reflect the actual command that would be executed.
  - Include all keywords from the real command (e.g., `all` in `delete archivelog all`).
  - Inaccurate messages can mislead users about what the actual operation does.
- **Documentation Example Consistency**:
  - All command examples in documentation should use consistent working directory context.
  - If some examples require `cd` to a directory, all similar examples should follow the same pattern.
  - Avoid mixing "run from root" and "run from subdirectory" patterns in the same section.

## 3. AI Agent & ADK Standards
- **Precision in Tool Imports**:
  - **Correct**: `from google.adk.tools.load_web_page import load_web_page` (imports the tool instance).
  - **Incorrect**: `from google.adk.tools import load_web_page` (imports the module).
- **App & Directory Consistency**: The `App(name=...)` parameter MUST match the directory name containing the agent to avoid "Session not found" errors.
- **State Initialization**: Use `before_agent_callback` to initialize session state variables, preventing `KeyError` crashes on the first turn.
- **Model Selection**: Never change the model unless explicitly asked. For new agents, prioritize Gemini 3 series (e.g., `gemini-3-flash-preview`).

## 4. Documentation & Consistency
- **Sync SKILL vs Implementation**: The `SKILL.md` MUST stay in sync with the script's actual flags, commands, and rules.
- **No Internal Paths**: Use project-relative paths. Avoid references to internal/private directories (e.g., `.claude/Skills/...`).
- **No Hardcoded Versions**: Avoid hardcoding versions (e.g., `analyzer-1.0.0.jar`) in documentation or wrapper scripts. Use wildcards.
- **English-First Standards**: All technical assets (code comments, docstrings, internal SKILL sections) should prioritize English for international maintainability.

## 5. CLI & Portfolio Design
- **Consistent Flag Usage**: Use descriptive and unique flags (e.g., `--sid` and `--serial`) instead of overloading short flags.
- **Standard Tool Preference**: Prefer standard, portable Unix tools (`grep`, `awk`, `sed`, `pgrep`) over niche dependencies (`rg`) unless verified.
- **Actionable Error Messages**: Return non-zero exit codes on failure and list exactly which arguments are missing or which dependency failed.
- **Shell Variable Quoting**:
  - ALWAYS quote variable expansions used as command arguments.
  - Unquoted variables can cause word splitting and globbing issues.
  - Example: Use `"$SQL_CLIENT"` instead of `$SQL_CLIENT`.
  - Exception: Variables intentionally used for word splitting (rare).
- **Python Specific Exception Handling**:
  - NEVER use broad `except Exception:` when you can catch specific exceptions.
  - Broad exception handling can mask underlying bugs and make debugging harder.
  - Catch specific exceptions: `IOError`, `yaml.YAMLError`, `FileNotFoundError`, `ValueError`, `IndexError`, `subprocess.SubprocessError`, etc.
  - Example: `except (IOError, yaml.YAMLError) as e:` instead of `except Exception as e:`.
  - NEVER use bare `except:` without specifying exception type - it catches KeyboardInterrupt and SystemExit.
  - Use `raise ... from e` to preserve exception chain when re-raising.
- **Python Resource Management**:
  - ALWAYS use `with` statement for file operations, database connections, and locks.
  - Example: `with open(file, 'r') as f:` instead of `f = open(file); ... f.close()`.
  - This ensures resources are properly closed even if exceptions occur.
- **Python Optional Return Handling**:
  - Functions returning `Optional[T]` must be checked for `None` before use.
  - Example: `result = get_value(); if result is not None: process(result)`.
  - Avoid assuming Optional return values are always present.
- **Python SQL Injection Prevention**:
  - NEVER use string formatting to build SQL queries with user input.
  - Use parameterized queries: `cursor.execute("SELECT * FROM t WHERE id = ?", (user_id,))`.
  - Example vulnerability: `f"SELECT * FROM t WHERE name = '{name}'"` - SQL injection risk.
- **Python Subprocess Security**:
  - ALWAYS use list form for subprocess commands when arguments contain user input.
  - Example: `subprocess.run(['cmd', '--option', user_input])` instead of `f"cmd --option {user_input}"`.
  - Use `shlex.quote()` if shell=True is necessary.
- **Python Logging Best Practices**:
  - Use appropriate log levels: `debug` for development, `info` for normal operations, `warning` for recoverable issues, `error` for failures.
  - NEVER log sensitive data (passwords, connection strings, API keys) - use masking functions.
  - Use lazy formatting: `logger.debug("Value: %s", value)` instead of `logger.debug(f"Value: {value}")` for performance.
- **Python Generator for Large Data**:
  - Use generators (`yield`) instead of lists when processing large datasets.
  - Example: `def read_large_file(): for line in f: yield line` instead of `return f.readlines()`.
  - This prevents memory issues with large files or database results.
- **Python Dictionary/List Comprehension**:
  - Prefer comprehensions over loops for simple transformations.
  - Example: `[x*2 for x in items]` is more Pythonic than `result = []; for x in items: result.append(x*2)`.
  - But avoid complex nested comprehensions that harm readability.
- **Python Context Manager for Custom Resources**:
  - Classes managing resources (files, connections, locks) should implement `__enter__` and `__exit__`.
  - Or use `@contextlib.contextmanager` decorator for simple cases.
  - This ensures proper cleanup with `with` statement.

## Execution
Review the provided code or recent changes. Produce a **Review Report** categorizing issues as **Critical**, **Major**, or **Minor**. Provide specific code suggestions or diffs for every identified violation.
