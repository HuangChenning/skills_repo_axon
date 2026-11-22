# JSON Safety Patterns for Shell Scripts

> Reference document for Gemini Code Assist Checker skill.
> Read this before auditing shell scripts that generate JSON output.

## Core Principles

1. **Never produce trailing commas** - JSON does not allow them
2. **Never produce empty values** - `"key": ,` is invalid
3. **Use prefix-comma pattern** - Add comma BEFORE elements, not after
4. **Always escape special characters** - Backslashes, quotes, newlines

---

## Pattern 1: Prefix-Comma for Arrays

### ❌ Wrong: Suffix Comma

```bash
# This produces trailing comma on last element
echo "["
for item in $items; do
    echo "  \"$item\","
done
echo "]"
# Output: [ "a", "b", "c", ]  <- Invalid JSON
```

### ✅ Correct: Prefix Comma with Flag

```bash
echo "["
FIRST=1
for item in $items; do
    if [ $FIRST -eq 1 ]; then
        echo "  \"$item\""
        FIRST=0
    else
        echo "  ,\"$item\""
    fi
done
echo "]"
# Output: [ "a" , "b" , "c" ]  <- Valid JSON
```

### ✅ Correct: Build to Temp File, Process at End

```bash
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

for item in $items; do
    echo "\"$item\"" >> "$TMP_FILE"
done

echo "["
first=1
while IFS= read -r line; do
    if [ $first -eq 1 ]; then
        echo "  $line"
        first=0
    else
        echo "  ,$line"
    fi
done < "$TMP_FILE"
echo "]"
```

---

## Pattern 2: Conditional Object Fields

### ❌ Wrong: Unconditional Comma

```bash
# This breaks if $SQL_TMP is empty
if [ -s "$SQL_TMP" ]; then
    cat "$SQL_TMP"
fi
echo "      ,\"status\": \"complete\""  # Comma even when no prior content
# Output: { ,"status": "complete" }  <- Invalid
```

### ✅ Correct: Condition on Prior Content

```bash
if [ -s "$SQL_TMP" ]; then
    first=1
    while IFS= read -r line; do
        if [ $first -eq 1 ]; then
            echo "      $line"
            first=0
        else
            echo "      ,$line"
        fi
    done < "$SQL_TMP"
    echo "      ,\"status\": \"complete\""
else
    echo "      \"status\": \"complete\""
fi
```

---

## Pattern 3: Empty Variable Handling

### ❌ Wrong: Direct Variable Use

```bash
echo "\"count\": $COUNT,"
# If COUNT is empty: "count": ,  <- Invalid
```

### ✅ Correct: Default Values

```bash
echo "\"count\": ${COUNT:-0},"
# If COUNT is empty: "count": 0,  <- Valid
```

### ✅ Correct: Conditional Field

```bash
if [ -n "$COUNT" ]; then
    echo "\"count\": $COUNT,"
fi
```

---

## Pattern 4: String Escaping

### ❌ Wrong: Raw Variable in JSON

```bash
echo "\"hostname\": \"$HOSTNAME\","
# If HOSTNAME contains " or \ or newline: Invalid JSON
```

### ✅ Correct: Escape Function

```bash
_json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' -e 's/\r/\\r/g' | tr -d '\n'
}

escaped_hostname=$(_json_escape "$HOSTNAME")
echo "\"hostname\": \"$escaped_hostname\","
```

---

## Pattern 5: Nested Object Structure

### ❌ Wrong: Flat Structure in Wrong Nest

```bash
echo "{"
echo "  \"collection\": {"
echo "    \"directories\": ["
# ... directories ...
echo "    ],"
echo "    \"sql_results\": {"  # <- This is inside directories array!
```

### ✅ Correct: Proper Nesting

```bash
echo "{"
echo "  \"collection\": {"
echo "    \"directories\": ["
# ... directories ...
echo "    ],"
echo "    \"sql_results\": {"
# ... sql_results ...
echo "    }"
echo "  }"
echo "}"
```

---

## Checklist for Auditors

When reviewing shell scripts that generate JSON:

- [ ] All loops use prefix-comma pattern, not suffix-comma
- [ ] Empty variables use `${VAR:-default}` syntax
- [ ] Conditional fields check for prior content before adding comma
- [ ] All string values pass through escape function
- [ ] Object/array nesting is correct and balanced
- [ ] No trailing commas on last array element
- [ ] No trailing commas on last object field
- [ ] Test with empty data sets produces valid JSON