# Web to Markdown

下载指定网页的内容并转换为格式化的 Markdown 文件。支持深度爬取、URL 过滤、关键字过滤和重复文件检测。

## 功能特性

### 核心功能
- 🌐 **单页/批量转换**: 支持单个 URL 或批量处理
- 🔍 **深度爬取**: 自动跟随链接，支持多层级爬取
- 🎯 **智能过滤**: URL 范围控制、关键字黑白名单
- 🔄 **重复检测**: 基于内容相似度的自动去重
- 📊 **统计报告**: 详细的爬取统计和日志
- ⚡ **并发下载**: 多线程并发下载，提升效率
- 🔁 **重试机制**: 自动重试失败的请求

### 高级功能
- **Sitemap 解析**: 自动从 sitemap.xml 获取 URL
- **URL 去重**: 相似 URL 智能过滤
- **跟踪参数移除**: 自动清理 URL 中的跟踪参数
- **关键字黑名单**: 过滤包含特定关键字的文章
- **文件内容查重**: 基于相似度阈值自动跳过重复文件

## 目录结构

```
web-to-markdown/
├── SKILL.md              # 技能定义文件
├── README.md             # 本文档
├── scripts/              # 核心脚本
│   ├── converter.py      # 主转换器
│   ├── crawler.py        # 深度爬虫
│   ├── scope.py          # URL 范围控制
│   ├── filters.py        # URL 过滤器
│   └── requirements.txt  # Python 依赖
├── assets/               # 配置文件示例
│   ├── config.example.yaml              # 完整配置示例
│   ├── config.oracle_11g_filtered.yaml  # Oracle 11g 爬取配置
│   ├── config.oracle_articles.yaml      # Oracle 文章爬取配置
│   ├── config.python_docs.yaml          # Python 文档爬取配置
│   └── config.deep_crawl.yaml           # 深度爬取配置
└── evals/                # 评估文件
    └── evals.json
```

## 安装依赖

```bash
pip3 install -r scripts/requirements.txt
```

### 依赖列表
- `requests` - HTTP 请求
- `beautifulsoup4` - HTML 解析
- `lxml` - XML/HTML 解析器
- `markdownify` - HTML 转 Markdown
- `tqdm` - 进度条显示
- `pyyaml` - YAML 配置文件支持

## 快速开始

### 1. 基本使用

```bash
# 转换单个网页
python3 scripts/converter.py https://example.com/article

# 指定输出目录
python3 scripts/converter.py https://example.com/article --output-dir my_output

# 使用关键字过滤
python3 scripts/converter.py https://example.com/article --keywords "Python教程"
```

### 2. 使用配置文件

```bash
# 使用 YAML 配置文件（推荐）
python3 scripts/converter.py --config assets/config.oracle_11g_filtered.yaml

# 配置文件 + 命令行参数覆盖
python3 scripts/converter.py --config config.yaml --max-workers 8
```

### 3. 深度爬取

```bash
# 爬取起始页及其所有直接链接（深度 1）
python3 scripts/converter.py https://docs.python.org --depth 1 --same-domain

# 更深层次的爬取（深度 2）
python3 scripts/converter.py https://example.com --depth 2 --same-domain
```

### 4. 批量处理

```bash
# 从文件读取 URL 列表
python3 scripts/converter.py --batch urls.txt

# 从 sitemap 获取 URL
python3 scripts/converter.py --sitemap https://example.com/sitemap.xml
```

## 配置选项

### YAML 配置文件

创建一个 YAML 配置文件（参考 `assets/config.example.yaml`）：

```yaml
# 基础设置
output_dir: "markdown_output"
timeout: 30
max_workers: 4
max_retries: 3
keywords: ""

# URL 来源
url: "https://example.com"

# URL 范围控制
scope:
  allow_domains:
    - "example.com"
  deny_paths:
    - "/admin/"
    - "/api/"

# 深度爬取
crawl:
  depth: 1
  same_domain: true
  delay: 0.5

# URL 过滤
filter:
  enable_similar: false
  similarity_threshold: 0.95
  disable_tracking: false

# 关键字黑名单
keyword_blacklist: "deprecated,archived"

# 文件查重（新增功能）
duplicate_threshold: 0.95  # 95% 相似度阈值

# 统计功能
enable_stats: true
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 网页 URL | - |
| `-o, --output-dir` | 输出目录 | `markdown_output` |
| `-k, --keywords` | 搜索关键词 | - |
| `-f, --filename` | 自定义文件名 | - |
| `-t, --timeout` | 请求超时（秒） | `30` |
| `-w, --max-workers` | 并发数量 | `4` |
| `-r, --max-retries` | 最大重试次数 | `3` |
| `-c, --config` | YAML 配置文件 | - |
| `-b, --batch` | 批量文件 | - |
| `--sitemap` | Sitemap URL | - |
| `--depth` | 爬取深度 | `0` |
| `--same-domain` | 只爬同域名 | `false` |
| `--filter-similar` | 启用 URL 过滤 | `false` |
| `--keyword-blacklist` | 关键字黑名单 | - |
| `--enable-stats` | 启用统计 | `false` |
| `--duplicate-threshold` | 文件查重阈值 | `0.0` |

### URL 范围控制

```bash
# 只允许特定域名
python3 scripts/converter.py https://example.com --allow-domains example.com,blog.example.com

# 排除特定路径
python3 scripts/converter.py https://example.com --deny-paths /admin/,/api/

# 使用正则表达式
python3 scripts/converter.py https://example.com --allow-regex "https://example\.com/.*tutorial.*"
```

## 功能详解

### 重复文件检测

新增的文件内容查重功能可以自动跳过内容相似的文件：

```yaml
# 在配置文件中设置
duplicate_threshold: 0.95  # 相似度 >= 95% 视为重复
```

或使用命令行：

```bash
python3 scripts/converter.py --config config.yaml --duplicate-threshold 0.95
```

**工作原理**：
- 使用 `difflib.SequenceMatcher` 计算文件内容相似度
- 相似度 >= 阈值时跳过保存，保留先下载的文件
- 线程安全，支持并发下载

**效果示例**：
```
[重复检测] 跳过重复文件: article_1.md (与 article.md 相似度 0.99)
```

### 深度爬取

深度爬取会自动跟随页面中的链接：

```yaml
crawl:
  depth: 2              # 爬取深度（0=只爬起始页，1=起始页+直接链接）
  same_domain: true     # 只爬取同域名下的链接
  delay: 0.5            # 请求间隔（秒）
```

**深度说明**：
- `depth: 0` - 只爬取起始 URL
- `depth: 1` - 爬取起始页 + 页面中的所有直接链接
- `depth: 2` - 爬取起始页 + 直接链接 + 二级链接

### 关键字过滤

```yaml
# 白名单：只保留包含这些关键字的内容
keywords: "Python,教程,入门"

# 黑名单：排除包含这些关键字的 URL
keyword_blacklist: "11gr1,11gR1,windows,deprecated"
```

### 统计报告

启用详细统计功能会生成 `_crawl_stats.txt` 报告：

```yaml
enable_stats: true
```

报告包含：
- 发现的总 URL 数
- 各级过滤统计（范围、相似度、关键字）
- 成功下载和失败的 URL 列表

## 配置示例

### 示例 1: Oracle 11g 文章爬取

使用 `assets/config.oracle_11g_filtered.yaml`：

```yaml
url: "https://oracle-base.com/articles/11g/"
keywords: "11g"
keyword_blacklist: "11gr1,11gR1,windows"
crawl:
  depth: 2
  same_domain: true
scope:
  allow_domains:
    - "oracle-base.com"
duplicate_threshold: 0.95
enable_stats: true
```

```bash
python3 scripts/converter.py --config assets/config.oracle_11g_filtered.yaml
```

### 示例 2: Python 文档爬取

```bash
python3 scripts/converter.py \
  https://docs.python.org/3/tutorial/ \
  --depth 1 \
  --same-domain \
  --allow-domains docs.python.org \
  --output-dir python_docs
```

### 示例 3: 带去重的批量爬取

```bash
python3 scripts/converter.py \
  --batch urls.txt \
  --filter-similar \
  --similarity-threshold 0.90 \
  --duplicate-threshold 0.95 \
  --enable-stats
```

## 输出格式

转换后的 Markdown 文件包含：

1. **元数据头部**（YAML frontmatter）：
```markdown
---
title: 文章标题
source: https://example.com/article
description: 文章描述
---
```

2. **正文内容**：
- 标题（# ## ###）
- 段落文本
- 链接（自动清理换行符）
- 列表
- 代码块

3. **自动清理**：
- 移除脚本、样式、导航等无关元素
- 清理广告和侧边栏
- 移除 HTML 注释
- 规范化空行

## 常见问题

### Q: 如何避免爬取过多内容？

使用深度限制和范围控制：
```yaml
crawl:
  depth: 1  # 限制爬取深度
scope:
  allow_paths:
    - "/articles/11g/"  # 只爬取特定路径
```

### Q: 如何处理重复内容？

使用重复文件检测：
```yaml
duplicate_threshold: 0.95  # 自动跳过 95%+ 相似度的文件
```

### Q: 如何提高下载速度？

增加并发数量（注意不要对服务器造成压力）：
```bash
python3 scripts/converter.py --config config.yaml --max-workers 8
```

### Q: 输出目录在哪里？

输出目录默认在项目根目录下，不是在 skills 目录中：
- 相对路径：相对于项目根目录
- 绝对路径：使用指定路径

## 技术细节

### 并发安全
使用 `threading.Lock` 保护共享资源，确保多线程环境下的数据一致性。

### 错误处理
- 自动重试失败的请求（最多 3 次）
- 记录失败的 URL 供后续处理
- 详细的错误日志输出

### 性能优化
- 线程池并发下载
- URL 去重减少重复请求
- 内容缓存用于相似度比较

## 许可证

本项目遵循项目根目录的许可证。

## 贡献

欢迎提交问题和改进建议！
