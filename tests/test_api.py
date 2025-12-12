#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Tests for vLLM-Ascend
API接口测试
"""

import pytest
import requests
import time
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 30


class TestVLLMAPI:
    """vLLM API测试类"""
    
    @pytest.fixture(scope="class")
    def api_base(self):
        """获取API基础URL"""
        return BASE_URL
    
    def test_health_check(self, api_base):
        """测试健康检查端点"""
        url = f"{api_base}/health"
        response = requests.get(url, timeout=5)
        
        assert response.status_code == 200
        print(f"✓ Health check passed")
    
    def test_get_models(self, api_base):
        """测试获取模型列表"""
        url = f"{api_base}/v1/models"
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        
        print(f"✓ Available models: {len(data['data'])}")
        for model in data["data"]:
            print(f"  - {model['id']}")
    
    def test_simple_completion(self, api_base):
        """测试简单文本生成"""
        url = f"{api_base}/v1/completions"
        
        payload = {
            "model": "/models/qwen3-0.6b",
            "prompt": "什么是人工智能？",
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        latency = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "text" in data["choices"][0]
        
        generated_text = data["choices"][0]["text"]
        assert len(generated_text) > 0
        
        print(f"✓ Simple completion test passed")
        print(f"  Latency: {latency:.3f}s")
        print(f"  Generated text: {generated_text[:100]}...")
    
    def test_temperature_effect(self, api_base):
        """测试temperature参数效果"""
        url = f"{api_base}/v1/completions"
        
        prompt = "人工智能的未来发展方向是："
        
        # 低temperature（更确定性）
        payload_low = {
            "model": "/models/qwen3-0.6b",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        # 高temperature（更随机）
        payload_high = {
            "model": "/models/qwen3-0.6b",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 1.0
        }
        
        response_low = requests.post(url, json=payload_low, timeout=TIMEOUT)
        response_high = requests.post(url, json=payload_high, timeout=TIMEOUT)
        
        assert response_low.status_code == 200
        assert response_high.status_code == 200
        
        text_low = response_low.json()["choices"][0]["text"]
        text_high = response_high.json()["choices"][0]["text"]
        
        print(f"✓ Temperature effect test passed")
        print(f"  Low temp (0.1): {text_low[:50]}...")
        print(f"  High temp (1.0): {text_high[:50]}...")


class TestErrorHandling:
    """错误处理测试类"""
    
    @pytest.fixture(scope="class")
    def api_base(self):
        return BASE_URL
    
    def test_invalid_model(self, api_base):
        """测试无效的模型名称"""
        url = f"{api_base}/v1/completions"
        
        payload = {
            "model": "/invalid/model/path",
            "prompt": "测试",
            "max_tokens": 10
        }
        
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        
        # 应该返回错误
        assert response.status_code in [400, 404, 500]
        print(f"✓ Invalid model test passed (status: {response.status_code})")
    
    def test_missing_required_fields(self, api_base):
        """测试缺少必需字段"""
        url = f"{api_base}/v1/completions"
        
        # 缺少prompt字段
        payload = {
            "model": "/models/qwen3-0.6b",
            "max_tokens": 10
        }
        
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        
        assert response.status_code == 400
        print(f"✓ Missing required fields test passed")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
