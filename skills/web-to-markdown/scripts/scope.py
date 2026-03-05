#!/usr/bin/env python3
"""
URL 范围控制模块
支持域名白名单/黑名单、路径模式匹配
"""

import re
import logging
from typing import Optional, List, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ScopeMatcher:
    """URL 范围匹配器"""

    def __init__(
        self,
        allow_domains: Optional[List[str]] = None,
        deny_domains: Optional[List[str]] = None,
        allow_paths: Optional[List[str]] = None,
        deny_paths: Optional[List[str]] = None,
        allow_regex: Optional[str] = None,
        deny_regex: Optional[str] = None
    ):
        """
        初始化范围匹配器

        Args:
            allow_domains: 域名白名单列表（只处理这些域名）
            deny_domains: 域名黑名单列表（不处理这些域名）
            allow_paths: 路径白名单列表（只处理这些路径前缀）
            deny_paths: 路径黑名单列表（不处理这些路径前缀）
            allow_regex: 允许 URL 的正则表达式
            deny_regex: 拒绝 URL 的正则表达式
        """
        # 标准化域名列表（移除 www. 前缀，转换为小写）
        self.allow_domains = self._normalize_domains(allow_domains) if allow_domains else None
        self.deny_domains = self._normalize_domains(deny_domains) if deny_domains else None

        # 标准化路径列表（确保以 / 开头）
        self.allow_paths = self._normalize_paths(allow_paths) if allow_paths else None
        self.deny_paths = self._normalize_paths(deny_paths) if deny_paths else None

        # 编译正则表达式
        self.allow_pattern = re.compile(allow_regex) if allow_regex else None
        self.deny_pattern = re.compile(deny_regex) if deny_regex else None

        # 记录配置
        self._log_config()

    def is_allowed(self, url: str) -> bool:
        """
        检查 URL 是否在允许范围内

        Args:
            url: 要检查的 URL

        Returns:
            True 如果 URL 允许处理，False 否则
        """
        try:
            parsed = urlparse(url)

            # 检查域名黑名单（优先级最高）
            if self.deny_domains:
                domain = self._normalize_domain(parsed.netloc)
                if domain in self.deny_domains:
                    logger.info(f"[范围过滤-黑名单] 域名 {domain}: {url}")
                    return False

            # 检查路径黑名单
            if self.deny_paths:
                path = parsed.path
                if any(path.startswith(deny_path) for deny_path in self.deny_paths):
                    logger.info(f"[范围过滤-黑名单] 路径 {path}: {url}")
                    return False

            # 检查正则表达式黑名单
            if self.deny_pattern and self.deny_pattern.search(url):
                logger.info(f"[范围过滤-黑名单] 正则匹配: {url}")
                return False

            # 检查域名白名单
            if self.allow_domains:
                domain = self._normalize_domain(parsed.netloc)
                if domain not in self.allow_domains:
                    logger.info(f"[范围过滤-白名单] 域名 {domain} 不在允许列表: {url}")
                    return False

            # 检查路径白名单
            if self.allow_paths:
                path = parsed.path
                if not any(path.startswith(allow_path) for allow_path in self.allow_paths):
                    logger.info(f"[范围过滤-白名单] 路径 {path} 不在允许列表: {url}")
                    return False

            # 检查正则表达式白名单
            if self.allow_pattern and not self.allow_pattern.search(url):
                logger.info(f"[范围过滤-白名单] 不匹配正则: {url}")
                return False

            return True

        except Exception as e:
            logger.error(f"检查 URL 时出错: {url}, 错误: {e}")
            return False

    def _normalize_domain(self, domain: str) -> str:
        """
        标准化域名

        Args:
            domain: 原始域名

        Returns:
            标准化后的域名（小写，无 www. 前缀）
        """
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    def _normalize_domains(self, domains: List[str]) -> Set[str]:
        """
        标准化域名列表

        Args:
            domains: 域名列表

        Returns:
            标准化后的域名集合
        """
        return {self._normalize_domain(d) for d in domains}

    def _normalize_paths(self, paths: List[str]) -> Set[str]:
        """
        标准化路径列表

        Args:
            paths: 路径列表

        Returns:
            标准化后的路径集合
        """
        normalized = set()
        for path in paths:
            path = path.strip()
            if not path.startswith('/'):
                path = '/' + path
            normalized.add(path)
        return normalized

    def _log_config(self):
        """记录配置信息"""
        if self.allow_domains:
            logger.info(f"域名白名单: {self.allow_domains}")
        if self.deny_domains:
            logger.info(f"域名黑名单: {self.deny_domains}")
        if self.allow_paths:
            logger.info(f"路径白名单: {self.allow_paths}")
        if self.deny_paths:
            logger.info(f"路径黑名单: {self.deny_paths}")
        if self.allow_pattern:
            logger.info(f"允许正则: {self.allow_pattern.pattern}")
        if self.deny_pattern:
            logger.info(f"拒绝正则: {self.deny_pattern.pattern}")


def create_scope_matcher_from_config(config: dict) -> ScopeMatcher:
    """
    从配置字典创建 ScopeMatcher

    Args:
        config: 配置字典，包含以下键：
            - allow_domains: List[str]
            - deny_domains: List[str]
            - allow_paths: List[str]
            - deny_paths: List[str]
            - allow_regex: str
            - deny_regex: str

    Returns:
        ScopeMatcher 实例
    """
    return ScopeMatcher(
        allow_domains=config.get('allow_domains'),
        deny_domains=config.get('deny_domains'),
        allow_paths=config.get('allow_paths'),
        deny_paths=config.get('deny_paths'),
        allow_regex=config.get('allow_regex'),
        deny_regex=config.get('deny_regex')
    )


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 示例 1: 只允许特定域名
    matcher1 = ScopeMatcher(
        allow_domains=['docs.python.org', 'github.com']
    )
    print(f"允许 python.org: {matcher1.is_allowed('https://docs.python.org/3/tutorial/')}")
    print(f"允许 google.com: {matcher1.is_allowed('https://www.google.com/')}")

    # 示例 2: 排除特定路径
    matcher2 = ScopeMatcher(
        allow_domains=['docs.python.org'],
        deny_paths=['/api/', '/reference/']
    )
    print(f"允许教程: {matcher2.is_allowed('https://docs.python.org/3/tutorial/')}")
    print(f"允许 API: {matcher2.is_allowed('https://docs.python.org/3/api/')}")

    # 示例 3: 使用正则表达式
    matcher3 = ScopeMatcher(
        allow_regex=r'https://docs\.python\.org/3/.*tutorial.*'
    )
    print(f"匹配教程: {matcher3.is_allowed('https://docs.python.org/3/tutorial/')}")
    print(f"匹配库: {matcher3.is_allowed('https://docs.python.org/3/library/')}")
