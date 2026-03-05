---
name: web-scraper
description: 通用网页数据抓取技能，支持从网页提取结构化数据。使用 CSS 选择器和 XPath 提取数据，支持导出 JSON/CSV 格式。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash
---

# Web Scraper - 网页数据抓取技能

## 功能概述

Web Scraper 是一个通用的网页数据抓取工具，可以从网页中提取结构化数据并导出为多种格式。

## 核心功能

- **CSS 选择器提取**: 使用 CSS 选择器定位元素
- **XPath 支持**: 使用 XPath 表达式提取复杂结构
- **数据清洗**: 自动清理和格式化提取的数据
- **多格式导出**: 支持 JSON、CSV、Excel 格式
- **批量处理**: 支持从多个页面提取数据
- **配置文件**: 使用 YAML 配置文件定义提取规则

## 使用场景

- 商品信息抓取（价格、标题、图片）
- 文章列表提取（标题、链接、摘要）
- 联系方式收集（邮箱、电话、地址）
- 数据统计和分析（表格数据）
- API 替代方案（无需 API 密钥）

## 快速开始

### 1. 使用命令行工具

```bash
# 提取单个页面的数据
python3 scraper.py <URL> --selector ".product-title"

# 使用配置文件
python3 scraper.py <URL> --config config.yaml

# 批量处理
python3 scraper.py --batch urls.txt --config config.yaml

# 导出为 JSON
python3 scraper.py <URL> --selector ".title" --output results.json

# 导出为 CSV
python3 scraper.py <URL> --selector ".price" --format csv --output prices.csv
```

### 2. 使用配置文件

创建 `config.yaml`:

```yaml
# 提取规则
fields:
  - name: title
    selector: "h1.product-title"
    type: text

  - name: price
    selector: ".price-current"
    type: text
    regex: "\\$([0-9.]+)"

  - name: rating
    selector: ".rating"
    attribute: data-rating
    type: float

  - name: image_url
    selector: ".product-image img"
    attribute: src
    type: url

# 分页设置
pagination:
  next_selector: "a.next-page"
  max_pages: 10

# 输出设置
output:
  format: json
  filename: products
```

然后运行：

```bash
python3 scraper.py https://example.com/products --config config.yaml
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `url` | 目标网页 URL |
| `-s, --selector` | CSS 选择器或 XPath |
| `-c, --config` | 配置文件路径 |
| `-b, --batch` | 批量处理 URL 文件 |
| `-f, --format` | 输出格式 (json/csv/excel) |
| `-o, --output` | 输出文件路径 |
| `--attribute` | 提取属性而非文本 |
| `--regex` | 使用正则表达式过滤 |
| `--delay` | 请求间隔（秒） |
| `--max-pages` | 最大抓取页数 |
| `--header` | 自定义请求头 |

## 数据类型

- `text`: 纯文本内容
- `number`: 数字（自动转换）
- `float`: 浮点数
- `url`: URL 链接
- `image`: 图片 URL
- `email`: 邮箱地址
- `date`: 日期时间
- `html`: HTML 内容

## 示例

### 示例 1: 提取文章标题

```bash
python3 scraper.py https://blog.example.com \
  --selector "h2.post-title" \
  --format json \
  --output titles.json
```

### 示例 2: 提取商品价格

```bash
python3 scraper.py https://shop.example.com/product/123 \
  --selector ".price" \
  --regex "\\$([0-9.]+)" \
  --format csv \
  --output prices.csv
```

### 示例 3: 批量提取

创建 `urls.txt`:
```
https://site1.com
https://site2.com
https://site3.com
```

运行：

```bash
python3 scraper.py --batch urls.txt --selector "h1" --output results.json
```

## 高级功能

### 1. 多字段提取

```bash
python3 scraper.py <URL> \
  --fields title=".title",price=".price",url="a@href" \
  --format json
```

### 2. 嵌套数据提取

```yaml
fields:
  - name: products
    selector: ".product-item"
    list: true
    fields:
      - name: name
        selector: ".name"
      - name: price
        selector: ".price"
```

### 3. 动态内容处理

```bash
# 等待 JavaScript 加载
python3 scraper.py <URL> --wait-selector ".data-loaded" --delay 2
```

### 4. 认证支持

```bash
# 使用 Cookie
python3 scraper.py <URL> --cookie "session=abc123"

# 使用 Basic Auth
python3 scraper.py <URL> --auth "user:password"
```

## 错误处理

- 自动重试失败的请求
- 跳过无效的选择器
- 记录详细的错误日志
- 验证提取的数据格式

## 依赖安装

```bash
pip3 install -r requirements.txt
```

主要依赖：
- requests
- beautifulsoup4
- lxml
 pyyaml
 pandas
