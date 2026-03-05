#!/usr/bin/env python3
"""
爬取引擎模块
支持深度控制和链接跟随
"""

import logging
from typing import List, Set, Optional, Deque, Tuple
from urllib.parse import urljoin, urlparse
from collections import deque
import time

import requests
from bs4 import BeautifulSoup

try:
    from .scope import ScopeMatcher
except ImportError:
    from scope import ScopeMatcher

logger = logging.getLogger(__name__)


class WebCrawler:
    """网页爬取引擎（带深度控制）"""

    def __init__(
        self,
        max_depth: int = 1,
        scope_matcher: Optional[ScopeMatcher] = None,
        same_domain_only: bool = True,
        timeout: int = 10,
        delay: float = 0.5,
        user_agent: str = None
    ):
        """
        初始化爬虫

        Args:
            max_depth: 最大爬取深度（0 表示只爬取起始页面）
            scope_matcher: URL 范围匹配器
            same_domain_only: 是否只爬取同域名下的链接
            timeout: 请求超时时间（秒）
            delay: 请求间隔时间（秒）
            user_agent: 用户代理字符串
        """
        self.max_depth = max_depth
        self.scope_matcher = scope_matcher
        self.same_domain_only = same_domain_only
        self.timeout = timeout
        self.delay = delay

        # 设置 User-Agent
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # 起始域名（用于同域名检查）
        self.start_domain = None

        logger.info(f"初始化爬虫: 深度={max_depth}, 同域名={same_domain_only}")

    def crawl(self, start_url: str) -> List[str]:
        """
        从起始 URL 开始爬取，返回所有发现的 URL

        Args:
            start_url: 起始 URL

        Returns:
            发现的所有 URL 列表（按发现顺序）
        """
        # 解析起始域名
        parsed = urlparse(start_url)
        self.start_domain = parsed.netloc

        # 初始化 BFS 队列:(url, depth)
        queue: Deque[Tuple[str, int]] = deque()
        queue.append((start_url, 0))

        # 记录已访问的 URL
        visited: Set[str] = set()

        # 记录所有发现的 URL
        all_urls: List[str] = []

        logger.info(f"开始爬取: {start_url}")

        while queue:
            url, depth = queue.popleft()

            # 跳过已访问的 URL
            if url in visited:
                continue

            # 检查是否应该爬取
            if not self._should_crawl(url, depth):
                continue

            try:
                # 标记为已访问
                visited.add(url)
                all_urls.append(url)

                logger.info(f"[深度 {depth}] 爬取: {url}")

                # 如果达到最大深度，不再提取链接
                if depth >= self.max_depth:
                    logger.debug(f"达到最大深度 {self.max_depth}，停止提取链接")
                    continue

                # 获取页面内容
                try:
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                except Exception as e:
                    logger.warning(f"获取页面失败: {url}, 错误: {e}")
                    continue

                # 提取链接
                links = self.extract_links(response.text, url)
                logger.info(f"从 {url} 提取到 {len(links)} 个链接")

                # 添加到队列
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

                # 请求延迟
                if self.delay > 0 and queue:
                    time.sleep(self.delay)

            except Exception as e:
                logger.error(f"爬取 {url} 时出错: {e}")
                continue

        logger.info(f"爬取完成: 共发现 {len(all_urls)} 个 URL")
        return all_urls

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        从 HTML 提取所有链接

        Args:
            html: HTML 内容
            base_url: 基础 URL（用于解析相对链接）

        Returns:
            提取的绝对 URL 列表
        """
        soup = BeautifulSoup(html, 'lxml')
        links = set()

        # 查找所有 <a> 标签
        for tag in soup.find_all('a', href=True):
            href = tag['href'].strip()

            # 跳过空链接和锚点
            if not href or href.startswith('#'):
                continue

            # 转换为绝对 URL
            absolute_url = urljoin(base_url, href)

            # 移除 fragment
            absolute_url = absolute_url.split('#')[0]

            # 只处理 HTTP/HTTPS 链接
            parsed = urlparse(absolute_url)
            if parsed.scheme not in ['http', 'https']:
                continue

            # 标准化 URL（移除末尾的斜杠）
            if absolute_url.endswith('/'):
                absolute_url = absolute_url[:-1]

            links.add(absolute_url)

        return list(links)

    def _should_crawl(self, url: str, current_depth: int) -> bool:
        """
        判断是否应该爬取该 URL

        Args:
            url: 要检查的 URL
            current_depth: 当前深度

        Returns:
            True 如果应该爬取，False 否则
        """
        # 检查深度限制
        if current_depth > self.max_depth:
            logger.debug(f"超过最大深度: {url}")
            return False

        # 检查范围限制
        if self.scope_matcher and not self.scope_matcher.is_allowed(url):
            logger.debug(f"不在允许范围内: {url}")
            return False

        # 检查同域名限制
        if self.same_domain_only:
            parsed = urlparse(url)
            if parsed.netloc != self.start_domain:
                logger.debug(f"不同域名: {url}")
                return False

        return True

    def crawl_with_content(self, start_url: str) -> List[Tuple[str, str]]:
        """
        爬取并返回 URL 和内容的元组列表

        Args:
            start_url: 起始 URL

        Returns:
            (url, html_content) 元组列表
        """
        # 解析起始域名
        parsed = urlparse(start_url)
        self.start_domain = parsed.netloc

        # 初始化 BFS 队列
        queue: Deque[Tuple[str, int]] = deque()
        queue.append((start_url, 0))

        # 记录已访问的 URL
        visited: Set[str] = set()

        # 记录结果
        results: List[Tuple[str, str]] = []

        logger.info(f"开始爬取（带内容）: {start_url}")

        while queue:
            url, depth = queue.popleft()

            # 跳过已访问的 URL
            if url in visited:
                continue

            # 检查是否应该爬取
            if not self._should_crawl(url, depth):
                continue

            try:
                # 标记为已访问
                visited.add(url)

                # 获取页面内容
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                # 保存结果
                results.append((url, response.text))
                logger.info(f"[深度 {depth}] 爬取成功: {url} ({len(response.text)} 字节)")

                # 如果达到最大深度，不再提取链接
                if depth >= self.max_depth:
                    continue

                # 提取链接
                links = self.extract_links(response.text, url)

                # 添加到队列
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

                # 请求延迟
                if self.delay > 0 and queue:
                    time.sleep(self.delay)

            except Exception as e:
                logger.error(f"爬取 {url} 时出错: {e}")
                continue

        logger.info(f"爬取完成: 共获取 {len(results)} 个页面")
        return results


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 示例 1: 简单爬取（深度 0）
    print("=== 示例 1: 深度 0 ===")
    crawler1 = WebCrawler(max_depth=0)
    urls1 = crawler1.crawl('https://httpbin.org/html')
    print(f"发现 {len(urls1)} 个 URL")

    # 示例 2: 深度 1
    print("\n=== 示例 2: 深度 1 ===")
    crawler2 = WebCrawler(max_depth=1, delay=0)
    urls2 = crawler2.crawl('https://httpbin.org/html')
    print(f"发现 {len(urls2)} 个 URL")

    # 示例 3: 带范围限制
    print("\n=== 示例 3: 带范围限制 ===")
    try:
        from .scope import ScopeMatcher
    except ImportError:
        from scope import ScopeMatcher

    scope = ScopeMatcher(allow_domains=['httpbin.org'])
    crawler3 = WebCrawler(max_depth=1, scope_matcher=scope, delay=0)
    urls3 = crawler3.crawl('https://httpbin.org/html')
    print(f"发现 {len(urls3)} 个 URL")
    for url in urls3:
        print(f"  - {url}")
