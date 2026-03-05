#!/usr/bin/env python3
"""
网页转 Markdown 转换器 (优化版)
下载网页内容并转换为 Markdown 格式

新特性:
- 并发下载支持
- 请求重试机制
- 改进的内容提取
- 支持 sitemap 自动发现
- 更好的错误处理
- URL 范围控制（白名单/黑名单）
- 深度爬取和链接跟随
- URL 去重和相似度过滤
- 跟踪参数自动移除
"""

import os
import re
import sys
import time
import copy
import logging
import argparse
from typing import Optional, List, Set, Dict
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import requests
from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md
from tqdm import tqdm

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# 导入新模块
# 导入新模块
try:
    # 作为包导入时
    from .scope import ScopeMatcher, create_scope_matcher_from_config
    from .crawler import WebCrawler
    from .filters import URLFilter
except ImportError:
    # 直接运行时
    from scope import ScopeMatcher, create_scope_matcher_from_config
    from crawler import WebCrawler
    from filters import URLFilter


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_project_root():
    """
    查找项目根目录

    从当前脚本位置向上查找，找到包含以下任一特征的目录：
    - .git 目录
    - .claude 目录
    - src 目录
    - pyproject.toml 或 setup.py 或 requirements.txt

    Returns:
        项目根目录的绝对路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 向上查找最多5级
    for _ in range(5):
        parent_dir = os.path.dirname(current_dir)

        # 检查是否找到项目根目录特征
        markers = [
            os.path.exists(os.path.join(parent_dir, '.git')),
            os.path.exists(os.path.join(parent_dir, '.claude')),
            os.path.exists(os.path.join(parent_dir, 'src')),
            os.path.exists(os.path.join(parent_dir, 'pyproject.toml')),
            os.path.exists(os.path.join(parent_dir, 'setup.py')),
            os.path.exists(os.path.join(parent_dir, 'requirements.txt'))
        ]

        if any(markers):
            return parent_dir

        current_dir = parent_dir

    # 如果找不到，返回当前工作目录
    return os.getcwd()


# 获取项目根目录
PROJECT_ROOT = find_project_root()


class WebToMarkdown:
    """网页转 Markdown 转换器类（优化版）"""

    def __init__(
        self,
        output_dir: str = "markdown_output",
        timeout: int = 30,
        max_workers: int = 4,
        max_retries: int = 3,
        retry_delay: int = 2,
        user_agent: str = None,
        scope_matcher: Optional[ScopeMatcher] = None,
        url_filter: Optional[URLFilter] = None,
        keyword_blacklist: Optional[List[str]] = None,
        enable_stats: bool = False,
        duplicate_threshold: float = 0.0
    ):
        """
        初始化转换器

        Args:
            output_dir: 输出目录路径
            timeout: 请求超时时间（秒）
            max_workers: 并发下载数量
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            user_agent: 自定义 User-Agent
            scope_matcher: URL 范围匹配器
            url_filter: URL 过滤器
            keyword_blacklist: 关键字黑名单（过滤包含这些关键字的文章）
            enable_stats: 是否启用统计功能
            duplicate_threshold: 文件内容查重阈值（0.0-1.0），超过此阈值则视为重复文件，0表示禁用
        """
        self.output_dir = output_dir
        self.timeout = timeout
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.scope_matcher = scope_matcher
        self.url_filter = url_filter
        self.keyword_blacklist = keyword_blacklist or []
        self.enable_stats = enable_stats
        self.duplicate_threshold = duplicate_threshold

        # 文件内容缓存（用于重复检测）
        self.file_contents: Dict[str, str] = {}  # filepath -> content
        # 线程锁，保护 file_contents 的并发访问
        self._lock = threading.Lock()

        # 计算输出目录的绝对路径（相对于项目根目录）
        if os.path.isabs(self.output_dir):
            self.output_dir = self.output_dir
        else:
            self.output_dir = os.path.join(PROJECT_ROOT, self.output_dir)

        # 统计跟踪
        self.stats = {
            'total_found': 0,          # 发现的总 URL 数
            'scope_filtered': 0,       # 范围过滤数
            'similar_filtered': 0,     # 相似度过滤数
            'keyword_filtered': 0,     # 关键字过滤数
            'downloaded': 0,           # 成功下载数
            'failed': 0,               # 失败数
        }
        self.all_discovered_urls = []      # 所有发现的 URL
        self.scope_filtered_urls = []      # 被范围过滤的 URL
        self.similar_filtered_urls = []    # 被相似度过滤的 URL
        self.keyword_filtered_urls = []    # 被关键字过滤的 URL
        self.downloaded_urls = []          # 成功下载的 URL
        self.failed_urls = []              # 下载失败的 URL

        # 配置请求头
        self.headers = {
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 记录已下载的文件
        self.downloaded_files: Set[str] = set()

    def fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        """
        带重试的请求

        Args:
            url: 请求 URL

        Returns:
            Response 对象，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求失败 {url}，{self.retry_delay}秒后重试... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"请求失败 {url}: {e}")
        return None

    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        提取网页主要内容（改进版）

        Args:
            soup: BeautifulSoup 对象

        Returns:
            包含主要内容的 BeautifulSoup 对象
        """
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'iframe', 'noscript', 'form', 'svg']):
            tag.decompose()

        # 移除注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 移除常见的广告和导航元素（扩展列表）
        for elem in soup.find_all(class_=re.compile(
            r'(ad|advertisement|banner|sidebar|navigation|menu|social|share|footer|'
            r'cookie|popup|modal|related|recommended|comments|subscribe)',
            re.I
        )):
            elem.decompose()

        # 移除带有特定 id 的元素
        for elem in soup.find_all(id=re.compile(
            r'(ad|advertisement|banner|sidebar|navigation|menu|social|share|footer|'
            r'cookie|popup|modal|related|recommended|comments|subscribe)',
            re.I
        )):
            elem.decompose()

        # 尝试多种方式找到主要内容区域
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', id=re.compile(r'(content|main|article)', re.I)) or
            soup.find('div', class_=re.compile(r'(content|main|article|post)', re.I)) or
            soup.find('div', role='main')
        )

        if main_content:
            return BeautifulSoup(str(main_content), 'lxml')

        # 如果没找到，返回整个 body
        body = soup.find('body')
        if body:
            return BeautifulSoup(str(body), 'lxml')

        return soup

    def filter_by_keywords(self, soup: BeautifulSoup, keywords: str) -> BeautifulSoup:
        """
        根据关键词过滤内容

        Args:
            soup: BeautifulSoup 对象
            keywords: 关键词（逗号分隔）

        Returns:
            过滤后的 BeautifulSoup 对象
        """
        if not keywords:
            return soup

        keyword_list = [k.strip().lower() for k in keywords.split(',')]
        filtered_soup = BeautifulSoup('<div></div>', 'lxml')
        container = filtered_soup.div

        # 保留匹配的段落和标题
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'code']):
            text = element.get_text().lower()
            if any(keyword in text for keyword in keyword_list):
                container.append(copy.copy(element))

        return filtered_soup

    def html_to_markdown(self, soup: BeautifulSoup, url: str) -> str:
        """
        将 HTML 转换为 Markdown（改进版）

        Args:
            soup: BeautifulSoup 对象
            url: 原始 URL

        Returns:
            Markdown 格式的文本
        """
        # 使用 markdownify 转换
        markdown_text = md(str(soup), heading_style="ATX")

        # 清理多余的空行
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        # 清理链接中的换行符
        markdown_text = re.sub(r'\[([^\]]+)\]\(\s*\n\s*', r'[\1](', markdown_text)
        markdown_text = re.sub(r'\)\s*\n\s*', ')', markdown_text)

        # 添加元数据
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else "未命名文档"

        # 获取描述
        description = ""
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta and desc_meta.get('content'):
            description = desc_meta['content']

        metadata = f"""---
title: {title_text}
source: {url}
"""
        if description:
            metadata += f"description: {description}\n"

        metadata += "---\n\n"

        return metadata + markdown_text.strip()

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        filename = re.sub(r'\s+', ' ', filename)  # 多个空格变一个
        filename = filename.strip('. ')
        if len(filename) > 200:
            filename = filename[:200]
        return filename if filename else 'unnamed'

    def generate_filename(self, url: str, custom_name: Optional[str] = None, soup: Optional[BeautifulSoup] = None) -> str:
        """
        生成输出文件名（改进版）

        Args:
            url: 网页 URL
            custom_name: 自定义文件名
            soup: BeautifulSoup 对象（用于提取标题）

        Returns:
            文件名（不含扩展名）
        """
        if custom_name:
            return self.sanitize_filename(custom_name)

        # 尝试从页面标题获取
        if soup:
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                if title_text:
                    return self.sanitize_filename(title_text)

        # 从 URL 提取文件名
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if path_parts:
            filename = path_parts[-1]
            # 移除扩展名
            filename = re.sub(r'\.(html?|php|aspx?|jsp)$', '', filename, flags=re.I)
            if filename:
                return self.sanitize_filename(filename)

        # 使用域名作为文件名
        domain = parsed.netloc.replace('www.', '')
        return self.sanitize_filename(domain)

    def save_markdown(self, content: str, filename: str) -> bool:
        """
        保存 Markdown 内容到文件（带重复检测）

        Args:
            content: Markdown 内容
            filename: 文件名（不含扩展名）

        Returns:
            成功返回 True，重复文件返回 True（但跳过保存）
        """
        filepath = os.path.join(self.output_dir, f"{filename}.md")

        # 检查内容是否重复（使用锁保护并发访问）
        if self.duplicate_threshold > 0:
            with self._lock:
                if self.file_contents:
                    for existing_path, existing_content in self.file_contents.items():
                        similarity = self._calculate_similarity(content, existing_content)
                        if similarity >= self.duplicate_threshold:
                            logger.info(f"[重复检测] 跳过重复文件: {filepath} (与 {os.path.basename(existing_path)} 相似度 {similarity:.2f})")
                            return True

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已保存: {filepath}")

            # 缓存文件内容用于重复检测（使用锁保护）
            with self._lock:
                self.file_contents[filepath] = content
            return True
        except Exception as e:
            logger.error(f"保存文件失败 {filepath}: {e}")
            return False

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        计算两个文本内容的相似度

        Args:
            content1: 文本内容1
            content2: 文本内容2

        Returns:
            相似度 (0.0 - 1.0)
        """
        from difflib import SequenceMatcher

        # 归一化文本（移除多余空白）
        norm1 = ' '.join(content1.split())
        norm2 = ' '.join(content2.split())

        # 计算相似度
        matcher = SequenceMatcher(None, norm1, norm2)
        ratio = matcher.ratio()

        return ratio

    def convert(
        self,
        url: str,
        keywords: Optional[str] = None,
        filename: Optional[str] = None
    ) -> bool:
        """
        转换单个网页

        Args:
            url: 网页 URL
            keywords: 关键词过滤
            filename: 自定义文件名

        Returns:
            成功返回 True
        """
        # 获取网页
        response = self.fetch_with_retry(url)
        if not response:
            return False

        # 解析 HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # 提取主要内容
        main_content = self.extract_main_content(soup)

        # 关键词过滤
        if keywords:
            main_content = self.filter_by_keywords(main_content, keywords)
            logger.info(f"已应用关键词过滤: {keywords}")

        # 转换为 Markdown
        markdown_text = self.html_to_markdown(main_content, url)

        # 生成文件名
        output_filename = self.generate_filename(url, filename, soup)

        # 处理重名
        original_name = output_filename
        counter = 1
        while output_filename in self.downloaded_files:
            output_filename = f"{original_name}_{counter}"
            counter += 1

        self.downloaded_files.add(output_filename)

        # 保存文件
        return self.save_markdown(markdown_text, output_filename)

    def convert_batch(
        self,
        urls: List[str],
        keywords: Optional[str] = None,
        show_progress: bool = True,
        apply_filter: bool = True
    ) -> dict:
        """
        批量转换网页（支持并发）

        Args:
            urls: URL 列表
            keywords: 关键词过滤
            show_progress: 是否显示进度
            apply_filter: 是否应用 URL 过滤器

        Returns:
            统计信息字典
        """
        # 记录所有发现的 URL（用于统计）
        if self.enable_stats:
            self.all_discovered_urls = urls.copy()
            self.stats['total_found'] = len(urls)

        # 应用关键字黑名单过滤
        if self.keyword_blacklist:
            original_count = len(urls)
            filtered_by_keywords = []
            for url in urls:
                # 检查 URL 是否包含黑名单关键字
                if any(keyword.lower() in url.lower() for keyword in self.keyword_blacklist):
                    filtered_by_keywords.append(url)
                    if self.enable_stats:
                        self.keyword_filtered_urls.append(url)

            urls = [url for url in urls if url not in filtered_by_keywords]
            keyword_filtered_count = original_count - len(urls)
            self.stats['keyword_filtered'] = keyword_filtered_count
            if show_progress and keyword_filtered_count > 0:
                logger.info(f"关键字黑名单过滤: 过滤 {keyword_filtered_count} 个包含黑名单关键字的 URL")
                if self.enable_stats:
                    logger.info(f"  黑名单关键字: {', '.join(self.keyword_blacklist)}")

        # 应用 URL 过滤器
        if apply_filter and self.url_filter:
            original_count = len(urls)
            urls, filtered_count = self.url_filter.add_batch(urls)
            if self.enable_stats:
                self.stats['similar_filtered'] = filtered_count
            if show_progress and filtered_count > 0:
                logger.info(f"URL 过滤: 原始 {original_count} 个，过滤 {filtered_count} 个，剩余 {len(urls)} 个")

        # 应用范围控制
        if self.scope_matcher:
            original_count = len(urls)
            allowed_urls = []
            filtered_urls = []
            for url in urls:
                if self.scope_matcher.is_allowed(url):
                    allowed_urls.append(url)
                else:
                    filtered_urls.append(url)
                    if self.enable_stats:
                        self.scope_filtered_urls.append(url)

            urls = allowed_urls
            scope_filtered = len(filtered_urls)
            self.stats['scope_filtered'] = scope_filtered
            if show_progress and scope_filtered > 0:
                logger.info(f"范围控制: 过滤 {scope_filtered} 个不在允许范围内的 URL")

        results = {
            "total": len(urls),
            "filtered": (filtered_count if apply_filter and self.url_filter else 0) + (scope_filtered if self.scope_matcher else 0),
            "success": 0,
            "failed": 0,
            "failed_urls": []
        }

        if show_progress:
            logger.info(f"开始批量转换 {len(urls)} 个网页...")

        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            futures = {}
            for url in urls:
                future = executor.submit(self.convert, url, keywords)
                futures[future] = url

            # 等待完成
            if show_progress:
                with tqdm(total=len(urls), desc="转换进度", unit="页") as pbar:
                    for future in as_completed(futures):
                        url = futures[future]
                        try:
                            if future.result():
                                results["success"] += 1
                            else:
                                results["failed"] += 1
                                results["failed_urls"].append(url)
                        except Exception as e:
                            logger.error(f"处理 {url} 时出错: {e}")
                            results["failed"] += 1
                            results["failed_urls"].append(url)
                        pbar.update(1)
            else:
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        if future.result():
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                            results["failed_urls"].append(url)
                    except Exception as e:
                        logger.error(f"处理 {url} 时出错: {e}")
                        results["failed"] += 1
                        results["failed_urls"].append(url)

        # 打印统计
        if show_progress:
            self.stats['downloaded'] = results['success']
            self.stats['failed'] = results['failed']

            # 记录成功和失败的 URL
            if self.enable_stats:
                for url in urls:
                    if url not in results['failed_urls']:
                        self.downloaded_urls.append(url)
                self.failed_urls = results['failed_urls']

            print("\n" + "=" * 50)
            print("批量转换完成！")
            print("=" * 50)
            print(f"总计: {results['total']} 个文件")
            print(f"成功: {results['success']} 个")
            print(f"失败: {results['failed']} 个")
            print(f"输出目录: {os.path.abspath(self.output_dir)}")

            # 如果启用统计，显示详细信息
            if self.enable_stats:
                print("\n" + "=" * 50)
                print("详细统计报告")
                print("=" * 50)
                print(f"发现的总 URL 数: {self.stats['total_found']}")
                print(f"  - 范围过滤: {self.stats['scope_filtered']} 个")
                print(f"  - 相似度过滤: {self.stats['similar_filtered']} 个")
                print(f"  - 关键字过滤: {self.stats['keyword_filtered']} 个")
                print(f"  - 成功下载: {self.stats['downloaded']} 个")
                print(f"  - 下载失败: {self.stats['failed']} 个")

                # 生成统计文件
                stats_file = os.path.join(self.output_dir, "_crawl_stats.txt")
                with open(stats_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("爬取统计报告\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"发现的总 URL 数: {self.stats['total_found']}\n")
                    f.write(f"  - 范围过滤: {self.stats['scope_filtered']} 个\n")
                    f.write(f"  - 相似度过滤: {self.stats['similar_filtered']} 个\n")
                    f.write(f"  - 关键字过滤: {self.stats['keyword_filtered']} 个\n")
                    f.write(f"  - 成功下载: {self.stats['downloaded']} 个\n")
                    f.write(f"  - 下载失败: {self.stats['failed']} 个\n\n")

                    if self.keyword_blacklist:
                        f.write(f"关键字黑名单: {', '.join(self.keyword_blacklist)}\n\n")

                    # 写入范围过滤的 URL
                    if self.scope_filtered_urls:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write(f"范围过滤的 URL ({len(self.scope_filtered_urls)} 个):\n")
                        f.write("=" * 60 + "\n")
                        for url in self.scope_filtered_urls:
                            f.write(f"  {url}\n")

                    # 写入相似度过滤的 URL
                    if self.similar_filtered_urls:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write(f"相似度过滤的 URL ({len(self.similar_filtered_urls)} 个):\n")
                        f.write("=" * 60 + "\n")
                        for url in self.similar_filtered_urls:
                            f.write(f"  {url}\n")

                    # 写入关键字过滤的 URL
                    if self.keyword_filtered_urls:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write(f"关键字过滤的 URL ({len(self.keyword_filtered_urls)} 个):\n")
                        f.write("=" * 60 + "\n")
                        for url in self.keyword_filtered_urls:
                            f.write(f"  {url}\n")

                    # 写入成功下载的 URL
                    if self.downloaded_urls:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write(f"成功下载的 URL ({len(self.downloaded_urls)} 个):\n")
                        f.write("=" * 60 + "\n")
                        for url in self.downloaded_urls:
                            f.write(f"  {url}\n")

                    # 写入下载失败的 URL
                    if self.failed_urls:
                        f.write("\n" + "=" * 60 + "\n")
                        f.write(f"下载失败的 URL ({len(self.failed_urls)} 个):\n")
                        f.write("=" * 60 + "\n")
                        for url in self.failed_urls:
                            f.write(f"  {url}\n")

                print(f"\n统计报告已保存到: {stats_file}")

            if results['failed_urls']:
                print("\n失败的 URL（前 10 个）:")
                for url in results['failed_urls'][:10]:
                    print(f"  - {url[:80]}")
                if len(results['failed_urls']) > 10:
                    print(f"  ... 还有 {len(results['failed_urls']) - 10} 个")

            print("=" * 50)

        return results


def extract_urls_from_sitemap(base_url: str, headers: dict) -> List[str]:
    """
    从 sitemap 提取 URL

    Args:
        base_url: 基础 URL
        headers: 请求头

    Returns:
        URL 列表
    """
    urls = []
    sitemap_urls = [
        urljoin(base_url, '/sitemap.xml'),
        urljoin(base_url, '/sitemap_index.xml'),
        urljoin(base_url, '/sitemap'),
    ]

    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                for loc in soup.find_all('loc'):
                    url = loc.get_text(strip=True)
                    # 过滤掉非内容页面
                    if not url.endswith('.xml') and not url.endswith('.pdf'):
                        urls.append(url)
                if urls:
                    logger.info(f"从 sitemap 找到 {len(urls)} 个 URL")
                    break
        except Exception as e:
            continue

    return urls


def read_urls_from_file(filepath: str) -> List[str]:
    """
    从文件读取 URL 列表

    Args:
        filepath: 文件路径

    Returns:
        URL 列表
    """
    urls = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        return urls
    except Exception as e:
        logger.error(f"读取文件失败 {filepath}: {e}")
        return []


def load_config(config_path: str) -> dict:
    """
    从 YAML 文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML 未安装，请运行: pip3 install pyyaml")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"已加载配置文件: {config_path}")
        return config or {}
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"配置文件解析失败: {e}")
        return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="网页转 Markdown 转换器 - 下载网页并转换为 Markdown 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换单个网页
  %(prog)s https://example.com/article

  # 指定输出目录
  %(prog)s https://example.com/article --output-dir my_markdown

  # 使用关键词过滤
  %(prog)s https://example.com/article --keywords "Python教程"

  # 自定义文件名
  %(prog)s https://example.com/article --filename my_article

  # 批量处理（从文件）
  %(prog)s --batch urls.txt

  # 批量处理（从 sitemap）
  %(prog)s --sitemap https://example.com

  # 使用更多并发
  %(prog)s --batch urls.txt --max-workers 8

  # URL 范围控制（只允许特定域名）
  %(prog)s https://example.com --allow-domains example.com,blog.example.com

  # URL 范围控制（排除特定路径）
  %(prog)s https://example.com --deny-paths /admin/,/api/

  # 深度爬取（爬取链接）
  %(prog)s https://example.com --depth 2 --same-domain

  # 组合使用
  %(prog)s https://docs.python.org --depth 1 --allow-domains docs.python.org --deny-paths /api/

  # URL 去重过滤
  %(prog)s --batch urls.txt --filter-similar

  # 去重 + 自定义相似度阈值
  %(prog)s --batch urls.txt --filter-similar --similarity-threshold 0.90

  # 使用 YAML 配置文件
  %(prog)s --config config.yaml

  # 配置文件 + 命令行参数覆盖
  %(prog)s --config config.yaml --max-workers 8
        """
    )

    parser.add_argument(
        "url",
        nargs='?',
        help="网页 URL（使用 --batch 或 --sitemap 时可选）"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default="markdown_output",
        help="输出目录路径（默认: markdown_output）"
    )

    parser.add_argument(
        "-k", "--keywords",
        help="搜索关键词，用于过滤内容（逗号分隔多个）"
    )

    parser.add_argument(
        "-f", "--filename",
        help="自定义输出文件名（不含 .md 扩展名）"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="请求超时时间（秒，默认: 30）"
    )

    parser.add_argument(
        "-w", "--max-workers",
        type=int,
        default=4,
        help="并发下载数量（默认: 4）"
    )

    parser.add_argument(
        "-r", "--max-retries",
        type=int,
        default=3,
        help="最大重试次数（默认: 3）"
    )

    parser.add_argument(
        "-c", "--config",
        metavar="FILE",
        help="YAML 配置文件路径（覆盖其他参数）"
    )

    parser.add_argument(
        "-b", "--batch",
        metavar="FILE",
        help="批量处理，从文件读取 URL 列表"
    )

    parser.add_argument(
        "--sitemap",
        metavar="URL",
        help="从 sitemap 获取 URL 列表"
    )

    # URL 范围控制参数
    scope_group = parser.add_argument_group('URL 范围控制')
    scope_group.add_argument(
        "--allow-domains",
        help="域名白名单（逗号分隔，只处理这些域名）"
    )
    scope_group.add_argument(
        "--deny-domains",
        help="域名黑名单（逗号分隔，不处理这些域名）"
    )
    scope_group.add_argument(
        "--allow-paths",
        help="路径白名单（逗号分隔，只处理这些路径前缀）"
    )
    scope_group.add_argument(
        "--deny-paths",
        help="路径黑名单（逗号分隔，不处理这些路径前缀）"
    )
    scope_group.add_argument(
        "--allow-regex",
        help="允许 URL 的正则表达式"
    )
    scope_group.add_argument(
        "--deny-regex",
        help="拒绝 URL 的正则表达式"
    )

    # 深度爬取参数
    crawl_group = parser.add_argument_group('深度爬取')
    crawl_group.add_argument(
        "--depth",
        type=int,
        default=0,
        help="爬取深度（0=只爬取起始页面，1=爬取起始页+直接链接，默认: 0）"
    )
    crawl_group.add_argument(
        "--same-domain",
        action="store_true",
        help="只爬取同域名下的链接"
    )
    crawl_group.add_argument(
        "--crawl-delay",
        type=float,
        default=0.5,
        help="爬取间隔时间（秒，默认: 0.5）"
    )

    # URL 过滤参数
    filter_group = parser.add_argument_group('URL 过滤')
    filter_group.add_argument(
        "--filter-similar",
        action="store_true",
        help="启用相似 URL 过滤（去重）"
    )
    filter_group.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.95,
        help="相似度阈值（0-1，默认: 0.95）"
    )
    filter_group.add_argument(
        "--disable-filter-tracking",
        action="store_true",
        help="禁用跟踪参数自动移除"
    )
    filter_group.add_argument(
        "--keyword-blacklist",
        help="关键字黑名单（逗号分隔），过滤包含这些关键字的 URL"
    )
    filter_group.add_argument(
        "--enable-stats",
        action="store_true",
        help="启用详细统计功能，生成统计报告"
    )
    filter_group.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.0,
        help="文件内容查重阈值（0.0-1.0，超过此阈值则视为重复文件，0表示禁用，默认: 0.0）"
    )

    args = parser.parse_args()

    # 加载配置文件（如果提供）
    config = {}
    if args.config:
        config = load_config(args.config)
        if not config:
            sys.exit(1)

    # 合并配置：配置文件优先，命令行参数可覆盖
    def get_config_value(config_key, args_value, default=None):
        """从配置或命令行获取值"""
        config_value = config.get(config_key)
        if config_value is not None and config_value != '':
            return config_value
        return args_value if args_value is not None else default

    output_dir = get_config_value('output_dir', args.output_dir, "markdown_output")
    timeout = get_config_value('timeout', args.timeout, 30)
    max_workers = get_config_value('max_workers', args.max_workers, 4)
    max_retries = get_config_value('max_retries', args.max_retries, 3)
    keywords = get_config_value('keywords', args.keywords)
    user_agent = get_config_value('user_agent', None)

    # 深度爬取配置
    # 优先从 crawl.depth 读取，然后从顶层 depth，最后使用命令行参数
    if 'crawl' in config and config['crawl'] and 'depth' in config['crawl']:
        depth = config['crawl']['depth']
    else:
        depth = get_config_value('depth', args.depth, 0)

    # 处理 same_domain (布尔值)
    if 'crawl' in config and config['crawl']:
        same_domain = config['crawl'].get('same_domain', args.same_domain)
        if same_domain is None:
            same_domain = False
    else:
        same_domain = args.same_domain

    crawl_delay = config.get('crawl', {}).get('delay', args.crawl_delay) if 'crawl' in config else args.crawl_delay
    if crawl_delay is None:
        crawl_delay = 0.5

    # URL 范围控制配置
    scope_config = config.get('scope', {})
    if not scope_config:
        # 从命令行参数构建
        if args.allow_domains:
            scope_config['allow_domains'] = args.allow_domains.split(',')
        if args.deny_domains:
            scope_config['deny_domains'] = args.deny_domains.split(',')
        if args.allow_paths:
            scope_config['allow_paths'] = args.allow_paths.split(',')
        if args.deny_paths:
            scope_config['deny_paths'] = args.deny_paths.split(',')
        if args.allow_regex:
            scope_config['allow_regex'] = args.allow_regex
        if args.deny_regex:
            scope_config['deny_regex'] = args.deny_regex

    scope_matcher = create_scope_matcher_from_config(scope_config) if scope_config else None

    # URL 过滤器配置
    filter_config = config.get('filter', {})
    enable_filter_similar = filter_config.get('enable_similar', args.filter_similar)
    similarity_threshold = filter_config.get('similarity_threshold', args.similarity_threshold)
    disable_tracking = filter_config.get('disable_tracking', args.disable_filter_tracking)

    url_filter = None
    if enable_filter_similar or not disable_tracking:
        url_filter = URLFilter(
            similarity_threshold=similarity_threshold,
            enable_fuzzy=enable_filter_similar
        )
        if enable_filter_similar:
            logger.info("URL 相似度过滤已启用")
        else:
            logger.info("URL 跟踪参数过滤已启用")

    # 关键字黑名单配置
    keyword_blacklist = get_config_value('keyword_blacklist', args.keyword_blacklist)
    if keyword_blacklist:
        keyword_blacklist = [k.strip() for k in keyword_blacklist.split(',')]
        logger.info(f"关键字黑名单: {', '.join(keyword_blacklist)}")

    # 统计功能配置
    enable_stats = get_config_value('enable_stats', args.enable_stats, False)
    if enable_stats:
        logger.info("详细统计功能已启用")

    # 文件查重配置
    duplicate_threshold = get_config_value('duplicate_threshold', args.duplicate_threshold, 0.0)
    if duplicate_threshold > 0:
        logger.info(f"文件内容查重已启用，阈值: {duplicate_threshold:.2f}")

    # 检查参数
    # 从配置文件或命令行获取 URL 来源
    url = config.get('url')
    if not url:
        url = args.url
    batch = config.get('batch')
    if not batch:
        batch = args.batch
    sitemap = config.get('sitemap')
    if not sitemap:
        sitemap = args.sitemap

    logger.debug(f"URL: {url}, Batch: {batch}, Sitemap: {sitemap}")

    if not url and not batch and not sitemap:
        parser.error("必须提供 URL 或使用 --batch 或 --sitemap 参数")

    # 创建转换器
    converter = WebToMarkdown(
        output_dir=output_dir,
        timeout=timeout,
        max_workers=max_workers,
        max_retries=max_retries,
        scope_matcher=scope_matcher,
        url_filter=url_filter,
        keyword_blacklist=keyword_blacklist,
        enable_stats=enable_stats,
        duplicate_threshold=duplicate_threshold
    )

    # 执行转换
    if batch:
        batch_file = batch if batch else args.batch
        urls = read_urls_from_file(batch_file)
        if not urls:
            logger.error(f"未从 {batch_file} 读取到任何 URL")
            sys.exit(1)

        # 如果有深度限制，先使用爬虫收集 URL
        if depth > 0:
            all_urls = []
            for start_url in urls:
                crawler = WebCrawler(
                    max_depth=depth,
                    scope_matcher=scope_matcher,
                    same_domain_only=same_domain,
                    timeout=timeout,
                    delay=crawl_delay
                )
                discovered = crawler.crawl(start_url)
                all_urls.extend(discovered)
            # 去重
            urls = list(set(all_urls))
            logger.info(f"深度爬取后发现 {len(urls)} 个唯一 URL")

        converter.convert_batch(urls, keywords)

    elif sitemap:
        sitemap_url = sitemap if sitemap else args.sitemap
        urls = extract_urls_from_sitemap(sitemap_url, converter.headers)
        if not urls:
            logger.error(f"未能从 {sitemap_url} 获取 URL")
            sys.exit(1)
        converter.convert_batch(urls, keywords)

    else:
        # 单个 URL 处理
        current_urls = [url]

        # 如果有深度限制，使用爬虫收集 URL
        if depth > 0:
            crawler = WebCrawler(
                max_depth=depth,
                scope_matcher=scope_matcher,
                same_domain_only=same_domain,
                timeout=timeout,
                delay=crawl_delay
            )
            current_urls = crawler.crawl(url)
            logger.info(f"深度爬取后发现 {len(current_urls)} 个 URL")

        # 处理发现的 URL
        if len(current_urls) > 1:
            converter.convert_batch(current_urls, keywords)
        else:
            success = converter.convert(url, keywords, args.filename)
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
