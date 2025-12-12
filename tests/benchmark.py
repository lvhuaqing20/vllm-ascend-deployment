#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Benchmark for vLLM-Ascend
性能基准测试
"""

import argparse
import time
import statistics
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# 配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 60


class BenchmarkRunner:
    """性能测试运行器"""
    
    def __init__(self, api_url: str = BASE_URL):
        self.api_url = api_url
        self.completion_url = f"{api_url}/v1/completions"
    
    def single_request(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        发送单个请求并测量性能
        
        Returns:
            包含延迟、tokens等信息的字典
        """
        payload = {
            "model": "/models/qwen3-0.6b",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        start_time = time.time()
        try:
            response = requests.post(self.completion_url, json=payload, timeout=TIMEOUT)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data["choices"][0]["text"]
                
                return {
                    "success": True,
                    "latency": latency,
                    "generated_tokens": len(generated_text.split()),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "latency": latency,
                    "error": f"HTTP {response.status_code}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "latency": time.time() - start_time,
                "error": str(e),
                "status_code": None
            }
    
    def benchmark_throughput(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        num_requests: int,
        concurrency: int
    ) -> Dict[str, Any]:
        """
        吞吐量基准测试
        """
        print(f"\n{'='*60}")
        print(f"Running throughput benchmark...")
        print(f"  Total requests: {num_requests}")
        print(f"  Concurrency: {concurrency}")
        print(f"  Max tokens: {max_tokens}")
        print(f"{'='*60}\n")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(
                    self.single_request,
                    prompt,
                    max_tokens,
                    temperature
                )
                futures.append(future)
            
            # 收集结果并显示进度
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                if completed % 10 == 0 or completed == num_requests:
                    print(f"Progress: {completed}/{num_requests} requests completed")
        
        # 统计分析
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        if not successful_results:
            print("\n❌ All requests failed!")
            return {"error": "All requests failed"}
        
        latencies = [r["latency"] for r in successful_results]
        total_tokens = sum(r.get("generated_tokens", 0) for r in successful_results)
        
        stats = {
            "total_requests": num_requests,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / num_requests * 100,
            "total_time": max(latencies),
            "throughput": len(successful_results) / max(latencies) if latencies else 0,
            "latency": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "std": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "min": min(latencies),
                "max": max(latencies),
                "p50": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            },
            "tokens": {
                "total": total_tokens,
                "per_request": total_tokens / len(successful_results) if successful_results else 0
            }
        }
        
        return stats
    
    def print_results(self, stats: Dict[str, Any]) -> None:
        """打印测试结果"""
        if "error" in stats:
            return
        
        print(f"\n{'='*60}")
        print(f"Benchmark Results")
        print(f"{'='*60}")
        print(f"\n📊 Request Statistics:")
        print(f"  Total requests:      {stats['total_requests']}")
        print(f"  Successful:          {stats['successful_requests']}")
        print(f"  Failed:              {stats['failed_requests']}")
        print(f"  Success rate:        {stats['success_rate']:.2f}%")
        
        print(f"\n⚡ Performance Metrics:")
        print(f"  Throughput:          {stats['throughput']:.2f} req/s")
        print(f"  Total time:          {stats['total_time']:.2f}s")
        
        print(f"\n⏱️  Latency Statistics (seconds):")
        print(f"  Mean:                {stats['latency']['mean']:.3f}s")
        print(f"  Median:              {stats['latency']['median']:.3f}s")
        print(f"  Std Dev:             {stats['latency']['std']:.3f}s")
        print(f"  Min:                 {stats['latency']['min']:.3f}s")
        print(f"  Max:                 {stats['latency']['max']:.3f}s")
        print(f"  P50:                 {stats['latency']['p50']:.3f}s")
        print(f"  P95:                 {stats['latency']['p95']:.3f}s")
        print(f"  P99:                 {stats['latency']['p99']:.3f}s")
        
        print(f"\n🎯 Token Statistics:")
        print(f"  Total tokens:        {stats['tokens']['total']}")
        print(f"  Tokens per request:  {stats['tokens']['per_request']:.1f}")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='vLLM-Ascend Performance Benchmark')
    
    parser.add_argument(
        '--url',
        type=str,
        default=BASE_URL,
        help='API base URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='fast',
        choices=['fast', 'slow', 'both'],
        help='Test mode: fast, slow, or both (default: fast)'
    )
    
    parser.add_argument(
        '--requests',
        type=int,
        default=100,
        help='Number of requests (default: 100)'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=10,
        help='Concurrency level (default: 10)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (optional)'
    )
    
    args = parser.parse_args()
    
    runner = BenchmarkRunner(api_url=args.url)
    
    # 测试场景配置
    scenarios = {
        'fast': {
            'prompt': '什么是人工智能？请简要回答。',
            'max_tokens': 50,
            'temperature': 0.7
        },
        'slow': {
            'prompt': '详细解释深度学习的工作原理，包括神经网络、反向传播和梯度下降等核心概念：',
            'max_tokens': 500,
            'temperature': 0.3
        }
    }
    
    all_results = {}
    
    # 运行测试
    modes_to_test = ['fast', 'slow'] if args.mode == 'both' else [args.mode]
    
    for mode in modes_to_test:
        print(f"\n🚀 Testing {mode.upper()} mode...")
        
        scenario = scenarios[mode]
        stats = runner.benchmark_throughput(
            prompt=scenario['prompt'],
            max_tokens=scenario['max_tokens'],
            temperature=scenario['temperature'],
            num_requests=args.requests,
            concurrency=args.concurrency
        )
        
        runner.print_results(stats)
        all_results[mode] = stats
    
    # 保存结果到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {args.output}")


if __name__ == "__main__":
    main()
