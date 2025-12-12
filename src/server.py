#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vLLM-Ascend Server
主服务器程序
"""

import os
import sys
import argparse
import logging
from typing import Optional

# 添加vLLM路径
sys.path.insert(0, '/workspace/vllm-ascend')

from utils import (
    load_config,
    get_config_path,
    setup_ascend_env,
    check_npu_available,
    validate_model_path,
    parse_thinking_mode,
    ConfigValidator
)

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class VLLMServer:
    """vLLM-Ascend服务器类"""
    
    def __init__(self, mode: str = "fast", config_path: Optional[str] = None):
        """
        初始化服务器
        
        Args:
            mode: 运行模式 ("fast" 或 "slow")
            config_path: 自定义配置文件路径
        """
        self.mode = parse_thinking_mode(mode)
        
        # 加载配置
        if config_path is None:
            config_path = get_config_path(self.mode)
        
        self.config = load_config(config_path)
        
        # 验证配置
        validator = ConfigValidator()
        if not validator.validate(self.config):
            raise ValueError("Invalid configuration")
        
        # 提取配置
        self.model_config = self.config['model']
        self.inference_config = self.config['inference']
        self.generation_config = self.config['generation']
        self.server_config = self.config['server']
        
        logger.info(f"VLLMServer initialized in {self.mode} mode")
    
    def setup_environment(self) -> None:
        """设置运行环境"""
        logger.info("Setting up environment...")
        
        # 设置昇腾环境
        setup_ascend_env()
        
        # 检查NPU
        if not check_npu_available():
            raise RuntimeError("NPU is not available")
        
        # 设置设备ID
        device_id = self.inference_config.get('device_id', 0)
        os.environ['ASCEND_DEVICE_ID'] = str(device_id)
        logger.info(f"Using NPU device: {device_id}")
        
        # 验证模型路径
        model_path = self.model_config['path']
        if not validate_model_path(model_path):
            raise ValueError(f"Invalid model path: {model_path}")
    
    def build_vllm_args(self) -> list:
        """
        构建vLLM命令行参数
        
        Returns:
            参数列表
        """
        args = []
        
        # 模型参数
        args.extend(['--model', self.model_config['path']])
        
        # 设备配置
        args.extend(['--device', self.inference_config['device']])
        
        # 序列长度
        if 'max_model_len' in self.inference_config:
            args.extend(['--max-model-len', str(self.inference_config['max_model_len'])])
        
        # 并发配置
        if 'max_num_seqs' in self.inference_config:
            args.extend(['--max-num-seqs', str(self.inference_config['max_num_seqs'])])
        
        # 数据类型
        if 'dtype' in self.model_config:
            args.extend(['--dtype', self.model_config['dtype']])
        
        # 内存配置
        if 'gpu_memory_utilization' in self.inference_config:
            args.extend(['--gpu-memory-utilization', str(self.inference_config['gpu_memory_utilization'])])
        
        # 张量并行
        if 'tensor_parallel_size' in self.inference_config:
            args.extend(['--tensor-parallel-size', str(self.inference_config['tensor_parallel_size'])])
        
        # KV Cache优化
        if self.inference_config.get('enable_prefix_caching', False):
            args.append('--enable-prefix-caching')
        
        # 日志配置
        if self.inference_config.get('disable_log_requests', False):
            args.append('--disable-log-requests')
        
        # 服务器配置
        args.extend(['--host', self.server_config['host']])
        args.extend(['--port', str(self.server_config['port'])])
        
        logger.info(f"vLLM args: {' '.join(args)}")
        return args
    
    def start(self) -> None:
        """启动服务器"""
        try:
            # 设置环境
            self.setup_environment()
            
            # 构建参数
            vllm_args = self.build_vllm_args()
            
            logger.info(f"Starting vLLM server in {self.mode} mode...")
            logger.info(f"Model: {self.model_config['name']}")
            logger.info(f"Max sequence length: {self.inference_config['max_model_len']}")
            logger.info(f"Max concurrent sequences: {self.inference_config['max_num_seqs']}")
            logger.info(f"Server listening on {self.server_config['host']}:{self.server_config['port']}")
            
            # 启动服务器
            os.system(f"python -m vllm.entrypoints.openai.api_server {' '.join(vllm_args)}")
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='vLLM-Ascend Server')
    
    parser.add_argument(
        '--mode',
        type=str,
        default='fast',
        choices=['fast', 'slow'],
        help='Thinking mode: fast or slow (default: fast)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to custom configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 创建并启动服务器
    try:
        server = VLLMServer(mode=args.mode, config_path=args.config)
        server.start()
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
