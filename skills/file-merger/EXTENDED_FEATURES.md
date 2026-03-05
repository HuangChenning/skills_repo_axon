# File Merger 扩展功能使用指南

## 新功能总览

File Merger 现在支持 7 大扩展功能，使文件合并更加强大和灵活。

---

## 🔸 功能 1: 递归扫描子目录

### 功能说明
自动扫描输入目录的所有子目录中的文件，无需手动整理文件。

### 使用场景
```
documents/
├── vol1/
│   ├── chapter1.md
│   └── chapter2.md
├── vol2/
│   ├── chapter3.md
│   └── chapter4.md
└── vol3/
    └── chapter5.md
```

### 命令示例

```bash
# 递归扫描所有子目录
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --recursive \
  --output-count 2
```

### 输出
```
扫描目录: ./documents (递归: True)
找到 5 个 .md 文件
  - documents/vol1/chapter1.md
  - documents/vol1/chapter2.md
  - documents/vol2/chapter3.md
  - documents/vol2/chapter4.md
  - documents/vol3/chapter5.md
```

---

## 🔸 功能 2: 正则表达式过滤文件

### 功能说明
使用正则表达式精确筛选要合并的文件，支持包含和排除两种模式。

### 命令示例

#### 2.1 包含模式
```bash
# 只合并以 "chapter_" 开头的文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --filter "chapter_.*" \
  --output-count 5

# 只合并包含 "report" 的文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type pdf \
  --filter ".*report.*" \
  --output-count 3

# 只合并 2023 年的文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --filter "2023.*" \
  --output-count 10
```

#### 2.2 排除模式
```bash
# 排除备份文件（以 ~ 结尾）
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --exclude ".*~$" \
  --output-count 5

# 排除临时文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --exclude "tmp|temp|backup" \
  --output-count 5

# 排除特定文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --exclude "(TODO|DRAFT)" \
  --output-count 5
```

#### 2.3 组合使用
```bash
# 包含特定模式，同时排除其他模式
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --filter "chapter_.*" \
  --exclude ".*draft.*" \
  --output-count 5
```

---

## 🔸 功能 3: 按文件大小平衡分配

### 功能说明
根据文件大小（而不是数量）平衡分配到输出文件，确保每个输出文件的大小相近。

### 对比

#### 方式 A：按数量分配（默认）
```
100个文件 → 10个输出
每个输出包含 10 个文件
```

#### 方式 B：按大小平衡（新功能）
```
总大小 100MB → 10个输出
每个输出约 10MB
```

### 命令示例

```bash
# 按文件大小平衡分配
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --balance-by-size \
  --output-count 10
```

### 输出示例

```
合并计划:
  源文件数: 20
  输出文件数: 4
  总大小: 2048000 字节, 每个输出目标大小: 512000 字节

输出 1: 5 个文件, 总大小: 505000 字节
输出 2: 5 个文件, 总大小: 515000 字节
输出 3: 5 个文件, 总大小: 510000 字节
输出 4: 5 个文件, 总大小: 518000 字节
```

### 适用场景
- 📄 **文档大小差异大**：有的文件很大，有的很小
- 📊 **需要均匀的输出**：希望每个输出文件大小相近
- 💾 **存储限制**：每个输出文件有大小限制

---

## 🔸 功能 4: 生成合并报告

### 功能说明
生成详细的 JSON 和 CSV 格式报告，记录合并过程的完整信息。

### 报告内容

#### JSON 报告包含：
- 时间戳
- 输入/输出目录
- 文件类型和扫描模式
- 文件统计
- 每个输出文件的详细信息
- 错误列表

#### CSV 报告包含：
- 摘要信息表
- 输出文件详情表
- 错误信息表

### 命令示例

```bash
# 生成 JSON 报告（自动生成 CSV）
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 10 \
  --generate-report report.json
```

### 输出文件

```
merged/
├── merged_1.md
├── merged_2.md
...
└── report.json    # JSON 报告
└── report.csv     # CSV 报告
```

### 报告示例

#### JSON 格式
```json
{
  "timestamp": "2026-03-05T02:30:00",
  "input_directory": "./documents",
  "output_directory": "./merged",
  "file_type": "md",
  "scan_mode": "递归",
  "total_files_found": 100,
  "total_files_processed": 100,
  "outputs_created": 10,
  "balance_mode": "按数量",
  "outputs": [
    {
      "name": "merged_1.md",
      "source_files": [
        {
          "path": "documents/chapter1.md",
          "name": "chapter1.md",
          "size": 1024,
          "hash": "abc123..."
        }
      ],
      "total_size": 10240
    }
  ],
  "errors": []
}
```

#### CSV 格式
```csv
合并报告摘要
时间戳,2026-03-05T02:30:00
输入目录,./documents
输出目录,./merged
文件类型,md
扫描模式,递归
发现文件数,100
处理文件数,100
创建输出数,10
平衡模式,按数量

输出文件,包含的源文件,文件数量,总大小(字节)
merged_1.md,chapter1.md, chapter2.md, ..., 10,10240
merged_2.md,chapter11.md, chapter12.md, ..., 10,10300
...
```

---

## 🔸 功能 5: 增量合并（只处理新文件）

### 功能说明
记录已处理的文件，后续运行只合并新增或修改的文件，避免重复处理。

### 工作原理

1. **首次运行**：处理所有文件，生成状态文件
2. **后续运行**：读取状态文件，只处理新文件
3. **状态保存**：更新状态文件记录已处理的文件

### 命令示例

#### 5.1 首次运行
```bash
# 第一次运行（处理所有文件）
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 10 \
  --incremental \
  --state-file merge_state.json
```

**输出**：
```
找到 100 个 .md 文件
处理 100 个文件，创建 10 个输出
状态已保存: merge_state.json
```

#### 5.2 后续运行
```bash
# 第二次运行（只处理新文件）
# 假设新增了 5 个文件
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 10 \
  --incremental \
  --state-file merge_state.json
```

**输出**：
```
加载状态文件: 100 个已处理文件
找到 105 个 .md 文件
跳过已处理文件（100 个）
处理 5 个新文件
状态已保存: merge_state.json
```

### 状态文件格式

```json
{
  "timestamp": "2026-03-05T02:30:00",
  "processed_files": [
    "documents/chapter1.md:abc123...",
    "documents/chapter2.md:def456...",
    ...
  ],
  "last_update": "2026-03-05T02:30:00"
}
```

### 使用场景

- 📅 **定期任务**：每天/每周合并新增文档
- 📂 **持续监控**：监控目录并自动合并新文件
- ⏱️ **节省时间**：跳过已处理的文件，只处理新内容

---

## 🔸 功能 6: 支持更多文件格式

### 新增格式

| 格式 | 扩展名 | 说明 | 处理方式 |
|------|--------|------|----------|
| **EPUB** | .epub | 电子书格式 | 基础合并（提取内容） |
| **HTML** | .html, .htm | 网页格式 | 提取 body，合并内容 |
| **RTF** | .rtf | 富文本格式 | 转换为文本 |
| **ODT** | .odt | OpenDocument 文本 | 提取文本内容 |

### 命令示例

#### 6.1 合并 EPUB
```bash
python3 scripts/merge_files.py \
  --input-dir ./ebooks \
  --output-dir ./merged \
  --file-type epub \
  --output-count 3
```

#### 6.2 合并 HTML
```bash
python3 scripts/merge_files.py \
  --input-dir ./webpages \
  --output-dir ./merged \
  --file-type html \
  --output-count 5
```

#### 6.3 合并 RTF
```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type rtf \
  --output-count 2
```

#### 6.4 合并 ODT
```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type odt \
  --output-count 2
```

### 处理所有类型

```bash
python3 scripts/merge_files.py \
  --input-dir ./mixed_documents \
  --output-dir ./organized \
  --file-type all \
  --output-count 10
```

---

## 🎯 组合使用示例

### 示例 1: 完整的文档整理流程

```bash
# 递归扫描所有子目录
# 只合并章节文件
# 按文件大小平衡分配
# 生成详细报告
python3 scripts/merge_files.py \
  --input-dir ./my_documents \
  --output-dir ./organized_docs \
  --file-type md \
  --recursive \
  --filter "chapter_.*" \
  --balance-by-size \
  --generate-report report.json \
  --output-count 10
```

### 示例 2: 自动化增量备份

```bash
# 定期任务脚本
python3 scripts/merge_files.py \
  --input-dir ./daily_notes \
  --output-dir ./weekly_notes \
  --file-type md \
  --recursive \
  --incremental \
  --state-file notes_state.json \
  --generate-report reports/backup_$(date +%Y%m%d).json \
  --output-count 4
```

### 示例 3: 复杂过滤和组织

```bash
# 从复杂目录结构中提取特定文件
# 排除临时和草稿文件
# 按大小平衡输出
python3 scripts/merge_files.py \
  --input-dir ./chaotic_folder \
  --output-dir ./organized \
  --file-type all \
  --recursive \
  --filter "(report|document|paper)" \
  --exclude "(tmp|temp|draft|backup|~$)" \
  --balance-by-size \
  --generate-report organization_report.json \
  --output-count 20
```

---

## 📊 性能优化建议

### 大文件集合处理

```bash
# 限制处理的文件数量
python3 scripts/merge_files.py \
  --input-dir ./large_collection \
  --output-dir ./batch1 \
  --file-type md \
  --total-files 100 \
  --output-count 10
```

### 分批处理

```bash
# 第一批
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./batch1 \
  --file-type md \
  --filter "^[a-m].*" \
  --output-count 5

# 第二批
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./batch2 \
  --file-type md \
  --filter "^[n-z].*" \
  --output-count 5
```

---

## 🔧 故障排查

### 问题 1: 正则表达式不生效

**解决**：使用 Python 正则表达式语法
```bash
# 正确
--filter "chapter_.*"

# 错误
--filter "chapter_*"
```

### 问题 2: 状态文件损坏

**解决**：删除状态文件，重新开始
```bash
rm merge_state.json
# 然后重新运行
```

### 问题 3: 某些格式无法合并

**解决**：检查是否安装了必要的依赖
```bash
pip3 install -r requirements.txt
```

---

## 📝 最佳实践

1. **测试优先**：使用 `--dry-run` 预览合并计划
2. **备份重要**：合并前备份源文件
3. **逐步验证**：先处理少量文件，确认结果
4. **使用报告**：生成报告便于审计和调试
5. **增量模式**：对于定期任务使用增量合并

---

## 🆕 所有功能一览表

| 功能 | 参数 | 说明 |
|------|------|------|
| **递归扫描** | `--recursive` | 扫描所有子目录 |
| **包含过滤** | `--filter PATTERN` | 正则表达式包含 |
| **排除过滤** | `--exclude PATTERN` | 正则表达式排除 |
| **大小平衡** | `--balance-by-size` | 按文件大小分配 |
| **生成报告** | `--generate-report FILE` | JSON/CSV 报告 |
| **增量合并** | `--incremental` | 只处理新文件 |
| **状态文件** | `--state-file FILE` | 状态存储路径 |
| **预览模式** | `--dry-run` | 预览不执行 |
| **自定义排序** | `--order-file FILE` | 指定文件顺序 |
| **限制数量** | `--total-files N` | 只处理前 N 个 |

---

所有扩展功能已完整实现并可以立即使用！🎉
