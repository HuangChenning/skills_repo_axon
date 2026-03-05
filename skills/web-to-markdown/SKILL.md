---
name: web-to-markdown
description: 下载指定网页的内容并转换为格式化的 Markdown 文件。当用户需要将网页转换为 Markdown 格式、批量下载网页内容、爬取网站文章时使用此技能。支持 URL 范围控制、深度爬取、相似度过滤、关键字黑名单等高级功能。用户提到"下载网页"、"转换为 Markdown"、"爬取文章"、"批量下载"等关键词时应触发此技能。
---

# 网页转 Markdown 技能

## 概述

此技能用于下载网页内容并将其转换为格式化的 Markdown 文件。支持单个 URL 转换、批量处理、深度爬取等高级功能。

## 目录结构

```
web-to-markdown/
├── SKILL.md              # 技能说明文件
├── scripts/              # 核心代码
│   ├── converter.py      # 主转换器
│   ├── crawler.py        # 深度爬取模块
│   ├── filters.py        # URL 过滤模块
│   ├── scope.py          # URL 范围控制模块
│   └── requirements.txt   # Python 依赖
├── assets/               # 配置文件示例
│   ├── config.example.yaml
│   ├── config.python_docs.yaml
│   ├── config.oracle_articles.yaml
│   └── config.deep_crawl.yaml
└── evals/                # 测试用例
    └── evals.json
```

## 使用方式

### 方式 1：命令行参数

```bash
# 进入技能目录
cd /path/to/.claude/skills/web-to-markdown

# 转换单个网页
python3 scripts/converter.py https://example.com/article

# 指定输出目录（输出将在项目根目录下）
python3 scripts/converter.py https://example.com/article --output-dir my_markdown

# 使用关键词过滤
python3 scripts/converter.py https://example.com/article --keywords "Python教程"

# 自定义文件名
python3 scripts/converter.py https://example.com/article --filename my_article

# 批量处理
python3 scripts/converter.py --batch urls.txt

# 深度爬取
python3 scripts/converter.py https://example.com --depth 1 --same-domain

# URL 范围控制
python3 scripts/converter.py --batch urls.txt --allow-domains example.com --deny-paths /admin/
```

### 方式 2：YAML 配置文件（推荐）

```bash
# 使用配置文件
python3 converter.py --config config.yaml

# 配置文件 + 命令行覆盖
python3 converter.py --config config.yaml --max-workers 8
```

## 配置文件说明

### 完整配置示例

```yaml
# ============================================
# 基础设置
# ============================================

# 输出目录
output_dir: "markdown_output"

# 请求超时时间（秒）
timeout: 30

# 并发下载数量
max_workers: 4

# 最大重试次数
max_retries: 3

# 搜索关键词（逗号分隔）
keywords: ""

# 自定义 User-Agent
# user_agent: "Mozilla/5.0 ..."

# ============================================
# URL 来源（三选一）
# ============================================

# 单个 URL
url: "https://example.com"

# 从文件批量读取
# batch: "urls.txt"

# 从 sitemap 获取
# sitemap: "https://example.com/sitemap.xml"

# ============================================
# URL 范围控制
# ============================================

scope:
  # 域名白名单
  allow_domains:
    - "docs.python.org"
    - "github.com"

  # 域名黑名单
  deny_domains:
    - "ads.example.com"

  # 路径白名单
  allow_paths:
    - "/docs/"
    - "/guides/"

  # 路径黑名单
  deny_paths:
    - "/api/"
    - "/admin/"

  # 正则表达式
  # allow_regex: "https://docs\\.python\\.org/3/.*tutorial.*"
  # deny_regex: ".*(deprecated|archived).*"

# ============================================
# 深度爬取设置
# ============================================

crawl:
  # 爬取深度（0 = 只爬起始页）
  depth: 1

  # 只爬取同域名
  same_domain: true

  # 请求间隔（秒）
  delay: 0.5

# ============================================
# URL 过滤设置
# ============================================

filter:
  # 启用相似度过滤
  enable_similar: false

  # 相似度阈值（0-1）
  similarity_threshold: 0.95

  # 禁用跟踪参数移除
  disable_tracking: false

# ============================================
# 内容提取设置
# ============================================

extraction:
  # 主要内容选择器
  content_selector: ""

  # 移除的元素
  remove_selectors:
    - "nav"
    - "header"
    - ".advertisement"

# ============================================
# 日志设置
# ============================================

logging:
  # 日志级别
  level: "INFO"
```

### 预设配置文件

#### 1. Python 文档爬取

```bash
python3 converter.py --config config.python_docs.yaml
```

**config.python_docs.yaml**：
```yaml
output_dir: "python_docs"
max_workers: 6

url: "https://docs.python.org/3/tutorial/"

scope:
  allow_domains: ["docs.python.org"]
  deny_paths: ["/3/api/", "/3/reference/"]

crawl:
  depth: 1
  delay: 1

filter:
  enable_similar: true
```

#### 2. Oracle 文章批量爬取

```bash
python3 converter.py --config config.oracle_articles.yaml
```

**config.oracle_articles.yaml**：
```yaml
output_dir: "oracle_articles"
max_workers: 8
timeout: 45

batch: "oracle_urls.txt"

scope:
  allow_domains: ["oracle-base.com"]
  allow_paths: ["/articles/11g/"]

filter:
  enable_similar: true
```

#### 3. 深度爬取

```bash
python3 converter.py --config config.deep_crawl.yaml
```

**config.deep_crawl.yaml**：
```yaml
output_dir: "site_content"
max_workers: 4

url: "https://example.com/docs"

crawl:
  depth: 2
  delay: 1

scope:
  allow_domains: ["example.com"]
  allow_paths: ["/docs/"]
  deny_paths: ["/docs/api/", "/admin/"]

filter:
  enable_similar: true
  similarity_threshold: 0.90
```

## 参数说明

### 基础参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 网页 URL | - |
| `--output-dir` | 输出目录 | markdown_output |
| `--keywords` | 搜索关键词 | - |
| `--filename` | 自定义文件名 | - |
| `--timeout` | 超时时间（秒） | 30 |
| `--max-workers` | 并发数 | 4 |
| `--max-retries` | 重试次数 | 3 |
| `--batch` | 批量处理文件 | - |
| `--sitemap` | Sitemap URL | - |
| `--config` | 配置文件路径 | - |

### URL 范围控制

| 参数 | 说明 |
|------|------|
| `--allow-domains` | 域名白名单 |
| `--deny-domains` | 域名黑名单 |
| `--allow-paths` | 路径白名单 |
| `--deny-paths` | 路径黑名单 |
| `--allow-regex` | 允许正则 |
| `--deny-regex` | 拒绝正则 |

### 深度爬取

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--depth` | 爬取深度 | 0 |
| `--same-domain` | 同域名限制 | - |
| `--crawl-delay` | 请求间隔（秒） | 0.5 |

### URL 过滤

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--filter-similar` | 启用去重 | - |
| `--similarity-threshold` | 相似度阈值 | 0.95 |
| `--disable-filter-tracking` | 禁用跟踪参数移除 | - |

## 输出

- Markdown 格式的文件（.md）
- 保留文章标题、段落、列表、链接等结构
- 代码块使用适当的语言标记
- 自动添加元数据头部（标题、来源 URL）

## 依赖

```bash
pip3 install -r requirements.txt
```

主要依赖：
- requests
- beautifulsoup4
- lxml
- markdownify
- pyyaml
- tqdm
