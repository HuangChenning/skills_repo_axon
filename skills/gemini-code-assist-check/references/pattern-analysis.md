# Gemini Code Assist Pattern Analysis

> Generated from analysis of 762 comments across 33 PRs in enmotech/db-ops-skills

## Overview Statistics

| Metric | Count |
|--------|-------|
| Total PRs Analyzed | 33 |
| Total Comments | 762 |
| Critical | 79 (10%) |
| High | 191 (25%) |
| Medium | 492 (65%) |

---

## Problem Category Distribution

Based on keyword analysis of all 762 comments:

| Category | Count | Percentage | Priority |
|----------|-------|------------|----------|
| Consistency Issues | 128 | 17% | HIGH |
| Hardcoded Values | 103 | 14% | HIGH |
| Configuration Issues | 55 | 7% | HIGH |
| Documentation-Implementation Mismatch | 39 | 5% | MEDIUM |
| Password/Credential Security | 31 | 4% | CRITICAL |
| Threshold/Constant Issues | 29 | 4% | MEDIUM |
| Error Handling | 26 | 3% | HIGH |
| Command Injection Risk | 20 | 3% | CRITICAL |
| JSON Generation Issues | 14 | 2% | CRITICAL |
| Exception Handling | 12 | 2% | HIGH |
| Shell Compatibility | 8 | 1% | MEDIUM |
| Resource Management | 7 | 1% | MEDIUM |

---

## Detailed Pattern Analysis

### 1. Consistency Issues (128 occurrences)

**Top patterns:**

| Pattern | Example |
|---------|---------|
| Config key mismatch | YAML uses `archive_dest`, Python reads `archive_status` |
| Command format inconsistency | SSH mode uses `df -Ph`, offline uses `df -P` |
| Documentation-code mismatch | Docs say `env_checker.sh`, actual script is `main.sh` |
| Default value mismatch | SKILL.md says port 5432, code defaults to 1521 |

**Detection patterns:**
```bash
# Check config key consistency
grep -r "key:" config.yaml | awk '{print $3}' | tr -d '"' > /tmp/config_keys.txt
grep -r "get('" scripts/*.py | grep -oP "get\('\K[^']+" > /tmp/code_keys.txt
diff /tmp/config_keys.txt /tmp/code_keys.txt
```

---

### 2. Hardcoded Values (103 occurrences)

**Top patterns:**

| Pattern | Severity | Example |
|---------|----------|---------|
| Hardcoded paths | HIGH | `/u01/app/oracle` |
| Hardcoded thresholds | MEDIUM | `if pct > 85:` |
| Hardcoded passwords | CRITICAL | `password = "oracle123"` |
| Hardcoded ports | LOW | `port = 1521` |

**Detection patterns:**
```bash
# Find hardcoded paths
grep -rn "/u0[0-9]/\|/opt/\|/home/oracle" --include="*.py" --include="*.sh"

# Find hardcoded thresholds
grep -rn "> [0-9][0-9]\|< [0-9][0-9]" --include="*.py" | grep -v "config\|threshold"
```

---

### 3. Configuration Issues (55 occurrences)

**Top patterns:**

| Pattern | Description |
|---------|-------------|
| Missing config file | Script references config that doesn't exist |
| Config schema mismatch | YAML structure changed but code not updated |
| Missing requirements.txt | Python imports external packages but no requirements.txt |
| Config not validated | No validation for required config fields |

---

### 4. Documentation-Implementation Mismatch (39 occurrences)

**Top patterns:**

| Pattern | Example |
|---------|---------|
| Script name mismatch | Docs say `env_checker.sh`, actual is `main.sh` |
| Feature mismatch | Docs mention PowerShell but only Bash exists |
| Missing env variables | SKILL.md doesn't list all required env vars |
| Output format mismatch | Docs say HTML+MD, actual only MD |

---

### 5. Password/Credential Security (31 occurrences)

**Top patterns:**

| Pattern | Severity | Description |
|---------|----------|-------------|
| Plaintext password in code | CRITICAL | `password = "sys123"` |
| Password in command line | HIGH | `sqlplus user/password@host` visible in `ps` |
| Password in examples | MEDIUM | Connection string examples with real-looking passwords |
| Credential files tracked | HIGH | `.env` or credential files not in `.gitignore` |

---

### 6. Threshold/Constant Issues (29 occurrences)

**Top patterns:**

| Pattern | Description |
|---------|-------------|
| Threshold in code, not config | `if usage > 85` instead of `config.threshold` |
| Duplicate thresholds | Same 85% in config.yaml, parser.py, SKILL.md |
| Magic numbers | Unexplained constants like `32` for GB limit |
| Inconsistent defaults | Different defaults in different files |

---

### 7. Error Handling Issues (26 occurrences)

**Top patterns:**

| Pattern | Description |
|---------|-------------|
| Silent error handling | `except Exception: pass` |
| No error message | Failure returns empty, caller doesn't know why |
| Generic error messages | "Error occurred" without specifics |
| No validation feedback | Invalid input silently ignored |

---

### 8. Command Injection Risk (20 occurrences)

**Top patterns:**

| Pattern | Severity | Example |
|---------|----------|---------|
| String formatting in commands | CRITICAL | `cmd = f"ls {user_input}"` |
| Shell=True with user input | HIGH | `subprocess.run(cmd, shell=True)` |
| SQL string concatenation | CRITICAL | `f"SELECT * FROM {table}"` |
| Eval with user input | CRITICAL | `eval(user_provided_code)` |

---

### 9. JSON Generation Issues (14 occurrences)

**Top patterns:**

| Pattern | Severity | Description |
|---------|----------|-------------|
| Trailing comma | CRITICAL | Last array element has comma |
| Empty value | CRITICAL | `"key": ,` when variable is empty |
| Missing escape | HIGH | Newlines/quotes not escaped |
| Invalid structure | CRITICAL | Unclosed brackets or wrong nesting |

---

### 10. Exception Handling (12 occurrences)

**Top patterns:**

| Pattern | Severity | Description |
|---------|----------|-------------|
| Bare `except:` | CRITICAL | Catches KeyboardInterrupt |
| `except Exception: pass` | HIGH | Silent failure, hard to debug |
| Wrong exception type | MEDIUM | Catching `Exception` when `ValueError` expected |
| No re-raise | MEDIUM | Catching and not re-raising loses stack trace |

---

### 11. Shell Compatibility (8 occurrences)

**Top patterns:**

| Pattern | Description |
|---------|-------------|
| Bashism in POSIX shell | Using `[[` in `#!/bin/sh` script |
| GNU-specific options | `timeout` not available on all Unix |
| Process substitution | `<(...)` not POSIX compatible |
| Non-portable commands | `rg` instead of `grep` |

---

### 12. Resource Management (7 occurrences)

**Top patterns:**

| Pattern | Description |
|---------|-------------|
| No `finally` block | Resources not cleaned on exception |
| Missing context manager | `open()` without `with` |
| SSH connection leak | Connection opened but never closed |
| Temp file leak | `mktemp` created but not cleaned |

---

## Quick Reference: Most Common Gemini Code Assist Comments

### Critical Level

```
"Hardcoded password in plain text"
"Command injection vulnerability"
"Invalid JSON - trailing comma"
"SSH host key verification disabled"
```

### High Level

```
"except Exception: pass silently swallows errors"
"Configuration key mismatch between YAML and Python"
"Hardcoded threshold should be in config"
"Password exposed in command line arguments"
```

### Medium Level

```
"Documentation inconsistent with implementation"
"Duplicate entry in .gitignore"
"Magic number should be extracted to constant"
"Consider using more specific exception type"
```

---

## Audit Checklist

Based on Gemini Code Assist patterns, check for:

### Critical (Must Fix)
- [ ] No hardcoded passwords anywhere
- [ ] No command injection vulnerabilities
- [ ] JSON generation produces valid output
- [ ] SSH host key verification enabled by default

### High (Should Fix)
- [ ] No `except Exception: pass` patterns
- [ ] Config keys match between YAML and Python
- [ ] Thresholds in config, not hardcoded
- [ ] Passwords not in command line arguments

### Medium (Consider Fix)
- [ ] Documentation matches implementation
- [ ] No duplicate entries in .gitignore
- [ ] Magic numbers extracted to named constants
- [ ] Specific exception types caught