# File Merger 技能使用指南

## 快速开始

### 安装依赖

```bash
cd /Users/huangchenning/个人/github/web_crawler/.claude/skills/file-merger/scripts
pip3 install -r requirements.txt
```

### 基本用法

```bash
# 合并 Markdown 文件（20个→4个）
python3 scripts/merge_files.py \
  --input-dir ./test_input/md_files \
  --output-dir ./test_output \
  --file-type md \
  --output-count 4
```

### 输出结果

脚本会生成：
- `merged_1.md` - 包含 chapter_1 到 chapter_5
- `merged_2.md` - 包含 chapter_6 到 chapter_10
- `merged_3.md` - 包含 chapter_11 到 chapter_15
- `merged_4.md` - 包含 chapter_16 到 chapter_20

每个输出文件包含：
1. **目录索引** - 列出所有包含的源文件
2. **文件内容** - 按顺序合并的所有源文件内容
3. **分隔符** - `---` 分隔不同文件

### 预览模式

在实际合并前，可以先预览合并计划：

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 10 \
  --dry-run
```

### 自定义排序

创建排序文件 `order.txt`：

```
chapter_5.md
chapter_1.md
chapter_10.md
chapter_2.md
```

然后使用：

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --order-file order.txt \
  --output-count 1
```

### 处理多种文件类型

```bash
# 分别处理目录中的所有类型
python3 scripts/merge_files.py \
  --input-dir ./mixed_documents \
  --output-dir ./organized \
  --file-type all \
  --output-count 10
```

这会为每种文件类型（.md, .pdf, .docx, .txt）分别创建合并后的输出。

### 限制处理的文件数量

如果目录中有100个文件，但只想处理前50个：

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --total-files 50 \
  --output-count 5
```

### 自定义分隔符

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 5 \
  --separator "======="
```

### 禁用目录索引

```bash
python3 scripts/merge_files.py \
  --input-dir ./documents \
  --output-dir ./merged \
  --file-type md \
  --output-count 5 \
  --no-index
```

## 测试示例

### 测试1: 合并 Markdown 章节

```bash
# 创建测试文件
cd test_input/md_files
for i in {1..20}; do
  echo "# 章节 $i" > "chapter_$i.md"
done

# 合并
python3 scripts/merge_files.py \
  --input-dir test_input/md_files \
  --output-dir test_output \
  --file-type md \
  --output-count 4
```

### 测试2: 预览合并计划

```bash
python3 scripts/merge_files.py \
  --input-dir test_input/md_files \
  --output-dir test_output \
  --file-type md \
  --output-count 4 \
  --dry-run
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| Markdown | .md | 保持原有格式，添加目录索引 |
| PDF | .pdf | 使用 PyPDF2 追加页面 |
| Word | .docx | 使用 python-docx 合并文档 |
| 文本 | .txt | 自动检测编码，添加目录 |

## 常见问题

### Q: 如何处理大量文件？
A: 脚本已经优化，可以处理数百个文件。对于非常大的文件集合，建议分批处理。

### Q: 可以合并加密的 PDF 吗？
A: 不可以，需要先解密。脚本会跳过加密文件并记录警告。

### Q: 合并后的文件在哪里？
A: 在指定的 `--output-dir` 目录中，文件名格式为 `merged_1.md`, `merged_2.md` 等。

### Q: 如何撤销合并？
A: 源文件不会被修改，只需删除输出目录即可。

### Q: 文件排序是否正确？
A: 是的，脚本使用自然排序（natural sorting），所以 `chapter_2.md` 会排在 `chapter_10.md` 之前。
