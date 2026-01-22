#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xinye 爬虫
"""

import re
import time
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector
from src.core.exceptions import (
    ArticleLinkNotFoundError,
    NetworkError,
    RequestTimeoutError,
    ConnectionError as V2RayConnectionError,
)


class XinyeCollector(BaseCollector):
    """Xinye 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)

    def find_subscription_links(self, content):
        """查找订阅链接 - 专门处理 xinye.eu.org 的格式"""
        links = []

        # 查找 GitHub raw 链接（主要来源）
        github_pattern = r'https://raw\.githubusercontent\.com/[^\s<>"]+\.txt'
        github_matches = re.findall(github_pattern, content)
        links.extend(github_matches)

        # 调用父类方法获取其他可能的链接
        parent_links = super().find_subscription_links(content)
        links.extend(parent_links)

        # 去重
        return list(set(links))

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)