# PDF 批量下载器技能

## 描述

从指定网页提取所有 PDF 文档链接，并批量下载到本地目录。

## 功能

- 自动解析网页 HTML 提取所有 PDF 链接
- 根据链接文本或 URL 生成干净的文件名
- 支持并发下载提高效率
- 显示下载进度和统计信息
- 支持断点续传（跳过已下载文件）
- 自动创建输出目录
- 完善的错误处理和日志记录

## 参数

- `url`: 要扫描的网页 URL（必需）
- `output_dir`: 输出目录路径（可选，默认为 "pdf_downloads"）
- `max_workers`: 并发下载数量（可选，默认为 4）
- `filter_pattern`: URL 过滤正则表达式（可选，只下载匹配的 PDF）

## 使用示例

```bash
# 下载 Oracle 文档的所有 PDF
/pdf-batch-downloader https://docs.oracle.com/cd/E11882_01/nav/portal_booklist.htm

# 指定输出目录
/pdf-batch-downloader https://example.com/docs --output-dir my_pdfs

# 使用更多并发
/pdf-batch-downloader https://example.com/docs --max-workers 8

# 过滤特定 PDF
/pdf-batch-downloader https://example.com/docs --filter-pattern ".*guide.*"
```

## 输出

- 下载的 PDF 文件保存在指定目录
- 显示下载进度和完成统计
- 记录失败下载的 URL
