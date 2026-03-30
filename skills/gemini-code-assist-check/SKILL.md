---
name: gemini-code-assist-check
version: "2.0.0"
description: >
  Offline code review skill based on 762 Gemini Code Assist comments from enmotech/db-ops-skills PRs.
  Audits code for security, robustness, JSON safety, exception handling, and consistency.
  Triggers: "audit this code", "review for Gemini standards", "offline code review", "check code quality".
metadata:
  openclaw:
    requires:
      bins: ["bash"]
    optionalBins: ["python3"]
env:
  - name: TARGET_PATH
    required: false
    description: Target file or directory to audit (defaults to current directory)
  - name: SEVERITY_FILTER
    required: false
    description: Minimum severity level to report (critical, high, medium, all). Default: all
tools:
  - bash: Required. Executes audit scripts.
  - python3: Optional. Runs advanced static analysis.
files:
  read:
    - references/pattern-analysis.md: Gemini comment pattern analysis
    - references/json-safety-patterns.md: JSON generation best practices
    - references/exception-handling-guide.md: Exception handling patterns
    - references/consistency-checklist.md: Cross-file consistency rules
    - references/fix-verification-guide.md: Fix verification and global search strategies
    - <workspace_dir>/task-list.json: Audit state
    - <workspace_dir>/audit-report.md: Generated audit report
  write:
    - <workspace_dir>/task-list.json: Audit state updates
    - <workspace_dir>/audit-report.md: Final audit report
---

# Gemini Code Assist Checker

离线代码审计技能，基于对 **762 条 Gemini Code Assist 评论**的分析，覆盖 **33 个 PR**。

> ⚠️ **审计原则**: 宁可误报不可漏报。Critical 问题必须阻断合并，High 问题建议修复后合并，Medium 问题可记录后续处理。

---

## 统计概览

| 严重性 | 数量 | 占比 |
|--------|------|------|
| Critical | 79 | 10% |
| High | 191 | 25% |
| Medium | 492 | 65% |

---

## 问题类别分布

> [!IMPORTANT]
> 在执行审计前，阅读 `references/pattern-analysis.md` 获取详细的问题模式分析。

| 类别 | 出现次数 | 优先级 | 说明 |
|------|----------|--------|------|
| **一致性性问题** | 128 | HIGH | 配置键名不匹配、命令格式不一致、文档与代码不符 |
| **硬编码问题** | 103 | HIGH | 硬编码路径、阈值、密码 |
| **配置问题** | 55 | HIGH | 配置缺失、配置键名不匹配、缺少依赖声明 |
| **文档与实现不符** | 39 | MEDIUM | 脚本名称、功能描述、输出格式不一致 |
| **密码/凭证安全** | 31 | CRITICAL | 明文密码、命令行密码、凭证文件 |
| **阈值/常量问题** | 29 | MEDIUM | 魔法数字、重复阈值定义 |
| **错误处理** | 26 | HIGH | 无错误消息、静默失败、验证无反馈 |
| **命令注入风险** | 20 | CRITICAL | 字符串格式化命令、shell=True |
| **JSON 生成问题** | 14 | CRITICAL | 尾部逗号、空值、未转义字符 |
| **异常处理** | 12 | HIGH | 静默 pass、错误异常类型 |
| **Shell 兼容性** | 8 | MEDIUM | Bashism、GNU 特定选项 |
| **资源管理** | 7 | MEDIUM | 无 finally、无上下文管理器 |

---

## 审计工作流

### Step 1: 确定审计范围

**输入**: 用户指定的文件/目录，或当前工作目录

**动作**:
1. 扫描目标路径下的所有代码文件（`.py`, `.sh`, `.yaml`, `.md`）
2. 统计文件数量，展示审计范围概览
3. 创建工作区目录：`~/.moclaw/workspace/gemini-code-assist-check-<timestamp>/`

---

### Step 2: 执行审计检查

按以下优先级顺序执行检查：

#### 2.1 Critical 级别检查（阻断性问题）

> [!CAUTION]
> Critical 问题必须全部修复后才能合并。

| 检查项 | 描述 | 检测模式 |
|--------|------|----------|
| **硬编码密码** | 代码中明文存储密码 | `password\s*=\s*['\"][^'\"]+['\"]` |
| **命令注入风险** | 用户输入直接拼接到命令 | `format\([^)]*\)`, `f"[^"]*\{` |
| **JSON 格式错误** | Shell 生成的 JSON 无效 | `echo.*,\s*$`, `"field":\s*,` |
| **SSH 主机密钥验证禁用** | 中间人攻击风险 | `StrictHostKeyChecking\s*=\s*no` |
| **SQL 注入风险** | 字符串拼接 SQL | `f"SELECT.*{` |

#### 2.2 High 级别检查（功能性问题）

> [!WARNING]
> High 问题建议修复后再合并。

| 检查项 | 描述 | 检测模式 |
|--------|------|----------|
| **静默异常处理** | `except` 后无错误日志，静默吞掉异常 | 见下方详细检测脚本 |
| **配置键名不匹配** | YAML 和 Python 使用不同键名 | 需跨文件分析 |
| **硬编码阈值** | 阈值在代码中而非配置中 | `> [0-9][0-9]` 无 config 引用 |
| **命令行密码** | 密码在进程列表中可见 | `-W.*password`, `user/password@` |
| **缺少依赖声明** | Python 包无 requirements.txt | `import (paramiko\|yaml)` 无 requirements.txt |
| **SSH 输出编码** | 使用 sys.stdout.encoding 解码远程输出 | `sys\.stdout\.encoding.*decode` |
| **路径计算不一致** | 相同功能使用不同路径计算方式 | `dirname.*dirname` vs `os.path.dirname` |
| **JSON 换行符删除** | Shell 脚本中 `tr -d '\n'` 破坏多行数据 | `tr -d.*\\n.*json\|_json_escape.*tr -d` |

> [!IMPORTANT]
> **静默异常处理检测详解**
>
> 问题模式不止 `except: pass`，还包括：
> - `except Exception: return "Unknown"` — 返回值但无日志
> - `except Exception as e:` 但未打印 `e` 到 stderr
> - `except Exception:` 后接任何非日志语句
>
> **检测脚本**（需使用 grep -P 支持多行匹配）：
> ```bash
> # 检测所有 except Exception 后接非日志语句的情况
> grep -rnP 'except\s+(Exception|\w+).*:\s*\n\s*(?!print.*file=sys\.stderr|logging\.)[^\n]*(return|pass|=)' --include="*.py"
> ```
>
> **手动验证步骤**：
> 1. 搜索所有 `except Exception` 出现位置
> 2. 检查每个位置是否有 `print(..., file=sys.stderr)` 或日志输出
> 3. 确认 `as e` 是否被使用

#### 2.3 Medium 级别检查（维护性问题）

| 检查项 | 描述 | 检测模式 |
|--------|------|----------|
| **文档与实现不符** | 文档描述与代码行为不一致 | 需人工验证 |
| **.gitignore 重复** | 同一条目出现多次 | `sort \| uniq -d` |
| **魔法数字** | 未命名的常量 | 上下文分析 |
| **Shell 兼容性** | Bashism in POSIX | `^\[\[` with `#!/bin/sh` |
| **警告输出到 stdout** | 警告应输出到 stderr | `print.*Warning.*\)` 无 `sys.stderr` |
| **正则表达式位置** | 常量正则定义在函数内 | `def.*\n.*re.compile` |
| **SQL 结果错误检查** | SQL 结果解析前未检查错误 | `sql_results.*get\(` 无 `ORA-` 检查 |
| **df 输出解析健壮性** | split 无法处理文件系统名中的空格 | `split.*df\|df.*awk` |
| **文件末尾换行符** | 文件末尾缺少换行符（违反 POSIX） | `tail -c 1 \| wc -l` |

---

### Step 3: 生成审计报告

**输出格式**: Markdown 报告

```markdown
# Code Audit Report

## Summary
| Severity | Count | Action |
|----------|-------|--------|
| Critical | X | Must fix before merge |
| High | X | Should fix |
| Medium | X | Consider fixing |

## Critical Issues
### 1. [File:Line] Issue Title
**Description**: ...
**Code**:
```language
// problematic code
```
**Suggestion**:
```language
// fixed code
```

## High Issues
...

## Medium Issues
...
```

---

## 评论处理工作流

> [!IMPORTANT]
> 当收到 Gemini Code Assist 或其他评审者的评论时，遵循以下流程确保一次性解决问题。
>
> **阅读 `references/fix-verification-guide.md` 获取完整的修复验证指南。**

### Step 1: 模式识别

不要只关注评论指出的具体位置，要理解问题**模式**：

| 评论示例 | 问题模式 | 需要搜索的位置 |
|----------|----------|----------------|
| "encoding missing at line 149" | **编码问题** | 所有 `open()`, `.decode()`, `.encode()` 调用 |
| "dirname called 2 times, should be 3" | **路径计算问题** | 所有 `dirname`, `os.path.dirname` 调用 |
| "hardcoded threshold 85" | **硬编码问题** | 所有阈值、魔法数字 |
| "config key mismatch" | **配置键名问题** | YAML 和 Python 中的所有键名 |

### Step 2: 全局搜索

收到评论后，**必须**全局搜索同类问题：

```bash
# 编码问题
grep -rn "sys.stdout.encoding" . --include="*.py"
grep -rn "\.decode(" . --include="*.py"
grep -rn "open(" . --include="*.py" | grep -v "encoding"

# 路径计算问题
grep -rn "dirname" . --include="*.py" --include="*.sh"
grep -rn "os.path.dirname" . --include="*.py"

# 配置键名问题
grep -E "^\s+[a-z_]+:" config.yaml  # 获取所有 YAML 键名
grep -rn "\.get\(['\"][a-z_]+['\"]" . --include="*.py"  # 获取所有代码引用
```

### Step 3: 批量修复

一次性修复所有发现的同类问题，不要只修复评论指出的位置。

**示例**：
```
评论指出: collector.py:149 encoding 问题

全局搜索发现:
- collector.py:149 - 需修复 ✅ 评论指出
- collector.py:150 - 需修复 ✅ 同类问题
- parser.py:361 - 已正确 ✅ 无需修改
- generator.py:295 - 需修复 ✅ 同类问题
```

### Step 4: 验证修复

修复后必须验证：

1. **语法正确性**: `python -m py_compile <file>`
2. **逻辑正确性**: 理解代码意图，验证修复方式正确（非"改了就行"）
3. **完整性检查**: 再次全局搜索，确认无遗漏
4. **一致性检查**: 确保其他位置的同类代码使用相同方式

### Step 5: 回复评论

回复时说明：
- 具体修复内容（附带代码片段）
- 是否同时修复了其他同类位置
- 修复的 commit hash
- 验证方法

**回复模板**：
```markdown
Thank you for catching this. I have fixed the issue in commit <hash>.

**The Fix:**
<描述修复内容>

**Code Change:**
```python
# Before
<修复前代码>

# After
<修复后代码>
```

**Global Search:**
I also searched for similar issues across the codebase:
- `file1.py:123` - ✅ Already correct
- `file2.py:456` - ✅ Fixed in this commit
```

### 常见错误

| 错误类型 | 描述 | 预防措施 |
|----------|------|----------|
| **声称修复但未修复** | 回复说修复了，但代码未变更 | 修复前后都用 `git diff` 验证 |
| **修复方式错误** | 修复了但方式不对 | 理解问题根因，验证逻辑正确性 |
| **遗漏同类问题** | 只修复评论位置，遗漏其他 | 全局搜索 + 列出所有位置 |

---

## 审计规则详解

### 规则 1: 一致性检查 (128 次出现)

> [!IMPORTANT]
> 一致性问题是 Gemini Code Assist 最常报告的问题类型 (17%)。

**检查项**:

#### 1.1 配置键名一致性

```yaml
# config.yaml
collection_sql:
  - key: "archive_dest"  # 键名
```

```python
# parser.py - 必须匹配
archive = data.get('sql_results', {}).get('archive_dest')  # ✅ 正确
# archive = data.get('archive_status')  # ❌ 错误键名
```

#### 1.2 命令格式一致性

```python
# SSH 模式
df_h_raw = run_remote(client, "df -Ph")

# 离线模式 - 必须使用相同格式
df -Ph  # ✅ 正确
# df -P  # ❌ 格式不一致
```

---

### 规则 2: 硬编码检查 (103 次出现)

**检查项**:

| 类型 | 示例 | 修复方案 |
|------|------|----------|
| 路径 | `/u01/app/oracle` | 使用 `{ORACLE_BASE}` 变量 |
| 阈值 | `if pct > 85:` | 从 config.yaml 读取 |
| 端口 | `port = 1521` | 使用环境变量或配置 |
| 密码 | `password = "sys"` | 使用环境变量或 Wallet |

---

### 规则 3: JSON 安全性 (14 次出现)

> 阅读 `references/json-safety-patterns.md` 获取完整指南。

**问题模式**:

```bash
# ❌ 错误 - 尾部逗号
echo "  \"key\": \"value\","
echo "}"

# ✅ 正确 - prefix-comma 模式
FIRST=1
for item in $items; do
    if [ $FIRST -eq 1 ]; then
        echo "  \"$item\""
        FIRST=0
    else
        echo "  ,\"$item\""
    fi
done
```

```bash
# ❌ 错误 - 空值导致无效 JSON
echo "\"count\": $COUNT,"
# 如果 COUNT 为空: "count": ,

# ✅ 正确 - 使用默认值
echo "\"count\": ${COUNT:-0},"
```

---

### 规则 4: 异常处理可见性 (12+ 次出现)

> 阅读 `references/exception-handling-guide.md` 获取完整指南。

> [!IMPORTANT]
> **此问题在 PR 中反复出现。修复时必须全局搜索所有 `except Exception` 位置，一次性修复所有同类问题。**

**问题模式（全部需要修复）**:

```python
# ❌ 模式 A - 静默 pass
except Exception:
    pass

# ❌ 模式 B - 静默返回值（无日志）
except Exception:
    return "Unknown"

# ❌ 模式 C - 有 as e 但未打印
except Exception as e:
    return "Unknown"  # e 未被使用

# ❌ 模式 D - 打印到 stdout（应为 stderr）
except Exception as e:
    print(f"Warning: {e}")  # 缺少 file=sys.stderr

# ✅ 正确模式 - 打印警告到 stderr
import sys
except Exception as e:
    print(f"Warning: Operation failed: {e}", file=sys.stderr)
    return "Unknown"  # 可选：返回默认值
```

**检测步骤**:

```bash
# Step 1: 找出所有 except Exception 位置
grep -rn "except Exception" . --include="*.py"

# Step 2: 检查每个位置是否有正确的错误日志
# 正确的代码包含: print(..., file=sys.stderr) 或 logging.error/warning

# Step 3: 确认 as e 是否存在
grep -rn "except Exception:" . --include="*.py"  # 无 as e - 可能有问题
grep -rn "except Exception as e:" . --include="*.py"  # 有 as e - 检查是否打印
```

**常见错误**:

| 错误 | 描述 | 修复 |
|------|------|------|
| 只修复评论位置 | 遗漏其他同类问题 | 全局搜索后列出所有位置 |
| 添加 as e 但未打印 | 形式上修复但无实际日志 | 必须添加 print(..., file=sys.stderr) |
| 打印到 stdout | 日志与正常输出混杂 | 使用 file=sys.stderr |

---

### 规则 5: 命令注入防护 (20 次出现)

**问题模式**:

```python
# ❌ 错误 - 用户输入直接格式化到命令
cmd = f"ls {user_input}"
subprocess.run(cmd, shell=True)

# ✅ 正确 - 使用列表形式
subprocess.run(["ls", user_input])

# ✅ 正确 - 或使用 shlex.quote()
import shlex
subprocess.run(f"ls {shlex.quote(user_input)}", shell=True)
```

---

### 规则 6: 密码安全 (31 次出现)

**问题模式**:

```bash
# ❌ 错误 - 密码在命令行可见
sqlplus sys/password@host:1521/orcl

# ✅ 正确 - 通过 stdin 传递密码
echo "$PASSWORD" | sqlplus sys@host:1521/orcl as sysdba
```

```python
# ❌ 错误 - 硬编码密码
password = "oracle123"

# ✅ 正确 - 从环境变量获取
import os
password = os.environ.get("ORACLE_PASSWORD")
```

---

### 规则 7: JSON 换行符处理 (新增)

**问题模式**:

```bash
# ❌ 错误 - tr -d '\n' 删除换行符，破坏多行数据
_json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n'
}

# ✅ 正确 - 转义换行符为 \n
_json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g'
}
```

**影响**: 多行 SQL 结果（如 `fra_status`, `archive_dest`）会被破坏。

---

### 规则 8: 警告输出流 (新增)

**问题模式**:

```python
# ❌ 错误 - 警告输出到 stdout
print(f"Warning: Could not parse line: '{line}'")

# ✅ 正确 - 警告输出到 stderr
import sys
print(f"Warning: Could not parse line: '{line}'", file=sys.stderr)
```

**原因**: 分离标准输出和错误/警告信息流，便于日志处理和管道操作。

---

### 规则 9: 正则表达式位置 (新增)

**问题模式**:

```python
# ❌ 错误 - 正则表达式定义在函数内部
def main():
    _SID_RE = re.compile(r'^[A-Za-z0-9_]{1,30}$')
    # ...

# ✅ 正确 - 正则表达式定义在模块级别
_SID_RE = re.compile(r'^[A-Za-z0-9_]{1,30}$')

def main():
    # ...
```

**原因**: 模块级常量更清晰，避免每次函数调用重新编译。

---

### 规则 10: SQL 结果错误检查 (新增)

**问题模式**:

```python
# ❌ 错误 - 直接解析 SQL 结果，未检查错误
fra_raw = data.get('sql_results', {}).get('fra_status', '')
if fra_raw:
    lines = fra_raw.strip().split('\n')
    # 直接开始解析，如果 SQL 失败会尝试解析错误消息

# ✅ 正确 - 先检查 SQL 错误，再解析
fra_raw = data.get('sql_results', {}).get('fra_status', '')
if fra_raw:
    # 检查 SQL 错误（与 archive_dest 处理方式一致）
    if any(err in fra_raw.upper() for err in ['ERROR', 'ORA-', 'CANNOT']):
        risks.append({'level': 'Warning', 'item': 'FRA Status Query Error',
                      'value': fra_raw[:80], 'threshold': 'No error'})
    else:
        lines = fra_raw.strip().split('\n')
        # 继续解析...
```

**检查项**:

| SQL 结果键名 | 是否需要错误检查 | 说明 |
|--------------|------------------|------|
| `fra_status` | ✅ 需要 | 解析数值，计算使用率 |
| `archive_dest` | ✅ 需要 | 已有错误检查 |
| `fra_path` | ❌ 不需要 | 仅用于路径替换 |
| `adr_home` | ❌ 不需要 | 仅用于路径替换 |
| `db_unique_name` | ❌ 不需要 | 简单字符串值 |

**一致性原则**: 所有需要解析并产生风险的 SQL 结果，都应先检查错误。

**检测模式**:
```bash
# 查找所有 SQL 结果引用
grep -rn "sql_results.*get\(" . --include="*.py"

# 查找已有错误检查的
grep -rn "ORA-\|ERROR.*sql_results" . --include="*.py"
```

---

### 规则 11: df 输出解析健壮性 (新增)

**问题模式**:

```python
# ❌ 错误 - split 无法处理文件系统名中的空格
parts = line.split(None, 5)
if len(parts) == 6:
    rows.append({'filesystem': parts[0], ...})

# ✅ 正确 - 使用正则表达式
import re
_DF_PATTERN = re.compile(
    r'^(?P<filesystem>.+?)\s+(?P<size>\S+)\s+(?P<used>\S+)\s+(?P<avail>\S+)\s+(?P<pct>\S+%?)\s+(?P<mount>.+)$'
)
match = _DF_PATTERN.match(line.strip())
if match:
    rows.append(match.groupdict())
```

```bash
# ❌ 错误 - awk 假设 $1 是完整 filesystem 名
df -Ph | awk '{print $1}'  # 如果 filesystem 是 "My FS"，只得到 "My"

# ✅ 正确 - 使用 perl 正则表达式
df -Ph | perl -ne 'if (/^(.+?)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+%?)\s+(.+)$/) { ... }'
```

**触发场景**:
- 网络挂载点名称含空格（如 `//server/share name`）
- 某些卷管理器配置
- 生产环境罕见，但理论上可能发生

**检测模式**:
```bash
# 查找 awk 解析 df 的代码
grep -rn "df.*awk" . --include="*.sh" --include="*.py"

# 查找 split 解析 df 的代码
grep -rn "split.*df\|df.*split" . --include="*.py"
```

---

### 规则 12: 文件末尾换行符 (新增)

**问题模式**:

```bash
# ❌ 错误 - 文件末尾没有换行符
$ cat file.txt
line1
line2$  # 光标在行尾，无换行

# ✅ 正确 - POSIX 标准要求文本文件以换行符结尾
$ cat file.txt
line1
line2
$  # 光标在新行
```

**影响**:
- 某些工具可能不正确处理最后一行
- POSIX 标准要求文本文件以换行符结尾
- Git diff 显示 "No newline at end of file"

**检测模式**:
```bash
# 检测文件末尾是否有换行符
for f in $(find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.json" -o -name "*.md" -o -name "*.yaml" -o -name "*.txt" \)); do
    if [ -f "$f" ] && [ "$(tail -c 1 "$f" | wc -l)" -eq 0 ]; then
        echo "Missing newline: $f"
    fi
done
```

**修复方法**:
```bash
# 添加末尾换行符
echo "" >> file.txt
```

---

## 快速审计脚本

```bash
#!/bin/bash
# 快速审计 - 检测常见问题

TARGET="${TARGET_PATH:-.}"

echo "=== Gemini Code Assist Quick Audit ==="

# Critical: JSON 格式
echo "Checking JSON safety..."
grep -rn 'echo.*,\s*$' "$TARGET" --include="*.sh"
grep -rn '"[^"]*":\s*,' "$TARGET" --include="*.sh"

# Critical: 硬编码密码
echo "Checking hardcoded passwords..."
grep -rn "password\s*=\s*['\"][^'\"]*['\"]" "$TARGET" --include="*.py"

# Critical: JSON 换行符处理
echo "Checking JSON newline handling..."
grep -rn "tr -d.*\\\\n.*json" "$TARGET" --include="*.sh"
grep -rn "_json_escape.*tr -d" "$TARGET" --include="*.sh"

# High: 静默异常（全面检测）
echo "Checking silent exceptions..."
echo "  [1] 查找所有 except Exception 位置..."
grep -rn "except Exception" "$TARGET" --include="*.py"
echo "  [2] 查找无 as e 的..."
grep -rn "except Exception:" "$TARGET" --include="*.py"
echo "  [3] 查找有 as e 但可能未打印的..."
grep -rn "except Exception as e:" "$TARGET" --include="*.py"
echo "  [4] 查找 pass 隐藏错误的..."
grep -rnP 'except\s+\w+.*:\s*\n\s*pass' "$TARGET" --include="*.py"

# High: JSON 换行符删除
echo "Checking tr -d '\n' in JSON context..."
grep -rn "tr -d.*\\n" "$TARGET" --include="*.sh" | grep -i json

# Medium: df 解析健壮性
echo "Checking df parsing robustness..."
grep -rn "df.*awk" "$TARGET" --include="*.sh" --include="*.py"
grep -rn "split.*df\|df.*split" "$TARGET" --include="*.py"

# Medium: .gitignore 重复
echo "Checking .gitignore duplicates..."
sort .gitignore | uniq -d

# Medium: 文件末尾换行符
echo "Checking trailing newlines..."
for f in $(find "$TARGET" -type f \( -name "*.py" -o -name "*.sh" -o -name "*.json" -o -name "*.md" -o -name "*.yaml" -o -name "*.txt" \)); do
    if [ -f "$f" ] && [ "$(tail -c 1 "$f" | wc -l)" -eq 0 ]; then
        echo "Missing newline: $f"
    fi
done
```

---

## 报告规范

审计报告必须包含：

1. **执行摘要** - 问题总数、各级别数量、审计范围
2. **Critical 问题详情** - 文件路径、行号、问题描述、修复建议代码
3. **High 问题详情** - 同上格式
4. **Medium 问题详情** - 可简化展示
5. **统计数据** - 扫描文件数、分析行数、应用检查数
6. **通过项列表** - 已验证无问题的检查项

---

## 安全

- 审计过程只读取文件，不修改任何代码
- 报告中如发现凭证明文，必须掩码显示
- 生成的报告保存在工作区目录，不污染源代码目录

---

## 附录: 最常见的 Gemini Code Assist 评论

### Critical 级别

```
"Hardcoded password in plain text"
"Command injection vulnerability"
"Invalid JSON - trailing comma"
"SSH host key verification disabled"
```

### High 级别

```
"except Exception: pass silently swallows errors"
"except Exception: return 'Unknown' without logging the error"
"The broad except Exception clause silently swallows all errors, returning 'Unknown' without any indication of what went wrong"
"Configuration key mismatch between YAML and Python"
"Hardcoded threshold should be in config"
"Password exposed in command line arguments"
```

### Medium 级别

```
"Documentation inconsistent with implementation"
"Duplicate entry in .gitignore"
"Magic number should be extracted to constant"
"Consider using more specific exception type"
```