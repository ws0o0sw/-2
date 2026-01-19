#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2RaySE网站节点收集器
使用Playwright进行浏览器自动化，收集v2rayse.com的免费节点
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Check and install playwright if not available
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            "playwright",
        ]
    )
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger


class V2RaySECollector:
    """V2RaySE网站收集器"""

    def __init__(self):
        self.logger = get_logger("v2rayse_collector")
        self.url = "https://www.v2rayse.com/free-node"
        self.result_dir = project_root / "result"
        self.result_file = self.result_dir / "v2rayse.txt"

    async def collect_nodes(self):
        """收集节点的主函数"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Set user agent to avoid blocking
                await page.set_extra_http_headers(
                    {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                )

                self.logger.info(f"访问网站: {self.url}")
                try:
                    await page.goto(
                        self.url, wait_until="domcontentloaded", timeout=60000
                    )
                except:
                    self.logger.warning("networkidle超时，使用domcontentloaded")
                    await page.goto(
                        self.url, wait_until="domcontentloaded", timeout=60000
                    )

                # 保存初始页面截图用于调试
                await page.screenshot(path="debug_initial.png")
                self.logger.info("保存初始页面截图: debug_initial.png")

                # 处理可能的广告弹窗
                try:
                    # Wait for popups to load then try to close them
                    await page.wait_for_timeout(2000)

                    # Try to close various popup types
                    popup_selectors = [
                        ".popup-close",
                        ".modal-close",
                        ".ad-close",
                        '[data-dismiss="modal"]',
                        ".close-button",
                        "#popup-close",
                    ]

                    for selector in popup_selectors:
                        try:
                            close_button = page.locator(selector).first
                            if await close_button.is_visible():
                                await close_button.click()
                                self.logger.info(f"关闭弹窗: {selector}")
                                break
                        except:
                            continue

                except Exception as e:
                    self.logger.warning(f"处理弹窗时出错: {e}")

                # 等待页面加载
                self.logger.info("等待页面加载...")
                await page.wait_for_timeout(10000)  # 直接等待10秒让页面加载

                # 尝试触发任何可能的按钮来加载节点
                try:
                    # 查找可能的加载按钮
                    load_buttons = page.locator(
                        'button:has-text("加载"), button:has-text("刷新"), button:has-text("获取"), button:has-text("开始")'
                    )
                    count = await load_buttons.count()
                    if count > 0:
                        await load_buttons.first.click()
                        self.logger.info("点击了加载按钮")
                        await page.wait_for_timeout(5000)

                except Exception as e:
                    self.logger.warning(f"尝试点击加载按钮失败: {e}")

                # 等待15秒让节点加载
                self.logger.info("等待15秒让节点加载...")
                await page.wait_for_timeout(15000)

                # 保存等待后的页面截图
                await page.screenshot(path="debug_after_wait.png")
                self.logger.info("保存等待后页面截图: debug_after_wait.png")

                # 保存页面HTML内容用于分析
                page_html = await page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page_html)
                self.logger.info("保存页面HTML: debug_page.html")

                # 也保存页面文本内容
                page_text = await page.inner_text("body")
                with open("debug_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(page_text)
                self.logger.info("保存页面文本: debug_page_text.txt")

                # 查找表头的全选复选框
                try:
                    # 表头的全选复选框通常在th元素中
                    select_all_selectors = [
                        'th input[type="checkbox"]',
                        'thead input[type="checkbox"]',
                        '.table-header input[type="checkbox"]',
                        '#table-header input[type="checkbox"]',
                        'input[type="checkbox"][data-select-all]',
                    ]

                    select_all_clicked = False
                    for selector in select_all_selectors:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                await element.check()
                                self.logger.info(f"勾选表头全选复选框: {selector}")
                                select_all_clicked = True
                                break
                        except Exception as e:
                            self.logger.debug(f"尝试 {selector} 失败: {e}")
                            continue

                    if not select_all_clicked:
                        # 如果没找到表头复选框，尝试查找页面中的所有复选框，第一个通常是全选
                        all_checkboxes = page.locator('input[type="checkbox"]')
                        count = await all_checkboxes.count()
                        if count > 0:
                            try:
                                await all_checkboxes.first.check()
                                self.logger.info("勾选第一个复选框（可能是全选）")
                                select_all_clicked = True
                            except Exception as e:
                                self.logger.warning(f"勾选第一个复选框失败: {e}")
                        else:
                            self.logger.warning("未找到任何复选框")

                except Exception as e:
                    self.logger.error(f"选择节点时出错: {e}")

                # 查找节点操作按钮并悬浮触发菜单
                try:
                    # 查找操作按钮（可能是"操作"列或特定的操作按钮）
                    operation_selectors = [
                        'button:contains("操作")',
                        ".operation-btn",
                        "#operation-btn",
                        "[data-operation]",
                        'button:has-text("操作")',
                    ]

                    operation_found = False
                    for selector in operation_selectors:
                        try:
                            operation_btn = page.locator(selector).first
                            if await operation_btn.is_visible():
                                # 查找转换选项 - 尝试多种选择器
                                convert_selectors = [
                                    'button:contains("转换")',
                                    'a:contains("转换")',
                                    '[data-action="convert"]',
                                    ".convert-option",
                                    'button:contains("V2RAY")',
                                    'button:contains("转V2RAY")',
                                    'button:contains("导出")',
                                    'a:contains("导出")',
                                    '[data-format="v2ray"]',
                                    '.menu-item:contains("转换")',
                                    '.dropdown-item:contains("转换")',
                                    'button:contains("复制")',
                                    'a:contains("复制")',
                                    ".copy-option",
                                    '[data-action="copy"]',
                                ]

                                # 先悬浮到操作按钮
                                await operation_btn.hover()
                                self.logger.info(f"悬浮到操作按钮: {selector}")
                                await page.wait_for_timeout(1000)  # 等待菜单显示

                                # 如果悬浮后没有找到转换选项，尝试点击操作按钮
                                convert_found = False
                                for convert_selector in convert_selectors[
                                    :3
                                ]:  # 先检查前3个选择器
                                    try:
                                        convert_btn = page.locator(
                                            convert_selector
                                        ).first
                                        if await convert_btn.is_visible():
                                            await convert_btn.click()
                                            self.logger.info(
                                                f"点击转换选项: {convert_selector}"
                                            )
                                            convert_found = True
                                            operation_found = True
                                            break
                                    except Exception as e:
                                        self.logger.debug(
                                            f"尝试 {convert_selector} 失败: {e}"
                                        )
                                        continue

                                if not convert_found:
                                    # 尝试点击操作按钮
                                    try:
                                        await operation_btn.click()
                                        self.logger.info("点击操作按钮")
                                        await page.wait_for_timeout(
                                            1000
                                        )  # 等待菜单显示

                                        # 保存点击后的截图
                                        await page.screenshot(path="debug_click.png")
                                        self.logger.info(
                                            "保存点击后页面截图: debug_click.png"
                                        )

                                        # 查找选中操作菜单项
                                        select_menu_selectors = [
                                            'button:contains("选中")',
                                            'a:contains("选中")',
                                            '[data-action="select"]',
                                            ".select-menu",
                                            ".select-option",
                                        ]

                                        select_menu_found = False
                                        for select_selector in select_menu_selectors:
                                            try:
                                                select_menu = page.locator(
                                                    select_selector
                                                ).first
                                                if await select_menu.is_visible():
                                                    # 悬浮到选中菜单
                                                    await select_menu.hover()
                                                    self.logger.info(
                                                        f"悬浮到选中菜单: {select_selector}"
                                                    )
                                                    await page.wait_for_timeout(
                                                        1000
                                                    )  # 等待子菜单显示

                                                    # 保存选中菜单悬浮后的截图
                                                    await page.screenshot(
                                                        path="debug_select_hover.png"
                                                    )
                                                    self.logger.info(
                                                        "保存选中菜单悬浮后截图: debug_select_hover.png"
                                                    )

                                                    select_menu_found = True
                                                    break
                                            except Exception as e:
                                                self.logger.debug(
                                                    f"查找选中菜单 {select_selector} 失败: {e}"
                                                )
                                                continue

                                        if not select_menu_found:
                                            self.logger.warning("未找到选中菜单")

                                        # 再次查找转换选项
                                        for convert_selector in convert_selectors:
                                            try:
                                                convert_btn = page.locator(
                                                    convert_selector
                                                ).first
                                                if await convert_btn.is_visible():
                                                    await convert_btn.click()
                                                    self.logger.info(
                                                        f"点击转换选项: {convert_selector}"
                                                    )
                                                    operation_found = True
                                                    break
                                            except Exception as e:
                                                self.logger.debug(
                                                    f"尝试 {convert_selector} 失败: {e}"
                                                )
                                                continue

                                    except Exception as e:
                                        self.logger.warning(f"点击操作按钮失败: {e}")

                                # 保存悬浮后的截图（无论是否点击）
                                await page.screenshot(path="debug_hover.png")
                                self.logger.info("保存悬浮后页面截图: debug_hover.png")

                                # 也查找所有可见的按钮，看看有哪些
                                all_visible_buttons = page.locator(
                                    "button:visible, a:visible"
                                )
                                button_count = await all_visible_buttons.count()
                                self.logger.info(
                                    f"找到 {button_count} 个可见的按钮/链接"
                                )

                                for i in range(min(button_count, 20)):  # 检查前20个
                                    try:
                                        btn_text = await all_visible_buttons.nth(
                                            i
                                        ).text_content()
                                        if btn_text:
                                            self.logger.info(
                                                f"按钮 {i}: '{btn_text.strip()}'"
                                            )
                                            if (
                                                "转换" in btn_text
                                                or "V2RAY" in btn_text
                                                or "导出" in btn_text
                                                or "复制" in btn_text
                                                or "选中" in btn_text
                                            ):
                                                self.logger.info(
                                                    f"找到可能的操作按钮: '{btn_text}'"
                                                )
                                    except Exception as e:
                                        self.logger.debug(f"获取按钮 {i} 文本失败: {e}")
                                        continue

                                for convert_selector in convert_selectors:
                                    try:
                                        convert_btn = page.locator(
                                            convert_selector
                                        ).first
                                        if await convert_btn.is_visible():
                                            await convert_btn.click()
                                            self.logger.info(
                                                f"点击转换选项: {convert_selector}"
                                            )
                                            operation_found = True
                                            break
                                    except Exception as e:
                                        self.logger.debug(
                                            f"尝试 {convert_selector} 失败: {e}"
                                        )
                                        continue

                                if operation_found:
                                    break

                        except Exception as e:
                            self.logger.debug(f"尝试 {selector} 失败: {e}")
                            continue

                    if not operation_found:
                        self.logger.warning("未找到节点操作按钮或转换选项")

                except Exception as e:
                    self.logger.error(f"转换格式时出错: {e}")

                # 等待转换完成
                await page.wait_for_timeout(3000)

                # 提取V2RAY节点数据
                v2ray_content = ""

                try:
                    # 首先尝试从文本区域或结果区域提取
                    content_selectors = [
                        "textarea",
                        "#result",
                        ".result",
                        "#v2ray-content",
                        ".v2ray-content",
                        "pre",
                        ".node-content",
                        "#node-content",
                    ]

                    for selector in content_selectors:
                        try:
                            content_element = page.locator(selector).first
                            if await content_element.is_visible():
                                v2ray_content = await content_element.text_content()
                                if v2ray_content:
                                    self.logger.info(
                                        f"从 {selector} 提取到内容: '{v2ray_content[:100]}...'"
                                    )
                                    if v2ray_content.strip():
                                        break
                                else:
                                    self.logger.info(f"从 {selector} 提取到空内容")
                        except:
                            continue

                    if not v2ray_content:
                        # 如果没找到特定区域，尝试从页面源码中提取节点配置
                        page_content = await page.content()
                        self.logger.info("从页面源码提取节点配置")

                        # 查找可能的节点配置模式
                        import re

                        # 提取各种类型的节点链接
                        node_patterns = [
                            r'vmess://[^\s"<]+',
                            r'vless://[^\s"<]+',
                            r'trojan://[^\s"<]+',
                            r'ss://[^\s"<]+',
                            r'ssr://[^\s"<]+',
                            r'hysteria://[^\s"<]+',
                        ]

                        all_links = []
                        for pattern in node_patterns:
                            links = re.findall(pattern, page_content)
                            all_links.extend(links)

                        if all_links:
                            v2ray_content = "\n".join(all_links)
                            self.logger.info(
                                f"从源码提取到 {len(all_links)} 个节点链接"
                            )
                        else:
                            # 如果还是没找到，尝试解析表格数据生成配置
                            self.logger.info("尝试解析表格数据生成节点配置")

                            # 从页面文本中提取节点信息
                            page_text = await page.inner_text("body")

                            # 解析节点表格 - 改进的解析逻辑
                            # 从页面文本中提取节点信息
                            lines = [
                                line.strip()
                                for line in page_text.split("\n")
                                if line.strip()
                            ]

                            # 查找节点数据的模式
                            # 典型的格式：🇺🇸_US_美国 vless v2.dabache.top 443 操作
                            nodes = []
                            i = 0
                            while i < len(lines):
                                line = lines[i]

                                # 查找以国旗开头的行（节点名称）
                                if (
                                    line.startswith("🇺🇸")
                                    or line.startswith("🇩🇪")
                                    or line.startswith("🇬🇧")
                                    or line.startswith("🇷🇺")
                                    or line.startswith("🇮🇹")
                                    or line.startswith("🇮🇶")
                                    or line.startswith("🇳🇱")
                                    or line.startswith("🇪🇸")
                                    or line.startswith("🇨🇦")
                                    or line.startswith("🇩🇰")
                                    or line.startswith("🇯🇵")
                                    or line.startswith("🇰🇷")
                                    or line.startswith("🇦🇺")
                                    or line.startswith("🇸🇬")
                                    or line.startswith("🇭🇰")
                                ):
                                    # 这是一个节点名称，接下来应该有类型、服务器、端口
                                    node_name = line

                                    # 查找下一行
                                    if i + 1 < len(lines):
                                        next_line = lines[i + 1]
                                        if next_line in [
                                            "vless",
                                            "vmess",
                                            "trojan",
                                            "ss",
                                            "ssr",
                                            "hysteria",
                                        ]:
                                            node_type = next_line

                                            # 查找服务器（通常是下一行）
                                            if i + 2 < len(lines):
                                                server_line = lines[i + 2]
                                                if (
                                                    "." in server_line
                                                    or ":" in server_line
                                                ):
                                                    server = server_line

                                                    # 查找端口（通常是下一行）
                                                    if i + 3 < len(lines):
                                                        port_line = lines[i + 3]
                                                        if port_line.isdigit():
                                                            port = port_line

                                                            nodes.append(
                                                                {
                                                                    "name": node_name,
                                                                    "type": node_type,
                                                                    "server": server,
                                                                    "port": port,
                                                                }
                                                            )

                                                            self.logger.info(
                                                                f"解析到节点: {node_name} {node_type} {server}:{port}"
                                                            )
                                                            i += 4  # 跳过已处理的行
                                                            continue

                                i += 1

                            # 生成V2RAY格式配置
                            if nodes:
                                v2ray_configs = []
                                for node in nodes:
                                    if (
                                        node.get("type")
                                        and node.get("server")
                                        and node.get("port")
                                    ):
                                        if node["type"] == "vless":
                                            config = f"vless://{node['server']}:{node['port']}?type=tcp&security=none#{node.get('name', 'Unknown')}"
                                        elif node["type"] == "vmess":
                                            # vmess需要更多参数，这里简化
                                            config = f"vmess://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"
                                        elif node["type"] == "ss":
                                            config = f"ss://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"
                                        else:
                                            config = f"{node['type']}://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"

                                        v2ray_configs.append(config)

                                if v2ray_configs:
                                    v2ray_content = "\n".join(v2ray_configs)
                                    self.logger.info(
                                        f"从表格解析生成 {len(v2ray_configs)} 个节点配置"
                                    )

                except Exception as e:
                    self.logger.error(f"提取内容时出错: {e}")

                # 关闭浏览器
                await browser.close()

                if v2ray_content:
                    # 确保结果目录存在
                    self.result_dir.mkdir(exist_ok=True)

                    # 保存到文件
                    with open(self.result_file, "w", encoding="utf-8") as f:
                        f.write(v2ray_content.strip())

                    self.logger.info(
                        f"成功保存 {len(v2ray_content.splitlines())} 个节点到 {self.result_file}"
                    )
                    return True
                else:
                    self.logger.error("未获取到任何节点内容")
                    return False

        except Exception as e:
            self.logger.error(f"收集过程出错: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """主函数"""
    collector = V2RaySECollector()
    success = await collector.collect_nodes()

    if success:
        print("✅ V2RaySE节点收集完成")
        sys.exit(0)
    else:
        print("❌ V2RaySE节点收集失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
