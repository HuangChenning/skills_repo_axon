# Exception Handling Guide for Python

> Reference document for Gemini Code Assist Checker skill.
> Read this before auditing Python exception handling patterns.

## Core Principles

1. **Never silently swallow exceptions** - Always log or re-raise
2. **Catch specific exceptions** - Not broad `Exception`
3. **Preserve exception chain** - Use `raise ... from e`
4. **Provide actionable context** - Include variable values in messages

---

## Pattern 1: Silent Exception Handling

### ❌ Wrong: Silent Pass

```python
try:
    config = load_config(path)
except Exception:
    pass  # Swallows all errors silently
```

### ✅ Correct: Log Warning

```python
try:
    config = load_config(path)
except FileNotFoundError:
    print(f"Warning: Config file not found: {path}, using defaults")
    config = DEFAULT_CONFIG
except json.JSONDecodeError as e:
    print(f"Warning: Invalid JSON in {path}: {e}")
    config = DEFAULT_CONFIG
```

### ✅ Correct: Non-Critical Operation Warning

```python
try:
    update_task_list(workspace_dir, updates)
except Exception as e:
    print(f"Warning: Failed to update task-list.json: {e}")
    # Non-fatal, continue execution
```

---

## Pattern 2: Broad Exception Catching

### ❌ Wrong: Catching Everything

```python
try:
    result = parse_data(raw)
except Exception:
    result = None
```

### ✅ Correct: Specific Exceptions

```python
try:
    result = parse_data(raw)
except (ValueError, KeyError) as e:
    print(f"Warning: Could not parse data: {e}")
    result = None
```

---

## Pattern 3: Parsing Error Handling

### ❌ Wrong: Ignoring Parse Failures

```python
for line in data_lines:
    parts = line.split('|')
    value = int(parts[2])  # May crash or fail silently
    results.append(value)
```

### ✅ Correct: Handle Parse Errors with Context

```python
for line in data_lines:
    parts = line.split('|')
    try:
        value = int(parts[2])
        results.append(value)
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse line '{line}': {e}")
        # Optionally: continue, append default, or collect errors
```

---

## Pattern 4: Exception Re-raising

### ❌ Wrong: Losing Context

```python
try:
    connect_database(host)
except Exception:
    raise Exception("Connection failed")  # Lost original error
```

### ✅ Correct: Preserve Chain

```python
try:
    connect_database(host)
except ConnectionError as e:
    raise DatabaseError(f"Failed to connect to {host}") from e
```

---

## Pattern 5: Resource Cleanup

### ❌ Wrong: No Cleanup on Error

```python
conn = open_connection()
data = conn.read()
conn.close()  # Never reached if read() fails
```

### ✅ Correct: Try-Finally

```python
conn = open_connection()
try:
    data = conn.read()
finally:
    conn.close()  # Always executed
```

### ✅ Better: Context Manager

```python
with open_connection() as conn:
    data = conn.read()
# Auto-closed even on exception
```

---

## Pattern 6: Custom Exceptions

### ❌ Wrong: Generic Exceptions

```python
if not valid:
    raise Exception("Invalid configuration")
```

### ✅ Correct: Custom Exception Class

```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

if not valid:
    raise ConfigurationError(f"Missing required field: {field}")
```

---

## Pattern 7: Error Propagation in CLI Tools

### ❌ Wrong: Exit in Module

```python
# In parser.py module
def parse_file(path):
    if not os.path.exists(path):
        sys.exit(1)  # Hard to test, hard to reuse
```

### ✅ Correct: Raise Exception, Handle in Main

```python
# In parser.py module
def parse_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

# In main()
def main():
    try:
        data = parse_file(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

---

## Gemini Code Assist Common Warnings

Based on PR review analysis, these are frequently flagged:

| Issue | Severity | Pattern to Avoid |
|-------|----------|------------------|
| `except Exception: pass` | High | Silent failure |
| `except ValueError: pass` | High | Parse failure hidden |
| `except: pass` | Critical | Catches KeyboardInterrupt |
| Bare `except:` | Critical | No exception type specified |
| `raise Exception()` | Medium | Generic exception type |

---

## Checklist for Auditors

When reviewing Python exception handling:

- [ ] No `except.*: pass` patterns without logging
- [ ] Specific exception types caught (not just `Exception`)
- [ ] Parse errors include the problematic input in warning
- [ ] Resource cleanup uses `try-finally` or context managers
- [ ] Custom exceptions defined for domain-specific errors
- [ ] No `sys.exit()` inside module functions
- [ ] Exception chain preserved with `raise ... from e`