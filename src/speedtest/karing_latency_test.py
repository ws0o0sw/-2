#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Karing延迟测试工具
基于Karing的延迟测试逻辑实现
"""

import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse


class KaringLatencyTester:
    """Karing延迟测试器"""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        # Karing测试的URL列表
        self.test_urls = [
            "https://www.google.com/generate_204",
            "https://www.cloudflare.com/",
            "https://www.apple.com/",
            "https://www.microsoft.com/",
            "https://www.baidu.com/",
            "https://www.bing.com/",
        ]

    async def test_node_latency(
        self, node_config: str, proxy: Optional[str] = None
    ) -> Dict:
        """测试单个节点的延迟"""
        try:
            # 解析节点配置
            if node_config.startswith("vmess://"):
                # 解析vmess链接
                import base64

                vmess_data = json.loads(
                    base64.b64decode(node_config[8:]).decode("utf-8")
                )
                server = vmess_data.get("add", "")
                port = vmess_data.get("port", 443)
                protocol = "vmess"
            elif node_config.startswith("vless://"):
                # 解析vless链接
                parsed = urllib.parse.urlparse(node_config)
                server = parsed.hostname
                port = parsed.port or 443
                protocol = "vless"
            elif node_config.startswith("ss://"):
                # 解析ss链接
                import base64

                ss_data = base64.b64decode(node_config[5:].split("@")[0]).decode(
                    "utf-8"
                )
                server = node_config.split("@")[1].split(":")[0]
                port = int(node_config.split(":")[-1])
                protocol = "ss"
            else:
                # 其他协议跳过
                return {
                    "config": node_config,
                    "latency": -1,
                    "error": "Unsupported protocol",
                }

            # 构建代理URL
            proxy_url = None
            if proxy:
                proxy_url = f"socks5://{proxy}"

            # 测试延迟
            latencies = []
            for test_url in self.test_urls[:2]:  # 只测试前2个URL
                try:
                    start_time = time.time()
                    async with aiohttp.ClientSession(
                        timeout=self.timeout, connector=aiohttp.TCPConnector(limit=1)
                    ) as session:
                        async with session.get(test_url, proxy=proxy_url) as response:
                            if response.status == 200 or response.status == 204:
                                latency = int((time.time() - start_time) * 1000)  # 毫秒
                                latencies.append(latency)
                except Exception as e:
                    continue

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                return {
                    "config": node_config,
                    "latency": avg_latency,
                    "protocol": protocol,
                    "server": server,
                    "port": port,
                }
            else:
                return {
                    "config": node_config,
                    "latency": -1,
                    "error": "Connection failed",
                }

        except Exception as e:
            return {"config": node_config, "latency": -1, "error": str(e)}

    async def test_nodes_batch(
        self,
        node_configs: List[str],
        proxy: Optional[str] = None,
        max_concurrent: int = 10,
    ) -> List[Dict]:
        """批量测试节点延迟"""
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def test_with_semaphore(config):
            async with semaphore:
                result = await self.test_node_latency(config, proxy)
                results.append(result)
                print(
                    f"✓ 测试完成: {result.get('server', 'Unknown')} - {result.get('latency', -1)}ms"
                )

        tasks = [test_with_semaphore(config) for config in node_configs]
        await asyncio.gather(*tasks)

        return results

    async def main(self, input_file: str, output_file: str):
        """主函数"""
        # 读取节点配置
        node_configs = []
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                config = line.strip()
                if config:
                    node_configs.append(config)

        print(f"📋 读取到 {len(node_configs)} 个节点配置")

        # 测试延迟
        print("🚀 开始Karing延迟测试...")
        results = await self.test_nodes_batch(node_configs, max_concurrent=8)

        # 过滤有效节点 (延迟 < 3000ms)
        valid_results = [
            r
            for r in results
            if r.get("latency", -1) > 0 and r.get("latency", -1) < 3000
        ]

        # 按延迟排序
        valid_results.sort(key=lambda x: x.get("latency", 9999))

        print(f"✅ 测试到 {len(valid_results)} 个有效节点")

        # 保存结果
        with open(output_file, "w", encoding="utf-8") as f:
            for result in valid_results:
                f.write(result["config"] + "\n")

        print(f"💾 结果已保存到 {output_file}")

        print(f"📊 有效节点统计:")
        for result in valid_results:
            config = result["config"]
            latency = result["latency"]
            protocol = result["protocol"]
            print(f"  {config} - {protocol} - {latency}ms")

    async def run_test(self, input_file: str, output_file: str):
        """运行测试"""
        await self.main(input_file, output_file)


# 主入口
if __name__ == "__main__":
    tester = KaringLatencyTester()

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python karing_latency_test.py <输入文件> <输出文件>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "result/karing.txt"

    # 运行测试
    asyncio.run(tester.run_test(input_file, output_file))
