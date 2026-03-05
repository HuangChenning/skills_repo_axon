#!/usr/bin/env python3
"""
URL 过滤和去重模块
支持 URL 标准化和相似度检测
"""

import re
import logging
from typing import Set, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class URLFilter:
    """
    URL 过滤器和去重器

    功能：
    - URL 标准化（移除跟踪参数、统一格式）
    - 精确去重
    - 可选的模糊相似度检测
    - 跟踪参数识别（utm_*, fbclid, gclid 等）
    """

    # 常见跟踪参数列表
    TRACKING_PARAMS = {
        # Google Analytics
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'utm_id', 'utm_source_platform', 'utm_creative_format', 'utm_marketing_tactic',
        # Facebook
        'fbclid', 'fb_action_ids', 'fb_action_types', 'fb_source',
        # Google Click ID
        'gclid',
        # Microsoft
        'msclkid', 'msclickid',
        # 其他
        'cid', 'igshid', 'ref', 'source', 'campaign',
        'mc_cid', 'mc_eid',
        '_ga', '_gl', 'gad', 'gclsrc',
        'spm', 'from', 'isappinstalled',
        'shareid', 'share_id',
        # Twitter/X
        's', 't', 'cn', 'ref_src',
        # LinkedIn
        'refId', 'refUid', 'trk', 'trackingId',
        # Amazon
        'tag', 'ref_', 'ascsubtag',
        # eBay
        'epid', 'itemId',
        # 通用
        'click_id', 'clickid', 'affiliate', 'aff', 'aff_id', 'affiliate_id',
        'referer', 'referrer', 'session_id', 'sid', 'sess_id',
    }

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        enable_fuzzy: bool = False,
        custom_tracking_params: Optional[Set[str]] = None
    ):
        """
        初始化 URL 过滤器

        Args:
            similarity_threshold: 相似度阈值（0-1），高于此值视为重复
            enable_fuzzy: 是否启用模糊相似度检测
            custom_tracking_params: 自定义跟踪参数集合
        """
        self.seen_urls: Set[str] = set()
        self.normalized_urls: dict = {}  # 标准化后的 URL 映射
        self.similarity_threshold = similarity_threshold
        self.enable_fuzzy = enable_fuzzy

        # 合并自定义跟踪参数
        self.tracking_params = self.TRACKING_PARAMS.copy()
        if custom_tracking_params:
            self.tracking_params.update(custom_tracking_params)

        # 统计信息
        self.stats = {
            'total_seen': 0,
            'duplicates_exact': 0,
            'duplicates_fuzzy': 0,
            'unique': 0
        }

    def normalize(self, url: str) -> str:
        """
        标准化 URL

        处理步骤：
        1. 解析 URL
        2. 移除跟踪参数
        3. 统一协议和域名（小写）
        4. 移除尾部斜杠
        5. 排序查询参数

        Args:
            url: 原始 URL

        Returns:
            标准化后的 URL
        """
        try:
            # 解析 URL
            parsed = urlparse(url)

            # 标准化协议和域名（小写）
            scheme = parsed.scheme.lower() if parsed.scheme else 'https'
            netloc = parsed.netloc.lower()

            # 移除端口号（如果是默认端口）
            if (scheme == 'http' and netloc.endswith(':80')) or \
               (scheme == 'https' and netloc.endswith(':443')):
                netloc = netloc.rsplit(':', 1)[0]

            # 处理路径
            path = parsed.path
            if path == '/':
                path = ''  # 移除根路径的斜杠
            elif path.endswith('/'):
                path = path.rstrip('/')  # 移除尾部斜杠

            # 处理查询参数 - 移除跟踪参数
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            filtered_params = {
                k: v for k, v in query_params.items()
                if k not in self.tracking_params
            }

            # 排序剩余参数（确保顺序不影响比较）
            query = urlencode(sorted(filtered_params.items()), doseq=True)

            # 移除 fragment（锚点）
            fragment = ''

            # 重建 URL
            normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))

            return normalized

        except Exception as e:
            logger.warning(f"URL 标准化失败 {url}: {e}")
            return url

    def similarity(self, url1: str, url2: str) -> float:
        """
        计算两个 URL 的相似度

        使用 SequenceMatcher 计算字符串相似度

        Args:
            url1: 第一个 URL
            url2: 第二个 URL

        Returns:
            相似度值（0-1），1 表示完全相同
        """
        return SequenceMatcher(None, url1, url2).ratio()

    def is_duplicate(self, url: str) -> bool:
        """
        检查 URL 是否重复

        Args:
            url: 要检查的 URL

        Returns:
            True 表示重复，False 表示新 URL
        """
        # 标准化 URL
        normalized = self.normalize(url)

        # 精确匹配
        if normalized in self.seen_urls:
            self.stats['duplicates_exact'] += 1
            return True

        # 模糊相似度检测
        if self.enable_fuzzy:
            for seen_url in self.seen_urls:
                sim = self.similarity(normalized, seen_url)
                if sim >= self.similarity_threshold:
                    logger.info(f"[相似度过滤] {url} 与 {seen_url} 相似度 {sim:.2f} >= {self.similarity_threshold}")
                    self.stats['duplicates_fuzzy'] += 1
                    return True

        return False

    def add(self, url: str) -> bool:
        """
        添加 URL，返回是否为新 URL

        Args:
            url: 要添加的 URL

        Returns:
            True 表示新 URL（已添加），False 表示重复
        """
        self.stats['total_seen'] += 1

        if self.is_duplicate(url):
            return False

        # 添加到已见集合
        normalized = self.normalize(url)
        self.seen_urls.add(normalized)
        self.stats['unique'] += 1
        return True

    def add_batch(self, urls: List[str]) -> Tuple[List[str], int]:
        """
        批量添加 URL，返回唯一的 URL 列表

        Args:
            urls: URL 列表

        Returns:
            (唯一 URL 列表, 过滤掉的数量)
        """
        unique_urls = []
        filtered_count = 0

        for url in urls:
            if self.add(url):
                unique_urls.append(url)
            else:
                filtered_count += 1

        return unique_urls, filtered_count

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.stats.copy()

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("URL 过滤统计")
        print("=" * 50)
        print(f"总计处理: {self.stats['total_seen']} 个 URL")
        print(f"唯一 URL: {self.stats['unique']} 个")
        print(f"精确重复: {self.stats['duplicates_exact']} 个")
        if self.enable_fuzzy:
            print(f"模糊重复: {self.stats['duplicates_fuzzy']} 个")
        print(f"过滤率: {(self.stats['total_seen'] - self.stats['unique']) / max(self.stats['total_seen'], 1) * 100:.1f}%")
        print("=" * 50)

    def reset(self):
        """重置过滤器状态"""
        self.seen_urls.clear()
        self.normalized_urls.clear()
        self.stats = {
            'total_seen': 0,
            'duplicates_exact': 0,
            'duplicates_fuzzy': 0,
            'unique': 0
        }
        logger.info("URL 过滤器已重置")


def extract_urls_from_text(text: str, base_url: str = '') -> List[str]:
    """
    从文本中提取 URL

    Args:
        text: 包含 URL 的文本
        base_url: 基础 URL（用于相对路径）

    Returns:
        URL 列表
    """
    # URL 正则表达式
    url_pattern = re.compile(
        r'http[s]?://'  # 协议
        r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # 域名和路径
    )

    urls = url_pattern.findall(text)
    return list(set(urls))  # 去重


def is_valid_url(url: str) -> bool:
    """
    检查 URL 是否有效

    Args:
        url: 要检查的 URL

    Returns:
        True 表示有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def filter_urls_by_pattern(urls: List[str], include_pattern: str = None, exclude_pattern: str = None) -> List[str]:
    """
    根据正则表达式过滤 URL

    Args:
        urls: URL 列表
        include_pattern: 包含模式（只保留匹配的）
        exclude_pattern: 排除模式（移除匹配的）

    Returns:
        过滤后的 URL 列表
    """
    filtered = urls

    if include_pattern:
        regex = re.compile(include_pattern)
        filtered = [u for u in filtered if regex.search(u)]

    if exclude_pattern:
        regex = re.compile(exclude_pattern)
        filtered = [u for u in filtered if not regex.search(u)]

    return filtered
