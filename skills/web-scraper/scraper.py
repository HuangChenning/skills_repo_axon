#!/usr/bin/env python3
"""
Web Scraper - 通用网页数据抓取工具
支持 CSS 选择器和 XPath 提取数据
"""

import os
import re
import json
import csv
import logging
import argparse
from typing import Any, List, Dict, Optional, Union
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import yaml
import pandas as pd
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FieldExtractor:
    """字段提取器"""

    def __init__(
        self,
        name: str,
        selector: str,
        field_type: str = "text",
        attribute: Optional[str] = None,
        regex: Optional[str] = None,
        multiple: bool = False
    ):
        """
        初始化字段提取器

        Args:
            name: 字段名称
            selector: CSS 选择器或 XPath
            field_type: 数据类型
            attribute: 提取属性（而非文本）
            regex: 正则表达式过滤
            multiple: 是否提取多个值
        """
        self.name = name
        self.selector = selector
        self.field_type = field_type
        self.attribute = attribute
        self.regex = re.compile(regex) if regex else None
        self.multiple = multiple

    def extract(self, soup: BeautifulSoup, base_url: str = "") -> Any:
        """
        从 BeautifulSoup 对象提取数据

        Args:
            soup: BeautifulSoup 对象
            base_url: 基础 URL（用于相对链接）

        Returns:
            提取的数据
        """
        try:
            # 处理属性选择器语法 (selector@attribute)
            if '@' in self.selector and not self.attribute:
                selector_part, attr_part = self.selector.split('@', 1)
                elements = soup.select(selector_part)
                if elements:
                    result = elements[0].get(attr_part)
                    return self._process_value(result, base_url)
                return None

            # 使用 CSS 选择器
            elements = soup.select(self.selector)

            if not elements:
                return None

            # 提取数据
            if self.multiple:
                results = []
                for elem in elements:
                    value = self._extract_single(elem, base_url)
                    if value is not None:
                        results.append(value)
                return results if results else None
            else:
                return self._extract_single(elements[0], base_url)

        except Exception as e:
            logger.warning(f"提取字段 {self.name} 失败: {e}")
            return None

    def _extract_single(self, element, base_url: str) -> Any:
        """提取单个元素的数据"""
        # 提取属性或文本
        if self.attribute:
            value = element.get(self.attribute)
        else:
            value = element.get_text(strip=True)

        return self._process_value(value, base_url)

    def _process_value(self, value: Optional[str], base_url: str) -> Any:
        """处理和转换提取的值"""
        if value is None:
            return None

        # 应用正则表达式
        if self.regex:
            match = self.regex.search(value)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
            else:
                return None

        # 类型转换
        try:
            if self.field_type == "text":
                return value.strip()

            elif self.field_type == "number":
                # 提取数字
                numbers = re.findall(r'[-+]?\d*\.?\d+', value)
                return int(numbers[0]) if numbers else None

            elif self.field_type == "float":
                # 提取浮点数
                numbers = re.findall(r'[-+]?\d*\.?\d+', value)
                return float(numbers[0]) if numbers else None

            elif self.field_type == "url":
                # 转换为绝对 URL
                if base_url and value and not value.startswith('http'):
                    return urljoin(base_url, value)
                return value

            elif self.field_type == "email":
                # 提取邮箱
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', value)
                return emails[0] if emails else None

            elif self.field_type == "html":
                return str(value)

            else:
                return value

        except (ValueError, IndexError) as e:
            logger.warning(f"类型转换失败: {value} -> {self.field_type}: {e}")
            return value


class WebScraper:
    """网页数据抓取器"""

    def __init__(
        self,
        config: Optional[Dict] = None,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = None
    ):
        """
        初始化抓取器

        Args:
            config: 配置字典
            delay: 请求间隔（秒）
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
            user_agent: 自定义 User-Agent
        """
        self.config = config or {}
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries

        # 初始化字段提取器
        self.extractors: List[FieldExtractor] = []
        if 'fields' in self.config:
            for field_config in self.config['fields']:
                extractor = FieldExtractor(
                    name=field_config['name'],
                    selector=field_config['selector'],
                    field_type=field_config.get('type', 'text'),
                    attribute=field_config.get('attribute'),
                    regex=field_config.get('regex'),
                    multiple=field_config.get('multiple', False)
                )
                self.extractors.append(extractor)

        # 配置请求头
        self.headers = {
            'User-Agent': user_agent or (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }

        # 统计信息
        self.stats = {
            'total_pages': 0,
            'successful': 0,
            'failed': 0,
            'items_extracted': 0
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取网页内容

        Args:
            url: 网页 URL

        Returns:
            HTML 内容，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在获取: {url} (尝试 {attempt + 1}/{self.max_retries})")
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text

            except requests.RequestException as e:
                logger.warning(f"请求失败: {url}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    logger.error(f"无法获取页面: {url}")
                    return None

    def extract_data(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        从 HTML 提取数据

        Args:
            html: HTML 内容
            url: 页面 URL（用于处理相对链接）

        Returns:
            提取的数据字典
        """
        soup = BeautifulSoup(html, 'lxml')
        data = {}

        for extractor in self.extractors:
            value = extractor.extract(soup, url)
            data[extractor.name] = value

        if data:
            self.stats['items_extracted'] += 1

        return data

    def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取单个网页

        Args:
            url: 网页 URL

        Returns:
            提取的数据字典
        """
        self.stats['total_pages'] += 1

        # 获取页面
        html = self.fetch_page(url)
        if not html:
            self.stats['failed'] += 1
            return None

        # 提取数据
        data = self.extract_data(html, url)
        if data:
            self.stats['successful'] += 1
            # 添加元数据
            data['_meta'] = {
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }

        # 请求延迟
        if self.delay > 0:
            time.sleep(self.delay)

        return data

    def scrape_batch(self, urls: List[str], show_progress: bool = True) -> List[Dict]:
        """
        批量抓取多个网页

        Args:
            urls: URL 列表
            show_progress: 是否显示进度

        Returns:
            提取的数据列表
        """
        results = []

        iterator = tqdm(urls, desc="抓取进度") if show_progress else urls

        for url in iterator:
            data = self.scrape(url)
            if data:
                results.append(data)

        return results

    def save_results(
        self,
        data: List[Dict],
        output_file: str,
        format: str = "json"
    ) -> bool:
        """
        保存提取结果

        Args:
            data: 提取的数据列表
            output_file: 输出文件路径
            format: 输出格式 (json/csv/excel)

        Returns:
            成功返回 True
        """
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            elif format == "csv":
                # 展开嵌套字典
                df = pd.json_normalize(data)
                df.to_csv(output_file, index=False, encoding='utf-8-sig')

            elif format == "excel":
                df = pd.json_normalize(data)
                df.to_excel(output_file, index=False)

            else:
                logger.error(f"不支持的格式: {format}")
                return False

            logger.info(f"结果已保存到: {output_file}")
            return True

        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return False

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("抓取统计")
        print("=" * 50)
        print(f"总页面数: {self.stats['total_pages']}")
        print(f"成功: {self.stats['successful']}")
        print(f"失败: {self.stats['failed']}")
        print(f"提取数据: {self.stats['items_extracted']} 条")
        print("=" * 50)


def load_config(config_file: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Web Scraper - 通用网页数据抓取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取标题
  %(prog)s https://example.com --selector "h1"

  # 使用配置文件
  %(prog)s https://example.com --config config.yaml

  # 批量处理
  %(prog)s --batch urls.txt --config config.yaml

  # 导出为 CSV
  %(prog)s https://example.com --selector ".price" --format csv --output prices.csv

  # 多字段提取
  %(prog)s https://example.com --fields title="h1",price=".price"
        """
    )

    parser.add_argument("url", nargs='?', help="目标网页 URL")
    parser.add_argument("-s", "--selector", help="CSS 选择器或 XPath")
    parser.add_argument("-c", "--config", help="配置文件路径")
    parser.add_argument("-b", "--batch", metavar="FILE", help="批量处理 URL 文件")
    parser.add_argument("-f", "--format", choices=['json', 'csv', 'excel'],
                        default="json", help="输出格式（默认: json）")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--attribute", help="提取属性（而非文本）")
    parser.add_argument("--regex", help="正则表达式过滤")
    parser.add_argument("--fields", help="多字段提取（逗号分隔，格式: name=selector）")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔（秒，默认: 1）")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时（秒，默认: 30）")
    parser.add_argument("--max-retries", type=int, default=3, help="最大重试次数（默认: 3）")

    args = parser.parse_args()

    # 检查参数
    if not args.url and not args.batch:
        parser.error("必须提供 URL 或使用 --batch 参数")

    # 加载配置或创建默认配置
    config = {}
    if args.config:
        config = load_config(args.config)
    elif args.fields:
        # 从命令行参数创建配置
        fields = []
        for field_def in args.fields.split(','):
            name, selector = field_def.split('=', 1)
            fields.append({
                'name': name.strip(),
                'selector': selector.strip(),
                'type': 'text'
            })
        config['fields'] = fields
    elif args.selector:
        # 单字段配置
        config['fields'] = [{
            'name': 'value',
            'selector': args.selector,
            'type': 'text',
            'attribute': args.attribute,
            'regex': args.regex
        }]

    # 创建抓取器
    scraper = WebScraper(
        config=config,
        delay=args.delay,
        timeout=args.timeout,
        max_retries=args.max_retries
    )

    # 执行抓取
    if args.batch:
        # 从文件读取 URL
        with open(args.batch, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        data = scraper.scrape_batch(urls)
    else:
        result = scraper.scrape(args.url)
        data = [result] if result else []

    # 保存结果
    if data:
        output_file = args.output or f"results.{args.format}"
        scraper.save_results(data, output_file, args.format)
        scraper.print_stats()

        # 打印预览
        print("\n数据预览（前 3 条）:")
        for i, item in enumerate(data[:3], 1):
            print(f"\n[{i}] {item.get('_meta', {}).get('url', 'N/A')}")
            for key, value in item.items():
                if key != '_meta':
                    print(f"  {key}: {value}")

        sys.exit(0)
    else:
        logger.error("未提取到任何数据")
        sys.exit(1)


if __name__ == "__main__":
    main()
