#!/bin/bash
# quick_audit.sh - Quick code audit for Gemini Code Assist standards
# Usage: TARGET_PATH=/path/to/code ./quick_audit.sh

set -euo pipefail

TARGET="${TARGET_PATH:-.}"
SEVERITY="${SEVERITY_FILTER:-all}"
WORKSPACE_BASE="$HOME/.moclaw/workspace"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_DIR="$WORKSPACE_BASE/gemini-code-assist-check-$TIMESTAMP"

# Create workspace
mkdir -p "$REPORT_DIR"

echo "=== Gemini Code Assist Quick Audit ==="
echo "Target: $TARGET"
echo "Report: $REPORT_DIR"
echo "Started: $(date)"
echo ""

# Initialize counters
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0

# ═══════════════════════════════════════════════════════════════
# CRITICAL CHECKS
# ═══════════════════════════════════════════════════════════════

echo "■ Running Critical checks..."

# 1. JSON trailing comma in shell scripts
echo "  [1/5] JSON trailing comma..."
if grep -rn 'echo.*,\s*$' "$TARGET" --include="*.sh" > "$REPORT_DIR/critical-json-trailing-comma.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/critical-json-trailing-comma.txt")
    echo "    ⚠ Found $COUNT potential issues"
    CRITICAL_COUNT=$((CRITICAL_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 2. JSON empty value
echo "  [2/5] JSON empty value..."
if grep -rn '"[^"]*":\s*,' "$TARGET" --include="*.sh" > "$REPORT_DIR/critical-json-empty-value.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/critical-json-empty-value.txt")
    echo "    ⚠ Found $COUNT potential issues"
    CRITICAL_COUNT=$((CRITICAL_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 3. Hardcoded passwords
echo "  [3/5] Hardcoded passwords..."
if grep -rn "password\s*=\s*['\"][^'\"]*['\"]" "$TARGET" --include="*.py" --include="*.sh" --include="*.yaml" > "$REPORT_DIR/critical-hardcoded-password.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/critical-hardcoded-password.txt")
    echo "    ⚠ Found $COUNT potential issues"
    CRITICAL_COUNT=$((CRITICAL_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 4. Command injection risk (format strings)
echo "  [4/5] Command injection risk..."
if grep -rn '\.format\|f"' "$TARGET" --include="*.py" | grep -E 'subprocess|exec|system|run' > "$REPORT_DIR/critical-command-injection.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/critical-command-injection.txt")
    echo "    ⚠ Found $COUNT potential issues"
    CRITICAL_COUNT=$((CRITICAL_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 5. Bare except
echo "  [5/5] Bare except clauses..."
if grep -rn 'except\s*:' "$TARGET" --include="*.py" > "$REPORT_DIR/critical-bare-except.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/critical-bare-except.txt")
    echo "    ⚠ Found $COUNT potential issues"
    CRITICAL_COUNT=$((CRITICAL_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# HIGH CHECKS
# ═══════════════════════════════════════════════════════════════

echo "■ Running High checks..."

# 1. Silent exception handling
echo "  [1/6] Silent exception handling..."
if grep -rnP 'except\s+\w+.*:\s*\n\s*pass' "$TARGET" --include="*.py" > "$REPORT_DIR/high-silent-exception.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-silent-exception.txt")
    echo "    ⚠ Found $COUNT potential issues"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 2. Unquoted shell variables
echo "  [2/6] Unquoted shell variables..."
if grep -rn '\$[A-Z_][A-Z0-9_]*[^}"'\''\\]' "$TARGET" --include="*.sh" | grep -v '\${' | grep -v '"\$' > "$REPORT_DIR/high-unquoted-variables.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-unquoted-variables.txt")
    echo "    ⚠ Found $COUNT potential issues (may include false positives)"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 3. Missing requirements.txt
echo "  [3/6] Dependency declaration..."
IMPORTS=$(grep -rh "^import\|^from" "$TARGET" --include="*.py" 2>/dev/null | grep -oE '(paramiko|yaml|jinja2|requests|flask|django)' | sort -u || true)
if [ -n "$IMPORTS" ]; then
    if [ ! -f "$TARGET/scripts/requirements.txt" ] && [ ! -f "$TARGET/requirements.txt" ]; then
        echo "    ⚠ External imports found but no requirements.txt: $IMPORTS"
        echo "Missing requirements.txt for: $IMPORTS" > "$REPORT_DIR/high-missing-requirements.txt"
        HIGH_COUNT=$((HIGH_COUNT + 1))
    else
        echo "    ✓ requirements.txt found"
    fi
else
    echo "    ✓ No external imports found"
fi

# 4. SSH host key verification
echo "  [4/6] SSH host key verification..."
if grep -rn 'StrictHostKeyChecking\s*=\s*no\|strict_host_key.*false' "$TARGET" --include="*.py" --include="*.yaml" > "$REPORT_DIR/high-ssh-no-verify.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-ssh-no-verify.txt")
    echo "    ⚠ Found $COUNT potential issues (SSH host key verification disabled)"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 5. SSH output encoding (sys.stdout.encoding for remote decoding)
echo "  [5/6] SSH output encoding..."
if grep -rn 'sys\.stdout\.encoding.*decode\|sys\.stdin\.encoding' "$TARGET" --include="*.py" > "$REPORT_DIR/high-ssh-encoding.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-ssh-encoding.txt")
    echo "    ⚠ Found $COUNT potential issues (using sys.stdout.encoding for remote data)"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 6. Missing file encoding in open() calls
echo "  [6/8] File encoding in open()..."
if grep -rn 'open([^)]*)' "$TARGET" --include="*.py" | grep -v 'encoding' | grep -v '#' > "$REPORT_DIR/high-missing-encoding.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-missing-encoding.txt")
    echo "    ⚠ Found $COUNT potential issues (may include false positives)"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 7. JSON newline deletion in shell scripts (breaks multi-line data)
echo "  [7/8] JSON newline deletion..."
if grep -rn "tr -d.*'\\\\n'" "$TARGET" --include="*.sh" > "$REPORT_DIR/high-json-newline-delete.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/high-json-newline-delete.txt")
    echo "    ⚠ Found $COUNT potential issues (tr -d '\\n' breaks multi-line JSON data)"
    HIGH_COUNT=$((HIGH_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 8. Regex constants defined inside functions
echo "  [8/8] Regex constants inside functions..."
if python3 -c "
import os
import re
for root, dirs, files in os.walk('$TARGET'):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fp:
                lines = fp.readlines()
            in_func = False
            func_indent = 0
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                if re.match(r'^(def |class )', stripped):
                    in_func = stripped.startswith('def ')
                    func_indent = indent
                elif in_func and indent <= func_indent and stripped and not stripped.startswith('#'):
                    in_func = False
                if in_func and 're.compile' in stripped and '_RE' in stripped:
                    print(f'{path}:{i}:{stripped.strip()[:50]}')
" > "$REPORT_DIR/high-regex-in-function.txt" 2>/dev/null; then
    if [ -s "$REPORT_DIR/high-regex-in-function.txt" ]; then
        COUNT=$(wc -l < "$REPORT_DIR/high-regex-in-function.txt")
        echo "    ⚠ Found $COUNT regex constants defined inside functions"
        HIGH_COUNT=$((HIGH_COUNT + COUNT))
    else
        echo "    ✓ No issues found"
    fi
else
    echo "    ✓ No issues found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# MEDIUM CHECKS
# ═══════════════════════════════════════════════════════════════

echo "■ Running Medium checks..."

# 1. .gitignore duplicates
echo "  [1/5] .gitignore duplicates..."
if [ -f "$TARGET/.gitignore" ]; then
    DUPES=$(sort "$TARGET/.gitignore" | uniq -d)
    if [ -n "$DUPES" ]; then
        echo "$DUPES" > "$REPORT_DIR/medium-gitignore-duplicates.txt"
        COUNT=$(echo "$DUPES" | wc -l)
        echo "    ⚠ Found $COUNT duplicate entries"
        MEDIUM_COUNT=$((MEDIUM_COUNT + COUNT))
    else
        echo "    ✓ No duplicates found"
    fi
else
    echo "    - No .gitignore file"
fi

# 2. TODO/FIXME comments
echo "  [2/5] TODO/FIXME comments..."
if grep -rn 'TODO\|FIXME\|XXX\|HACK' "$TARGET" --include="*.py" --include="*.sh" > "$REPORT_DIR/medium-todo-comments.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/medium-todo-comments.txt")
    echo "    ℹ Found $COUNT TODO/FIXME comments"
    MEDIUM_COUNT=$((MEDIUM_COUNT + COUNT))
else
    echo "    ✓ No TODO/FIXME found"
fi

# 3. Long functions (over 50 lines)
echo "  [3/5] Long function detection..."
# Simple heuristic: count lines between 'def ' and next 'def ' or end
python3 -c "
import os
import re
for root, dirs, files in os.walk('$TARGET'):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fp:
                content = fp.read()
            funcs = re.findall(r'(def \w+\([^)]*\):.*?)(?=\ndef |\nclass |\Z)', content, re.DOTALL)
            for func in funcs:
                lines = len(func.split('\n'))
                if lines > 50:
                    name = re.search(r'def (\w+)', func).group(1)
                    print(f'{path}:{name}:{lines} lines')
" > "$REPORT_DIR/medium-long-functions.txt" 2>/dev/null || true
if [ -s "$REPORT_DIR/medium-long-functions.txt" ]; then
    COUNT=$(wc -l < "$REPORT_DIR/medium-long-functions.txt")
    echo "    ℹ Found $COUNT functions over 50 lines"
    MEDIUM_COUNT=$((MEDIUM_COUNT + COUNT))
else
    echo "    ✓ No long functions found"
fi

# 4. Warnings output to stdout instead of stderr
echo "  [4/5] Warnings to stdout..."
if grep -rn 'print.*Warning' "$TARGET" --include="*.py" | grep -v 'sys.stderr' > "$REPORT_DIR/medium-warning-stdout.txt" 2>/dev/null; then
    COUNT=$(wc -l < "$REPORT_DIR/medium-warning-stdout.txt")
    echo "    ⚠ Found $COUNT warnings printing to stdout (should use stderr)"
    MEDIUM_COUNT=$((MEDIUM_COUNT + COUNT))
else
    echo "    ✓ No issues found"
fi

# 5. Regex constants defined inside functions (code style)
echo "  [5/5] Regex constants in functions..."
if [ -s "$REPORT_DIR/high-regex-in-function.txt" ]; then
    # Already detected in HIGH checks, just report
    COUNT=$(wc -l < "$REPORT_DIR/high-regex-in-function.txt")
    echo "    ℹ Found $COUNT regex constants inside functions (should be module-level)"
    # Don't double count - already in HIGH_COUNT
else
    echo "    ✓ No issues found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo "                        AUDIT SUMMARY                          "
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Critical Issues: $CRITICAL_COUNT (must fix before merge)"
echo "  High Issues:     $HIGH_COUNT (should fix)"
echo "  Medium Issues:   $MEDIUM_COUNT (consider fixing)"
echo ""
echo "  Total Issues:    $((CRITICAL_COUNT + HIGH_COUNT + MEDIUM_COUNT))"
echo ""
echo "═══════════════════════════════════════════════════════════════"

# Generate report
cat > "$REPORT_DIR/audit-report.md" << EOF
# Code Audit Report

**Generated**: $(date)
**Target**: $TARGET

## Summary

| Severity | Count | Action |
|----------|-------|--------|
| Critical | $CRITICAL_COUNT | Must fix before merge |
| High | $HIGH_COUNT | Should fix |
| Medium | $MEDIUM_COUNT | Consider fixing |
| **Total** | **$((CRITICAL_COUNT + HIGH_COUNT + MEDIUM_COUNT))** | |

## Critical Issues

$(if [ -s "$REPORT_DIR/critical-json-trailing-comma.txt" ]; then echo "### JSON Trailing Comma"; echo "\`\`\`"; cat "$REPORT_DIR/critical-json-trailing-comma.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/critical-json-empty-value.txt" ]; then echo "### JSON Empty Value"; echo "\`\`\`"; cat "$REPORT_DIR/critical-json-empty-value.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/critical-hardcoded-password.txt" ]; then echo "### Hardcoded Passwords"; echo "\`\`\`"; cat "$REPORT_DIR/critical-hardcoded-password.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/critical-command-injection.txt" ]; then echo "### Command Injection Risk"; echo "\`\`\`"; cat "$REPORT_DIR/critical-command-injection.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/critical-bare-except.txt" ]; then echo "### Bare Except"; echo "\`\`\`"; cat "$REPORT_DIR/critical-bare-except.txt"; echo "\`\`\`"; echo ""; fi)

## High Issues

$(if [ -s "$REPORT_DIR/high-silent-exception.txt" ]; then echo "### Silent Exception Handling"; echo "\`\`\`"; cat "$REPORT_DIR/high-silent-exception.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-unquoted-variables.txt" ]; then echo "### Unquoted Shell Variables"; echo "\`\`\`"; head -20 "$REPORT_DIR/high-unquoted-variables.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-missing-requirements.txt" ]; then echo "### Missing Requirements"; echo "\`\`\`"; cat "$REPORT_DIR/high-missing-requirements.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-ssh-no-verify.txt" ]; then echo "### SSH Host Key Verification Disabled"; echo "\`\`\`"; cat "$REPORT_DIR/high-ssh-no-verify.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-ssh-encoding.txt" ]; then echo "### SSH Output Encoding Issue"; echo "\`\`\`"; cat "$REPORT_DIR/high-ssh-encoding.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-missing-encoding.txt" ]; then echo "### Missing File Encoding"; echo "\`\`\`"; cat "$REPORT_DIR/high-missing-encoding.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-json-newline-delete.txt" ]; then echo "### JSON Newline Deletion"; echo "\`\`\`"; cat "$REPORT_DIR/high-json-newline-delete.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/high-regex-in-function.txt" ]; then echo "### Regex Constants in Functions"; echo "\`\`\`"; cat "$REPORT_DIR/high-regex-in-function.txt"; echo "\`\`\`"; echo ""; fi)

## Medium Issues

$(if [ -s "$REPORT_DIR/medium-gitignore-duplicates.txt" ]; then echo "### .gitignore Duplicates"; echo "\`\`\`"; cat "$REPORT_DIR/medium-gitignore-duplicates.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/medium-todo-comments.txt" ]; then echo "### TODO/FIXME Comments"; echo "\`\`\`"; cat "$REPORT_DIR/medium-todo-comments.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/medium-long-functions.txt" ]; then echo "### Long Functions (>50 lines)"; echo "\`\`\`"; cat "$REPORT_DIR/medium-long-functions.txt"; echo "\`\`\`"; echo ""; fi)
$(if [ -s "$REPORT_DIR/medium-warning-stdout.txt" ]; then echo "### Warnings to stdout (should use stderr)"; echo "\`\`\`"; cat "$REPORT_DIR/medium-warning-stdout.txt"; echo "\`\`\`"; echo ""; fi)

---
*Report generated by gemini-code-assist-check skill*
EOF

echo ""
echo "Detailed report saved to: $REPORT_DIR/audit-report.md"
echo ""

# Exit with appropriate code
if [ "$SEVERITY" = "critical" ] && [ $CRITICAL_COUNT -gt 0 ]; then
    exit 1
elif [ "$SEVERITY" = "high" ] && [ $((CRITICAL_COUNT + HIGH_COUNT)) -gt 0 ]; then
    exit 1
elif [ $CRITICAL_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi