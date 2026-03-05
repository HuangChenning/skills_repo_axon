#!/usr/bin/env python3
"""
Browser Crawler - 浏览器渲染爬虫
使用 Playwright 处理 JavaScript 动态内容
"""

import os
import sys
import json
import logging
import argparse
from typing import Optional, List, Dict
from urllib.parse import urlparse
import asyncio
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrowserCrawler:
    """浏览器爬虫类"""

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport: Dict = None,
        slow_mo: int = 0,
        user_agent: str = None
    ):
        """
        初始化浏览器爬虫

        Args:
            browser_type: 浏览器类型（chromium/firefox/webkit）
            headless: 是否使用无头模式
            viewport: 视口大小 {"width": 1920, "height": 1080}
            slow_mo: 操作延迟（毫秒）
            user_agent: 自定义 User-Agent
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright 未安装，请运行: pip3 install playwright")

        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.slow_mo = slow_mo
        self.user_agent = user_agent

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 统计信息
        self.stats = {
            'pages_loaded': 0,
            'screenshots': 0,
            'pdfs': 0,
            'errors': 0
        }

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()

        launch_options = {
            'headless': self.headless,
            'slow_mo': self.slow_mo
        }

        # 根据浏览器类型启动
        if self.browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(**launch_options)
        elif self.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(**launch_options)
        elif self.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(**launch_options)
        else:
            raise ValueError(f"不支持的浏览器类型: {self.browser_type}")

        # 创建上下文
        context_options = {
            'viewport': self.viewport,
            'user_agent': self.user_agent,
            'java_script_enabled': True
        }

        self.context = await self.browser.new_context(**context_options)

        # 创建页面
        self.page = await self.context.new_page()

        logger.info(f"浏览器已启动: {self.browser_type} (headless={self.headless})")

    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("浏览器已关闭")

    async def navigate(
        self,
        url: str,
        wait_until: str = "networkidle",
        timeout: int = 30000
    ) -> bool:
        """
        导航到指定 URL

        Args:
            url: 目标 URL
            wait_until: 等待条件（load/domcontentloaded/networkidle）
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True
        """
        try:
            logger.info(f"正在加载: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            self.stats['pages_loaded'] += 1
            return True

        except Exception as e:
            logger.error(f"加载页面失败: {url}, 错误: {e}")
            self.stats['errors'] += 1
            return False

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 30000
    ) -> bool:
        """
        等待选择器出现

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True
        """
        try:
            logger.info(f"等待选择器: {selector}")
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True

        except Exception as e:
            logger.error(f"等待选择器超时: {selector}, 错误: {e}")
            return False

    async def wait(self, milliseconds: int):
        """等待指定时间"""
        await self.page.wait_for_timeout(milliseconds)

    async def execute_script(self, script: str) -> any:
        """
        执行 JavaScript 代码

        Args:
            script: JavaScript 代码

        Returns:
            执行结果
        """
        try:
            result = await self.page.evaluate(script)
            logger.info(f"脚本执行成功: {script[:50]}...")
            return result

        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            return None

    async def scroll_page(
        self,
        times: int = 5,
        interval: int = 1000
    ):
        """
        自动滚动页面

        Args:
            times: 滚动次数
            interval: 每次滚动间隔（毫秒）
        """
        logger.info(f"开始滚动页面（{times} 次）")

        for i in range(times):
            # 滚动到页面底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.wait(interval)

            # 检查是否还有新内容加载
            current_height = await self.page.evaluate("document.body.scrollHeight")
            logger.info(f"滚动 {i + 1}/{times}, 当前高度: {current_height}")

    async def screenshot(
        self,
        path: str,
        full_page: bool = False
    ) -> bool:
        """
        保存页面截图

        Args:
            path: 保存路径
            full_page: 是否截取整个页面

        Returns:
            成功返回 True
        """
        try:
            await self.page.screenshot(path=path, full_page=full_page)
            self.stats['screenshots'] += 1
            logger.info(f"截图已保存: {path}")
            return True

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

    async def save_pdf(self, path: str) -> bool:
        """
        保存页面为 PDF

        Args:
            path: 保存路径

        Returns:
            成功返回 True
        """
        try:
            await self.page.pdf(path=path)
            self.stats['pdfs'] += 1
            logger.info(f"PDF 已保存: {path}")
            return True

        except Exception as e:
            logger.error(f"保存 PDF 失败: {e}")
            return False

    async def get_html(self) -> str:
        """获取页面 HTML"""
        return await self.page.content()

    async def get_text(self) -> str:
        """获取页面文本内容"""
        return await self.page.inner_text("body")

    async def extract_data(
        self,
        selectors: Dict[str, str]
    ) -> Dict[str, any]:
        """
        提取页面数据

        Args:
            selectors: 选择器字典 {"name": "selector"}

        Returns:
            提取的数据字典
        """
        data = {}

        for name, selector in selectors.items():
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    if len(elements) == 1:
                        data[name] = await elements[0].inner_text()
                    else:
                        data[name] = [
                            await el.inner_text() for el in elements
                        ]
            except Exception as e:
                logger.warning(f"提取 {name} 失败: {e}")
                data[name] = None

        return data

    async def crawl(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        wait_time: int = 0,
        scroll: bool = False,
        scroll_times: int = 5,
        script: Optional[str] = None,
        screenshot: Optional[str] = None,
        pdf: Optional[str] = None,
        output: Optional[str] = None
    ) -> Optional[str]:
        """
        执行完整的爬取流程

        Args:
            url: 目标 URL
            wait_selector: 等待的选择器
            wait_time: 等待时间（毫秒）
            scroll: 是否滚动页面
            scroll_times: 滚动次数
            script: 要执行的脚本
            screenshot: 截图保存路径
            pdf: PDF 保存路径
            output: HTML 保存路径

        Returns:
            页面 HTML 内容
        """
        # 导航到页面
        if not await self.navigate(url):
            return None

        # 等待选择器
        if wait_selector:
            if not await self.wait_for_selector(wait_selector):
                logger.warning("选择器等待超时")

        # 等待指定时间
        if wait_time > 0:
            await self.wait(wait_time)

        # 执行脚本
        if script:
            await self.execute_script(script)

        # 滚动页面
        if scroll:
            await self.scroll_page(times=scroll_times)

        # 保存截图
        if screenshot:
            await self.screenshot(screenshot)

        # 保存 PDF
        if pdf:
            await self.save_pdf(pdf)

        # 获取 HTML
        html = await self.get_html()

        # 保存 HTML
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML 已保存: {output}")

        return html

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("爬虫统计")
        print("=" * 50)
        print(f"加载页面: {self.stats['pages_loaded']}")
        print(f"截图数量: {self.stats['screenshots']}")
        print(f"PDF 数量: {self.stats['pdfs']}")
        print(f"错误次数: {self.stats['errors']}")
        print("=" * 50)


async def crawl_single(args):
    """爬取单个页面"""
    crawler = BrowserCrawler(
        browser_type=args.browser,
        headless=args.headless,
        viewport={"width": args.viewport[0], "height": args.viewport[1]} if args.viewport else None,
        slow_mo=args.slow_mo
    )

    await crawler.start()

    try:
        html = await crawler.crawl(
            url=args.url,
            wait_selector=args.wait_selector,
            wait_time=args.wait,
            scroll=args.scroll,
            scroll_times=args.scroll_times,
            script=args.script,
            screenshot=args.screenshot,
            pdf=args.pdf,
            output=args.output
        )

        if html:
            print(f"\n✓ 成功抓取: {args.url}")
            print(f"  HTML 大小: {len(html)} 字节")
            crawler.print_stats()

    finally:
        await crawler.close()


async def crawl_batch(args):
    """批量爬取"""
    # 读取 URL 列表
    with open(args.batch, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    logger.info(f"开始批量抓取 {len(urls)} 个页面")

    results = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 处理: {url}")

        crawler = BrowserCrawler(
            browser_type=args.browser,
            headless=args.headless,
            slow_mo=args.slow_mo
        )

        await crawler.start()

        try:
            output_file = None
            if args.output_dir:
                filename = f"page_{i}.html"
                output_file = os.path.join(args.output_dir, filename)

            html = await crawler.crawl(
                url=url,
                wait_selector=args.wait_selector,
                wait_time=args.wait,
                scroll=args.scroll,
                output=output_file
            )

            if html:
                results.append({'url': url, 'html': html})
                print(f"✓ 成功: {url}")

        except Exception as e:
            logger.error(f"处理失败: {url}, 错误: {e}")

        finally:
            await crawler.close()

    print(f"\n批量抓取完成: {len(results)}/{len(urls)} 成功")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Browser Crawler - 浏览器渲染爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  %(prog)s https://example.com

  # 等待元素加载
  %(prog)s https://example.com --wait-selector ".content"

  # 保存截图
  %(prog)s https://example.com --screenshot screenshot.png

  # 自动滚动
  %(prog)s https://example.com --scroll --scroll-times 10

  # 导出 PDF
  %(prog)s https://example.com --pdf page.pdf

  # 执行脚本
  %(prog)s https://example.com --script "window.scrollTo(0,1000)"

  # 批量处理
  %(prog)s --batch urls.txt --output-dir ./output
        """
    )

    parser.add_argument("url", nargs='?', help="目标网页 URL")
    parser.add_argument("-b", "--batch", metavar="FILE", help="批量处理 URL 文件")
    parser.add_argument("-w", "--wait", type=int, default=0, help="等待时间（毫秒）")
    parser.add_argument("--wait-selector", help="等待特定选择器")
    parser.add_argument("--screenshot", help="保存截图路径")
    parser.add_argument("--pdf", help="保存 PDF 路径")
    parser.add_argument("-o", "--output", help="输出 HTML 文件路径")
    parser.add_argument("--output-dir", help="批量处理输出目录")
    parser.add_argument("--script", help="执行 JavaScript 代码")
    parser.add_argument("--scroll", action="store_true", help="启用自动滚动")
    parser.add_argument("--scroll-times", type=int, default=5, help="滚动次数")
    parser.add_argument("--viewport", nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                        default=[1920, 1080], help="视口大小")
    parser.add_argument("--browser", choices=['chromium', 'firefox', 'webkit'],
                        default="chromium", help="浏览器类型")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="使用无头模式（默认）")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="显示浏览器窗口")
    parser.add_argument("--slow-mo", type=int, default=0, help="操作延迟（毫秒）")

    args = parser.parse_args()

    # 检查参数
    if not args.url and not args.batch:
        parser.error("必须提供 URL 或使用 --batch 参数")

    # 运行爬虫
    if args.batch:
        asyncio.run(crawl_batch(args))
    else:
        asyncio.run(crawl_single(args))


if __name__ == "__main__":
    main()
