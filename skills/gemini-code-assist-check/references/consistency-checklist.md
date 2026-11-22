# Cross-File Consistency Checklist

> Reference document for Gemini Code Assist Checker skill.
> Read this when auditing consistency across multiple files.

## Categories of Consistency Issues

1. **Key Name Consistency** - YAML config keys vs Python code
2. **Command Format Consistency** - Same command across different modes
3. **Documentation Consistency** - SKILL.md vs actual behavior
4. **Threshold Consistency** - Hardcoded values vs config values

---

## 1. Key Name Consistency

### Problem Pattern

Config defines one key name, code reads a different one.

```yaml
# config.yaml
collection_sql:
  - key: "archive_dest"    # Key name: archive_dest
    query: "SELECT ..."
```

```python
# parser.py
archive = data.get('sql_results', {}).get('archive_status')  # Wrong key!
```

### Audit Steps

1. Extract all `key:` values from config.yaml
2. Search code for `get('...')` calls on those data sources
3. Verify exact string match

### Fix Pattern

```python
# Option A: Fix the code to match config
archive = data.get('sql_results', {}).get('archive_dest')

# Option B: If config is wrong, update config and verify all references
```

---

## 2. Command Format Consistency

### Problem Pattern

Same command uses different flags in different collection modes.

```python
# collector.py (SSH mode)
df_h_raw = run_remote(client, "df -Ph")

# generator.py (Offline mode - in shell template)
df -P    # Missing -h flag!
```

### Audit Steps

1. Identify all commands that appear in multiple files
2. Compare flags and arguments
3. Verify output format compatibility

### Common Inconsistencies to Check

| Command | SSH Mode | Offline Mode | Issue |
|---------|----------|--------------|-------|
| `df` | `-Ph` | `-P` | Human-readable vs 1K-blocks |
| `df -i` | `-Pi` | `-P -i` | Same output, different syntax |
| `find` | `-type f` | Missing | Count files vs all entries |
| `ps` | Full awk loop | `$NF` only | Robust vs fragile parsing |

---

## 3. Documentation Consistency

### Problem Pattern

SKILL.md describes behavior that doesn't match code.

```yaml
# SKILL.md
env:
  - name: DB_PORT
    description: Database port (default: 5432)
```

```python
# collector.py
DEFAULT_PORT = 1521  # Mismatch!
```

### Audit Steps

1. Extract all defaults from SKILL.md env section
2. Extract all defaults from code
3. Cross-reference for exact match

### Key Areas to Check

- Default port numbers
- Default file paths
- Threshold values in documentation vs config
- Supported database versions list
- Required tools/binaries list

---

## 4. Threshold Consistency

### Problem Pattern

Thresholds hardcoded in multiple places.

```yaml
# config.yaml
global_thresholds:
  disk_usage_pct: 85
```

```python
# parser.py
warn_t = thresholds.get('disk_usage_pct', 85)  # Duplicate!
```

```markdown
# SKILL.md
| Warning | disk usage > 85% |  # Third instance!
```

### Audit Steps

1. Find all threshold values in config.yaml
2. Search code for those same values hardcoded
3. Search documentation for those same values
4. Flag any value that appears in multiple places

### Recommended Pattern

```python
# Single source of truth in config.yaml
# Code uses thresholds.get('key') without default
# Documentation references "see config.yaml" instead of values
```

---

## 5. File Reference Consistency

### Problem Pattern

SKILL.md doesn't declare all files the skill reads/writes.

```yaml
# SKILL.md files.read section
- scripts/config.yaml
- scripts/collector.py
# Missing: scripts/requirements.txt!
```

### Audit Steps

1. Parse SKILL.md files.read and files.write sections
2. Scan scripts/ directory for all files
3. Identify any file not declared in SKILL.md
4. Check for hardcoded paths that should use <workspace_dir>

---

## 6. Duplicate Detection

### Problem Pattern

Same entry appears multiple times.

```bash
# .gitignore
.qoder/
...
.qoder/    # Duplicate!
```

### Audit Steps

```bash
# Check for duplicate lines
sort .gitignore | uniq -d

# Check for duplicate code patterns
# (Requires semantic analysis)
```

---

## Quick Audit Commands

```bash
# 1. Key name consistency
grep -r "key:" config.yaml | awk '{print $3}' | tr -d '"' > /tmp/config_keys.txt
grep -r "get('" scripts/*.py | grep -oP "get\('\K[^']+" > /tmp/code_keys.txt
diff /tmp/config_keys.txt /tmp/code_keys.txt

# 2. Command format consistency
echo "=== df commands ===" && grep -rn "df -P" scripts/
echo "=== find commands ===" && grep -rn "find.*-type" scripts/

# 3. Threshold duplication
grep -r "85\|90\|95" scripts/*.py config.yaml SKILL.md | grep -v "# "

# 4. .gitignore duplicates
sort .gitignore | uniq -d
```

---

## Checklist for Auditors

- [ ] All config keys are read with exact same key name in code
- [ ] Commands use same flags across SSH and offline modes
- [ ] Default values match between SKILL.md and code
- [ ] Thresholds defined in config.yaml, not duplicated in code/docs
- [ ] All script files declared in SKILL.md files section
- [ ] No duplicate entries in .gitignore
- [ ] All paths use <workspace_dir> not hardcoded directories