---
name: browser-crawler
description: 浏览器渲染爬虫技能，使用真实浏览器抓取 JavaScript 动态内容。支持等待元素加载、执行 JavaScript、截图等功能。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash
---

# Browser Crawler - 浏览器渲染爬虫技能

## 功能概述

Browser Crawler 使用真实浏览器引擎（如 Playwright 或 Selenium）抓取网页，特别适合处理 JavaScript 动态渲染的内容。

## 核心功能

- **JavaScript 执行**: 完整执行页面 JavaScript
- **动态内容加载**: 等待 AJAX/异步内容加载完成
- **元素等待**: 智能等待特定元素出现
- **页面截图**: 保存页面截图
- **PDF 导出**: 将页面保存为 PDF
- **交互操作**: 支持点击、滚动、填表等操作
- **无头模式**: 支持无界面运行
- **多浏览器**: 支持 Chrome、Firefox、Safari

## 使用场景

- 单页应用（SPA/React/Vue/Angular）
- 无限滚动页面（社交媒体、电商）
- 需要登录的页面
- 动态加载的内容
- 复杂交互的页面
- 需要截图的场景

## 快速开始

### 1. 基本使用

```bash
# 抓取动态页面
python3 browser_crawler.py <URL>

# 等待特定元素
python3 browser_crawler.py <URL> --wait-selector ".data-loaded"

# 保存截图
python3 browser_crawler.py <URL> --screenshot screenshot.png

# 导出 PDF
python3 browser_crawler.py <URL> --pdf page.pdf
```

### 2. 高级功能

```bash
# 执行自定义 JavaScript
python3 browser_crawler.py <URL> --script "window.scrollTo(0,document.body.scrollHeight)"

# 模拟滚动加载
python3 browser_crawler.py <URL> --scroll --scroll-times 5

# 设置视口大小
python3 browser_crawler.py <URL> --viewport 1920,1080

# 使用慢速网络模拟
python3 browser_crawler.py <URL> --slow-mo 1000
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `url` | 目标网页 URL |
| `-w, --wait` | 等待时间（毫秒） |
| `--wait-selector` | 等待特定选择器出现 |
| `--screenshot` | 保存页面截图 |
| `--pdf` | 导出为 PDF |
| `--script` | 执行 JavaScript 代码 |
| `--scroll` | 启用自动滚动 |
| `--scroll-times` | 滚动次数 |
| `--viewport` | 视口大小（宽x高） |
| `--browser` | 浏览器类型（chromium/firefox/webkit） |
| `--headless` | 无头模式（默认开启） |
| `--slow-mo` | 操作延迟（毫秒） |
| `--output` | 输出文件路径 |

## 配置文件

创建 `browser_config.yaml`:

```yaml
# 浏览器设置
browser:
  type: chromium  # chromium, firefox, webkit
  headless: true
  slow_mo: 0

# 视口设置
viewport:
  width: 1920
  height: 1080

# 等待设置
wait:
  timeout: 30000  # 毫秒
  selector: null  # 等待的选择器

# 滚动设置
scroll:
  enabled: false
  times: 5
  interval: 1000

# 输出设置
output:
  screenshot: null
  pdf: null
  html: true
```

使用配置文件：

```bash
python3 browser_crawler.py <URL> --config browser_config.yaml
```

## 使用示例

### 示例 1: 抓取 SPA 应用

```bash
python3 browser_crawler.py https://react.example.com \
  --wait-selector ".app-loaded" \
  --output app.html
```

### 示例 2: 无限滚动页面

```bash
python3 browser_crawler.py https://social.example.com/feed \
  --scroll \
  --scroll-times 10 \
  --wait 2000
```

### 示例 3: 页面截图

```bash
python3 browser_crawler.py https://example.com \
  --screenshot screenshot.png \
  --viewport 1920,1080 \
  --wait 3000
```

### 示例 4: 批量处理

创建 `urls.txt`:

```
https://site1.com
https://site2.com
https://site3.com
```

运行：

```bash
python3 browser_crawler.py --batch urls.txt --output-dir screenshots/
```

## 高级功能

### 1. JavaScript 注入

```bash
python3 browser_crawler.py <URL> \
  --script "document.querySelector('.banner').remove()"
```

### 2. Cookie 处理

```python
# 在脚本中使用
context.add_cookies([
    {
        'name': 'session',
        'value': 'abc123',
        'domain': '.example.com',
        'path': '/'
    }
])
```

### 3. 代理设置

```bash
python3 browser_crawler.py <URL> --proxy http://proxy.example.com:8080
```

### 4. 用户数据持久化

```bash
# 保存浏览器状态
python3 browser_crawler.py <URL> --user-data-dir ./browser_data
```

### 5. 网络拦截

```python
# 拦截请求
async def handle_route(route):
    if "ads" in route.request.url:
        await route.abort()
    else:
        await route.continue_()
```

## 性能优化

### 并发抓取

```bash
# 使用多个浏览器实例
python3 browser_crawler.py --batch urls.txt --max-workers 3
```

### 资源节省

```bash
# 禁用图片加载
python3 browser_crawler.py <URL> --no-images

# 禁用 CSS
python3 browser_crawler.py <URL> --no-css
```

## 依赖安装

### 使用 Playwright（推荐）

```bash
# 安装 Python 包
pip3 install playwright

# 安装浏览器
playwright install chromium
```

### 使用 Selenium

```bash
pip3 install selenium selenium-wire

# 需要手动安装 ChromeDriver
```

## 对比：Playwright vs Selenium

| 特性 | Playwright | Selenium |
|------|-----------|----------|
| 速度 | 更快 | 较慢 |
| 稳定性 | 更高 | 较低 |
| API | 现代 | 传统 |
| 文档 | 优秀 | 一般 |
| 多浏览器 | 原生支持 | 需要额外驱动 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 常见问题

### Q: 如何处理弹窗？
```bash
python3 browser_crawler.py <URL> --auto-close-modals
```

### Q: 如何下载文件？
```python
# 设置下载路径
page.context.set_default_download_path('./downloads')
```

### Q: 如何调试？
```bash
# 使用 headed 模式
python3 browser_crawler.py <URL> --no-headless

# 或使用调试模式
python3 browser_crawler.py <URL> --debug
```

## 注意事项

- 浏览器占用资源较多，注意内存使用
- 建议在服务器上使用无头模式
- 某些网站可能检测并阻止自动化
- 遵守网站的 robots.txt 和使用条款
