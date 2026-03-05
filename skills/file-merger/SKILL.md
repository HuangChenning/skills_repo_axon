---
name: file-merger
description: 文件批量合并技能。当用户需要合并多个文件时使用此技能。支持 Markdown、PDF、Word、TXT 文件的批量合并，可指定合并后的文件数量，自动生成目录索引和分隔符。适用于文档整理、资料归档、批量处理等场景。每当用户提到"合并文件"、"批量合并"、"整理文档"等相关需求时，即使没有明确说明，也应该主动考虑使用此技能。
user-invocable: true
---

# File Merger - 文件批量合并技能

## 功能概述

File Merger 是一个智能文件批量合并工具，可以将指定目录下的多个文件按用户指定的数量进行合并，自动生成目录索引和分隔符。

## 核心功能

**基础功能**
- **多格式支持**：Markdown (.md)、PDF (.pdf)、Word (.docx)、纯文本 (.txt)
- **均匀分配**：将 N 个文件平均合并成 M 个输出文件
- **类型隔离**：不同文件类型分别处理，不混合
- **保持格式**：输出文件保持与源文件相同的格式
- **自定义排序**：支持用户提供文件顺序列表
- **目录索引**：自动生成每个合并文件的目录
- **智能分隔**：在源文件之间添加清晰分隔符

**扩展功能（✅ 已实现）**
- **✅ 递归扫描子目录**：自动扫描所有子目录中的文件
- **✅ 正则表达式过滤**：使用正则表达式精确筛选文件
- **✅ 按文件大小平衡分配**：根据文件大小均匀分配到输出文件
- **✅ 生成合并报告**：生成 JSON 和 CSV 格式的详细报告
- **✅ 增量合并**：只处理新增或修改的文件，避免重复处理
- **✅ 支持更多格式**：EPUB、HTML、RTF、ODT 等文件格式
- **✅ 自然排序**：正确处理带数字的文件名（chapter_2 排在 chapter_10 前）

## 使用场景

- 📚 **文档整理**：将分散的章节文档合并成完整文档
- 📖 **资料归档**：将多个报告合并成少量归档文件
- 📝 **笔记整理**：将每日笔记按周/月合并
- 📋 **批量处理**：处理大量格式统一的文档
- 🗂️ **文件分组**：将相关文件分组管理

## 快速开始

### 1. 基本用法

```bash
# 将 100 个文件合并成 10 个
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --total-files 100 \
  --output-count 10

# 合并 PDF 文件
python3 scripts/merge_files.py \
  --input-dir ./reports \
  --output-dir ./merged_reports \
  --file-type pdf \
  --output-count 5

# 处理所有类型（分别处理）
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type all \
  --output-count 10
```

### 2. 自定义排序

创建一个排序文件 `file_order.txt`：

```
chapter1.md
chapter3.md
chapter2.md
appendix.md
```

然后使用：

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --order-file file_order.txt \
  --output-count 1
```

### 3. 输出格式说明

合并后的文件结构：

```
# 目录
1. 文件1
2. 文件2
3. 文件3
...

---

## 文件1内容
（原始内容）

---

## 文件2内容
（原始内容）

---

```

## 命令行参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--input-dir` | ✅ | 输入目录路径 |
| `--output-dir` | ✅ | 输出目录路径 |
| `--file-type` | ✅ | 文件类型 (md/pdf/docx/txt/all) |
| `--output-count` | ✅ | 要生成的输出文件数量 |
| `--order-file` | ❌ | 自定义排序文件路径 |
| `--total-files` | ❌ | 指定要处理的文件总数 |
| `--separator` | ❌ | 自定义分隔符（默认：---） |
| `--no-index` | ❌ | 不生成目录索引 |
| `--dry-run` | ❌ | 预览合并计划但不执行 |

## 工作流程

### 步骤 1：扫描文件

脚本会扫描输入目录，按文件类型分组：

```
输入目录/
├── doc1.md
├── doc2.md
├── doc3.pdf
├── doc4.pdf
└── doc5.txt

扫描结果：
- .md: 2 个文件
- .pdf: 2 个文件
- .txt: 1 个文件
```

### 步骤 2：排序文件

默认按文件名字母排序。如果提供了 `--order-file`，则按指定顺序：

```
file_order.txt:
chapter3.md
chapter1.md
chapter2.md

排序结果：
1. chapter3.md
2. chapter1.md
3. chapter2.md
```

### 步骤 3：计算分配

根据 `--output-count` 均匀分配：

```
100 个文件 ÷ 10 个输出 = 每个输出 10 个文件

合并计划：
输出1: 文件1-10
输出2: 文件11-20
...
输出10: 文件91-100
```

### 步骤 4：生成合并文件

对每个输出文件：
1. 生成目录索引（列出所有包含的源文件）
2. 按顺序合并文件内容
3. 在文件间添加分隔符
4. 保存到输出目录

## 使用示例

### 示例 1：合并 Markdown 文档

**场景**：将 50 个章节 Markdown 文件合并成 5 个部分

```bash
python3 scripts/merge_files.py \
  --input-dir ./chapters \
  --output-dir ./parts \
  --file-type md \
  --output-count 5
```

**输出**：
```
parts/
├── part_1.md    # 章节1-10
├── part_2.md    # 章节11-20
├── part_3.md    # 章节21-30
├── part_4.md    # 章节31-40
└── part_5.md    # 章节41-50
```

### 示例 2：合并 PDF 报告

**场景**：将 30 份月度报告合并成季度报告（4 个文件）

```bash
python3 scripts/merge_files.py \
  --input-dir ./monthly_reports \
  --output-dir ./quarterly_reports \
  --file-type pdf \
  --output-count 4
```

**输出**：
```
quarterly_reports/
├── merged_1.pdf    # Q1: 1-3月报告
├── merged_2.pdf    # Q2: 4-6月报告
├── merged_3.pdf    # Q3: 7-9月报告
└── merged_4.pdf    # Q4: 10-12月报告
```

### 示例 3：自定义顺序合并

**场景**：按特定顺序合并文档

```bash
# 创建排序文件
cat > order.txt << EOF
introduction.md
methods.md
results.md
discussion.md
conclusion.md
EOF

# 合并
python3 scripts/merge_files.py \
  --input-dir ./sections \
  --output-dir ./complete_paper \
  --file-type md \
  --order-file order.txt \
  --output-count 1
```

### 示例 4：批量处理多种类型

**场景**：分别处理目录中的所有类型

```bash
python3 scripts/merge_files.py \
  --input-dir ./mixed_documents \
  --output-dir ./organized \
  --file-type all \
  --output-count 10
```

**输出**：
```
organized/
├── md_merged_1.md
├── md_merged_2.md
...
├── pdf_merged_1.pdf
├── pdf_merged_2.pdf
...
├── docx_merged_1.docx
...
└── txt_merged_1.txt
...
```

## 排序文件格式

排序文件每行一个文件名（不含路径）：

```
# 可选：添加注释（以 # 开头）
chapter1.md
appendix_a.md
chapter2.md
appendix_b.md
```

**规则**：
- 每行一个文件名
- 空行忽略
- `#` 开头的行为注释
- 只需要列出要包含的文件（未列出的将被忽略）

## 输出文件命名

### Markdown
```
merged_1.md, merged_2.md, ... 或
part_1.md, part_2.md, ...
```

### PDF
```
merged_1.pdf, merged_2.pdf, ...
```

### Word
```
merged_1.docx, merged_2.docx, ...
```

### TXT
```
merged_1.txt, merged_2.txt, ...
```

## 高级选项

### 1. 仅处理指定数量的文件

```bash
# 只处理前 50 个文件（忽略其他）
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --total-files 50 \
  --output-count 5
```

### 2. 预览合并计划

```bash
# 查看将要执行的合并计划
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 10 \
  --dry-run
```

输出示例：
```
合并计划（预览）：
找到 100 个 .md 文件
将创建 10 个输出文件
每个输出包含约 10 个源文件

[输出 1] merged_1.md:
  - doc01.md → doc10.md

[输出 2] merged_2.md:
  - doc11.md → doc20.md

...

(实际文件不会被修改)
```

### 3. 自定义分隔符

```bash
# 使用自定义分隔符
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 5 \
  --separator "======="
```

### 4. 禁用目录索引

```bash
# 不生成目录，直接合并内容
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 5 \
  --no-index
```

## 实现细节

### 文件类型处理

| 格式 | 读取方式 | 合并方式 | 特殊处理 |
|------|---------|---------|---------|
| .md | 直接读取文本 | 拼接 + 分隔符 | 保持 Markdown 格式 |
| .pdf | PyPDF2/pdfplumber | 页面追加 | 保留原有页码 |
| .docx | python-docx | 段落追加 | 保持样式 |
| .txt | 直接读取文本 | 拼接 + 分隔符 | 编码自动检测 |

### 依赖库

```bash
# 安装依赖
pip3 install pypdf2 python-docx chardet

# 或使用 requirements.txt
pip3 install -r scripts/requirements.txt
```

## 错误处理

- **文件不存在**：跳过并记录警告
- **读取失败**：记录错误，继续处理其他文件
- **编码错误**：尝试多种编码，记录使用的编码
- **写入失败**：检查输出目录权限，提供详细错误信息

## 日志和报告

合并过程会生成详细日志：

```
[INFO] 开始扫描目录: ./documents
[INFO] 找到 100 个 .md 文件
[INFO] 排序方式: 文件名（字母）
[INFO] 合并计划: 100 个文件 → 10 个输出
[INFO] 正在处理输出 1/10...
[INFO]   已合并: doc01.md, doc02.md, ..., doc10.md
[INFO]   已保存: merged_1.md
...
[INFO] 合并完成！
[INFO] 成功: 10/10
[INFO] 输出目录: ./merged
```

## 注意事项

1. **备份重要文件**：合并操作会创建新文件，不会修改源文件，但仍建议备份
2. **文件编码**：TXT 文件会自动检测编码，建议使用 UTF-8
3. **大文件处理**：处理大量或大文件时可能需要较长时间
4. **磁盘空间**：确保输出目录有足够空间
5. **PDF 限制**：某些加密的 PDF 可能无法合并

## 常见问题

### Q: 如何处理不同编码的 TXT 文件？
A: 脚本会自动检测编码（UTF-8, GBK, etc.），如果检测失败会尝试多种编码。

### Q: 合并后的 PDF 页码会连续吗？
A: 是的，合并后的 PDF 会保持原始页码，需要重新编号的话可以使用 PDF 编辑工具。

### Q: 可以合并加密的 PDF 吗？
A: 不可以，需要先解密。脚本会跳过加密文件并记录警告。

### Q: 如何撤销合并？
A: 源文件不会被修改，只需删除输出目录即可。

### Q: 支持子目录递归吗？
A: 是的！使用 `--recursive` 参数可以递归扫描所有子目录。

### Q: 如何只合并特定模式的文件？
A: 使用 `--filter` 参数配合正则表达式，例如 `--filter "chapter_.*"` 只合并以 "chapter_" 开头的文件。

### Q: 可以按文件大小平衡分配吗？
A: 是的！使用 `--balance-by-size` 参数会根据文件大小均匀分配，而不是按文件数量。

### Q: 如何查看详细的合并信息？
A: 使用 `--generate-report report.json` 参数会生成详细的 JSON 和 CSV 格式报告。

### Q: 如何避免重复处理已合并的文件？
A: 使用 `--incremental` 和 `--state-file state.json` 参数，脚本会记录已处理的文件，下次只处理新文件。

## 高级格式支持

除基础格式外，还支持：
- **EPUB (.epub)** - 电子书格式
- **HTML (.html, .htm)** - 网页格式
- **RTF (.rtf)** - 富文本格式
- **ODT (.odt)** - OpenDocument 文本格式

使用 `--file-type all` 可以同时处理所有格式。

查看详细文档：[EXTENDED_FEATURES.md](EXTENDED_FEATURES.md)
