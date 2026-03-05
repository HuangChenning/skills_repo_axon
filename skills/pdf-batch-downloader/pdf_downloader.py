#!/usr/bin/env python3
"""
PDF 批量下载器 (优化版)
从网页提取所有 PDF 链接并批量下载

新特性:
- 支持从 sitemap 获取链接
- 智能文件名生成（支持多种网站结构）
- 下载重试机制
- 更好的错误处理
- 支持从文件导入 URL 列表
"""

import os
import re
import sys
import time
import logging
import argparse
from urllib.parse import urljoin, urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Set
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFBatchDownloader:
    """PDF 批量下载器类（优化版）"""

    def __init__(
        self,
        output_dir: str = "pdf_downloads",
        max_workers: int = 4,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        user_agent: str = None
    ):
        """
        初始化 PDF 批量下载器

        Args:
            output_dir: 输出目录路径
            max_workers: 并发下载数量
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            user_agent: 自定义 User-Agent
        """
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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

        # 统计信息
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

        # 记录已下载的文件
        self.downloaded_files: Set[str] = set()

        # 记录失败的 URL
        self.failed_urls: List[str] = []

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

    def extract_from_sitemap(self, base_url: str, filter_pattern: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        从 sitemap.xml 提取 PDF 链接

        Args:
            base_url: 基础 URL
            filter_pattern: 过滤模式

        Returns:
            (标题, URL) 列表
        """
        # 尝试常见的 sitemap 位置
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
        ]

        pdf_links = []
        for sitemap_url in sitemap_urls:
            response = self.fetch_with_retry(sitemap_url)
            if response:
                soup = BeautifulSoup(response.content, 'lxml')
                for loc in soup.find_all('loc'):
                    url = loc.get_text(strip=True)
                    if self._is_pdf_url(url):
                        if filter_pattern and not re.search(filter_pattern, url):
                            continue
                        # 从 URL 生成标题
                        title = self._extract_title_from_url(url)
                        pdf_links.append((title, url))

                if pdf_links:
                    logger.info(f"从 sitemap 找到 {len(pdf_links)} 个 PDF 链接")
                    break

        return pdf_links

    def extract_from_html(self, response: requests.Response, base_url: str, filter_pattern: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        从 HTML 提取 PDF 链接（支持多种网站结构）

        Args:
            response: HTTP 响应
            base_url: 基础 URL
            filter_pattern: 过滤模式

        Returns:
            (标题, URL) 列表
        """
        soup = BeautifulSoup(response.content, 'lxml')
        pdf_links = []

        # 方法 1: Oracle 文档结构 (booklist + booktitle)
        for booklist in soup.find_all('div', class_='booklist'):
            title = ''
            booktitle = booklist.find('div', class_='booktitle')
            if booktitle:
                title_link = booktitle.find('a')
                if title_link:
                    title = title_link.get_text(strip=True)

            pdf_link = booklist.find('a', href=lambda x: x and '.pdf' in x)
            if pdf_link:
                href = pdf_link['href']
                absolute_url = urljoin(base_url, href)

                if filter_pattern and not re.search(filter_pattern, absolute_url):
                    continue

                link_text = title if title else pdf_link.get_text(strip=True)
                pdf_links.append((link_text, absolute_url))

        # 方法 2: 通用方法 - 查找所有 PDF 链接
        if not pdf_links:
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(base_url, href)

                if self._is_pdf_url(absolute_url):
                    if filter_pattern and not re.search(filter_pattern, absolute_url):
                        continue

                    # 尝试从多个位置获取标题
                    text = (link.get('title') or
                           link.get_text(strip=True) or
                           link.get('aria-label', ''))

                    # 如果标题是通用文本，尝试从父元素获取
                    if text.lower() in ['pdf', 'download', 'view', '']:
                        # 查找相邻的标题元素
                        parent = link.parent
                        if parent:
                            # 查找同级的标题元素
                            for sibling in parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong']):
                                title = sibling.get_text(strip=True)
                                if title and len(title) > 3:
                                    text = title
                                    break

                    pdf_links.append((text, absolute_url))

        logger.info(f"从 HTML 找到 {len(pdf_links)} 个 PDF 链接")
        return pdf_links

    def extract_pdf_links(
        self,
        url: str,
        filter_pattern: Optional[str] = None,
        use_sitemap: bool = False
    ) -> List[Tuple[str, str]]:
        """
        提取 PDF 链接（自动选择最佳方法）

        Args:
            url: 网页 URL
            filter_pattern: URL 过滤正则表达式
            use_sitemap: 是否优先使用 sitemap

        Returns:
            包含 (文档标题, PDF URL) 的列表
        """
        # 如果指定使用 sitemap 或 URL 是 sitemap
        if use_sitemap or 'sitemap' in url.lower():
            return self.extract_from_sitemap(url, filter_pattern)

        # 尝试从 HTML 提取
        response = self.fetch_with_retry(url)
        if response:
            pdf_links = self.extract_from_html(response, url, filter_pattern)

            # 如果 HTML 中没有找到链接，尝试 sitemap
            if not pdf_links:
                logger.info("HTML 中未找到 PDF 链接，尝试从 sitemap 获取...")
                pdf_links = self.extract_from_sitemap(url, filter_pattern)

            return pdf_links

        return []

    def _is_pdf_url(self, url: str) -> bool:
        """检查 URL 是否指向 PDF 文件"""
        parsed = urlparse(url)
        path = unquote(parsed.path.lower())

        # 检查 .pdf 扩展名
        if path.endswith('.pdf'):
            return True

        # 检查某些特殊模式
        if '.pdf' in path or '.pdf?' in url.lower():
            return True

        return False

    def _extract_title_from_url(self, url: str) -> str:
        """从 URL 提取标题"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # 移除 .pdf 扩展名
        title = path.replace('.pdf', '')

        # 使用路径的最后一部分
        parts = title.split('/')
        if parts:
            title = parts[-1]

        # 替换连字符和下划线为空格
        title = title.replace('-', ' ').replace('_', ' ')

        return title.strip()

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

        # 替换多个连续空格为单个空格
        filename = re.sub(r'\s+', ' ', filename)

        # 移除首尾空格和点
        filename = filename.strip('. ')

        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]

        return filename if filename else 'unnamed'

    def generate_filename(self, link_text: str, url: str, index: int) -> str:
        """
        生成 PDF 文件名

        Args:
            link_text: 链接文本（可能是文档标题）
            url: PDF URL
            index: 索引号

        Returns:
            文件名（不含扩展名）
        """
        name = None

        # 优先使用链接文本作为文件名
        if link_text and link_text.lower() not in ['pdf', 'view', 'download', '']:
            name = self.sanitize_filename(link_text)

        # 如果没有标题，从 URL 提取
        if not name:
            name = self._extract_title_from_url(url)

        # 如果仍然没有名称，使用索引
        if not name:
            name = f"document_{index:03d}"

        return self.sanitize_filename(name)

    def download_pdf(self, url: str, filename: str) -> bool:
        """
        下载单个 PDF 文件（带重试）

        Args:
            url: PDF URL
            filename: 目标文件名

        Returns:
            成功返回 True，失败返回 False
        """
        filepath = os.path.join(self.output_dir, f"{filename}.pdf")

        # 检查文件是否已存在
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 1024:  # 大于 1KB 认为有效
                logger.debug(f"文件已存在，跳过: {filename}.pdf")
                self.stats["skipped"] += 1
                return True

        # 带重试的下载
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()

                # 写入临时文件
                temp_filepath = filepath + '.tmp'
                with open(temp_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # 下载完成后重命名
                os.rename(temp_filepath, filepath)

                logger.info(f"下载成功: {filename}.pdf")
                self.stats["success"] += 1
                self.downloaded_files.add(filename)
                return True

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"下载失败 {filename}，{self.retry_delay}秒后重试... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"下载失败 {filename}: {e}")
                    self.stats["failed"] += 1
                    self.failed_urls.append(url)

                    # 删除不完整的文件
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    if os.path.exists(filepath + '.tmp'):
                        os.remove(filepath + '.tmp')

                    return False

    def download_batch(
        self,
        pdf_links: List[Tuple[str, str]],
        show_progress: bool = True
    ) -> None:
        """
        批量下载 PDF 文件

        Args:
            pdf_links: (链接文本, URL) 列表
            show_progress: 是否显示进度条
        """
        self.stats["total"] = len(pdf_links)

        if show_progress:
            logger.info(f"开始批量下载 {len(pdf_links)} 个 PDF 文件...")

        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 准备下载任务
            futures = {}
            used_filenames = set()

            for index, (text, url) in enumerate(pdf_links, 1):
                filename = self.generate_filename(text, url, index)

                # 处理重名
                original_name = filename
                counter = 1
                while filename in used_filenames:
                    filename = f"{original_name}_{counter}"
                    counter += 1

                used_filenames.add(filename)
                future = executor.submit(self.download_pdf, url, filename)
                futures[future] = (text, url, filename)

            # 等待所有任务完成
            if show_progress:
                with tqdm(total=len(pdf_links), desc="下载进度", unit="文件") as pbar:
                    for future in as_completed(futures):
                        text, url, filename = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"处理 {filename} 时出错: {e}")
                        pbar.update(1)
            else:
                for future in as_completed(futures):
                    future.result()

    def print_summary(self):
        """打印下载摘要"""
        print("\n" + "=" * 50)
        print("下载完成！")
        print("=" * 50)
        print(f"总计: {self.stats['total']} 个文件")
        print(f"成功: {self.stats['success']} 个")
        print(f"跳过: {self.stats['skipped']} 个（已存在）")
        print(f"失败: {self.stats['failed']} 个")
        print(f"输出目录: {os.path.abspath(self.output_dir)}")

        if self.failed_urls:
            print("\n失败的 URL:")
            for url in self.failed_urls[:10]:
                print(f"  - {url[:80]}")
            if len(self.failed_urls) > 10:
                print(f"  ... 还有 {len(self.failed_urls) - 10} 个")

        print("=" * 50)

    def run(
        self,
        url: str,
        filter_pattern: Optional[str] = None,
        show_progress: bool = True,
        use_sitemap: bool = False
    ) -> bool:
        """
        运行批量下载流程

        Args:
            url: 要扫描的网页 URL
            filter_pattern: URL 过滤正则表达式
            show_progress: 是否显示进度
            use_sitemap: 是否使用 sitemap

        Returns:
            成功返回 True
        """
        # 提取 PDF 链接
        pdf_links = self.extract_pdf_links(url, filter_pattern, use_sitemap)

        if not pdf_links:
            logger.warning("未找到任何 PDF 链接")
            return False

        # 显示找到的链接（前 10 个）
        logger.info("找到的 PDF 链接（显示前 10 个）:")
        for i, (text, url) in enumerate(pdf_links[:10], 1):
            name = text if text else os.path.basename(urlparse(url).path)
            print(f"  {i}. {name[:60]} -> {url[:60]}...")
        if len(pdf_links) > 10:
            print(f"  ... 还有 {len(pdf_links) - 10} 个链接")

        # 批量下载
        self.download_batch(pdf_links, show_progress)

        # 打印摘要
        self.print_summary()

        return True


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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF 批量下载器 - 从网页提取并下载所有 PDF 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从网页下载所有 PDF
  %(prog)s https://docs.oracle.com/cd/E11882_01/nav/portal_booklist.htm

  # 指定输出目录
  %(prog)s https://example.com/docs --output-dir my_pdfs

  # 使用更多并发线程
  %(prog)s https://example.com/docs --max-workers 8

  # 过滤特定 PDF
  %(prog)s https://example.com/docs --filter-pattern ".*guide.*"

  # 从 sitemap 获取
  %(prog)s https://example.com --use-sitemap

  # 从文件读取 URL 列表
  %(prog)s --file urls.txt
        """
    )

    parser.add_argument(
        "url",
        nargs='?',
        help="要扫描的网页 URL（使用 --file 时可选）"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default="pdf_downloads",
        help="输出目录路径（默认: pdf_downloads）"
    )

    parser.add_argument(
        "-w", "--max-workers",
        type=int,
        default=4,
        help="并发下载数量（默认: 4）"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="请求超时时间（秒，默认: 30）"
    )

    parser.add_argument(
        "-r", "--max-retries",
        type=int,
        default=3,
        help="最大重试次数（默认: 3）"
    )

    parser.add_argument(
        "-f", "--filter-pattern",
        help="URL 过滤正则表达式"
    )

    parser.add_argument(
        "--use-sitemap",
        action="store_true",
        help="优先从 sitemap.xml 获取链接"
    )

    parser.add_argument(
        "--file",
        metavar="FILE",
        help="从文件读取 URL 列表"
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="不显示进度条"
    )

    args = parser.parse_args()

    # 检查参数
    if not args.url and not args.file:
        parser.error("必须提供 URL 或使用 --file 参数")

    # 创建下载器
    downloader = PDFBatchDownloader(
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        timeout=args.timeout,
        max_retries=args.max_retries
    )

    # 运行下载
    if args.file:
        urls = read_urls_from_file(args.file)
        if not urls:
            logger.error(f"未从 {args.file} 读取到任何 URL")
            sys.exit(1)

        all_links = []
        for url in urls:
            links = downloader.extract_pdf_links(url, args.filter_pattern, args.use_sitemap)
            all_links.extend(links)

        downloader.download_batch(all_links, not args.no_progress)
        downloader.print_summary()
        success = downloader.stats['success'] > 0
    else:
        success = downloader.run(
            url=args.url,
            filter_pattern=args.filter_pattern,
            show_progress=not args.no_progress,
            use_sitemap=args.use_sitemap
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
