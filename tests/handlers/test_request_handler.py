#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.request_handler
测试请求处理器的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout, ConnectionError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.request_handler import RequestHandler
from src.core.exceptions import NetworkError


class TestRequestHandler:
    """请求处理器测试"""

    @pytest.fixture
    def mock_logger(self):
        """创建模拟的日志记录器"""
        logger = Mock()
        logger.debug = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        logger.info = Mock()
        return logger

    @pytest.fixture
    def mock_session(self):
        """创建模拟的 requests.Session"""
        session = Mock()
        return session

    @pytest.fixture
    def handler(self, mock_session, mock_logger):
        """创建请求处理器实例"""
        return RequestHandler(
            session=mock_session,
            timeout=30,
            retry_count=3,
            logger=mock_logger
        )

    @pytest.fixture
    def mock_response(self):
        """创建模拟的响应"""
        response = Mock()
        response.status_code = 200
        response.text = "测试内容"
        response.content = "测试内容".encode("utf-8")
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        response.raise_for_status = Mock()
        return response

    def test_get_request_success(self, handler, mock_session, mock_response):
        """测试成功的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com")

        assert response is not None
        assert response.status_code == 200
        assert response.text == "测试内容"
        mock_session.get.assert_called_once()

    def test_get_request_with_headers(self, handler, mock_session, mock_response):
        """测试带请求头的GET请求"""
        mock_session.get.return_value = mock_response

        headers = {"User-Agent": "test"}
        response = handler.get("http://example.com", headers=headers)

        assert response is not None
        mock_session.get.assert_called_once()

    def test_get_request_with_timeout(self, handler, mock_session, mock_response):
        """测试带超时的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", timeout=10)

        assert response is not None

    def test_get_request_timeout_error(self, handler, mock_session):
        """测试超时错误"""
        mock_session.get.side_effect = Timeout("请求超时")

        with pytest.raises(NetworkError):
            handler.get("http://example.com")

    def test_get_request_connection_error(self, handler, mock_session):
        """测试连接错误"""
        mock_session.get.side_effect = ConnectionError("连接失败")

        with pytest.raises(NetworkError):
            handler.get("http://example.com")

    def test_get_request_http_error(self, handler, mock_session):
        """测试HTTP错误"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("HTTP错误")
        mock_session.get.return_value = mock_response

        with pytest.raises(NetworkError):
            handler.get("http://example.com")

    def test_post_request_success(self, handler, mock_session, mock_response):
        """测试成功的POST请求"""
        mock_session.post.return_value = mock_response

        response = handler.post("http://example.com", data={"key": "value"})

        assert response is not None
        assert response.status_code == 200

    def test_post_request_with_json(self, handler, mock_session, mock_response):
        """测试带JSON数据的POST请求"""
        mock_session.post.return_value = mock_response

        response = handler.post("http://example.com", json={"key": "value"})

        assert response is not None

    def test_post_request_timeout_error(self, handler, mock_session):
        """测试POST请求超时错误"""
        mock_session.post.side_effect = Timeout("请求超时")

        with pytest.raises(NetworkError):
            handler.post("http://example.com", data={"key": "value"})

    def test_retry_on_failure(self, handler, mock_session):
        """测试失败重试"""
        mock_session.get.side_effect = [Timeout("第一次失败"), Timeout("第二次失败"), Mock(status_code=200, text="成功")]

        response = handler.get("http://example.com")

        assert response is not None
        assert mock_session.get.call_count == 3

    def test_retry_exhausted(self, handler, mock_session):
        """测试重试次数耗尽"""
        mock_session.get.side_effect = Timeout("总是失败")

        with pytest.raises(NetworkError):
            handler.get("http://example.com")

        assert mock_session.get.call_count == 3

    def test_get_with_session_creation(self, mock_logger):
        """测试自动创建session"""
        import requests
        handler = RequestHandler(
            session=None,
            timeout=30,
            retry_count=3,
            logger=mock_logger
        )

        assert handler.session is not None

    def test_get_with_cookies(self, handler, mock_session, mock_response):
        """测试带cookies的请求"""
        mock_session.get.return_value = mock_response

        cookies = {"session": "test123"}
        response = handler.get("http://example.com", cookies=cookies)

        assert response is not None

    def test_get_with_proxies(self, handler, mock_session, mock_response):
        """测试带代理的请求"""
        mock_session.get.return_value = mock_response

        proxies = {"http": "http://proxy.example.com:8080"}
        response = handler.get("http://example.com", proxies=proxies)

        assert response is not None

    def test_get_with_verify_false(self, handler, mock_session, mock_response):
        """测试禁用SSL验证"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", verify=False)

        assert response is not None

    def test_get_with_allow_redirects_false(self, handler, mock_session, mock_response):
        """测试禁用重定向"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", allow_redirects=False)

        assert response is not None

    def test_get_with_stream(self, handler, mock_session, mock_response):
        """测试流式响应"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", stream=True)

        assert response is not None

    def test_get_with_params(self, handler, mock_session, mock_response):
        """测试带查询参数的请求"""
        mock_session.get.return_value = mock_response

        params = {"page": 1, "limit": 10}
        response = handler.get("http://example.com", params=params)

        assert response is not None

    def test_handle_response_encoding(self, handler, mock_session):
        """测试处理响应编码"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = "测试内容".encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com")

        assert response is not None
        assert response.encoding == "utf-8"

    def test_handle_response_without_encoding(self, handler, mock_session):
        """测试处理没有编码的响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = "test content".encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.encoding = None
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com")

        assert response is not None

    def test_get_with_retry_delay(self, handler, mock_session):
        """测试重试延迟"""
        import time
        mock_session.get.side_effect = [Timeout("第一次失败"), Mock(status_code=200, text="成功")]

        start_time = time.time()
        response = handler.get("http://example.com")
        end_time = time.time()

        assert response is not None
        assert end_time - start_time >= 1  # 至少延迟1秒

    def test_get_empty_url(self, handler):
        """测试空URL"""
        with pytest.raises(NetworkError):
            handler.get("")

    def test_get_invalid_url(self, handler):
        """测试无效URL"""
        with pytest.raises(NetworkError):
            handler.get("not-a-url")