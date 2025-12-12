#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for vLLM-Ascend deployment
工具函数模块
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Successfully loaded config from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        raise


def get_config_path(mode: str = "fast") -> str:
    """
    获取配置文件路径
    
    Args:
        mode: 运行模式 ("fast" 或 "slow")
        
    Returns:
        配置文件的绝对路径
    """
    base_dir = Path(__file__).parent.parent
    config_file = f"{mode}_mode.yaml"
    config_path = base_dir / "config" / config_file
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    return str(config_path)


def setup_ascend_env() -> None:
    """
    设置昇腾环境变量
    """
    ascend_home = os.environ.get('ASCEND_HOME', '/usr/local/Ascend')
    
    # 设置关键环境变量
    env_vars = {
        'ASCEND_HOME': ascend_home,
        'LD_LIBRARY_PATH': f"{ascend_home}/driver/lib64:{os.environ.get('LD_LIBRARY_PATH', '')}",
        'PYTHONPATH': f"{ascend_home}/python/site-packages:{os.environ.get('PYTHONPATH', '')}",
        'PATH': f"{ascend_home}/bin:{os.environ.get('PATH', '')}",
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.debug(f"Set {key}={value}")
    
    logger.info("Ascend environment variables configured")


def check_npu_available() -> bool:
    """
    检查NPU设备是否可用
    
    Returns:
        True if NPU is available, False otherwise
    """
    try:
        import torch_npu
        if torch_npu.npu.is_available():
            device_count = torch_npu.npu.device_count()
            logger.info(f"NPU is available, device count: {device_count}")
            return True
        else:
            logger.warning("NPU is not available")
            return False
    except ImportError:
        logger.error("torch_npu is not installed")
        return False
    except Exception as e:
        logger.error(f"Error checking NPU availability: {e}")
        return False


def validate_model_path(model_path: str) -> bool:
    """
    验证模型路径是否有效
    
    Args:
        model_path: 模型路径
        
    Returns:
        True if valid, False otherwise
    """
    model_path = Path(model_path)
    
    if not model_path.exists():
        logger.error(f"Model path does not exist: {model_path}")
        return False
    
    # 检查必要的模型文件
    required_files = ['config.json', 'tokenizer_config.json']
    for file in required_files:
        if not (model_path / file).exists():
            logger.warning(f"Missing model file: {file}")
    
    # 检查模型权重文件
    weight_files = list(model_path.glob('*.bin')) + list(model_path.glob('*.safetensors'))
    if not weight_files:
        logger.error("No model weight files found")
        return False
    
    logger.info(f"Model path validated: {model_path}")
    return True


def parse_thinking_mode(mode: Optional[str]) -> str:
    """
    解析思考模式参数
    
    Args:
        mode: 模式字符串
        
    Returns:
        标准化的模式字符串 ("fast" 或 "slow")
    """
    if mode is None:
        mode = os.environ.get('THINKING_MODE', 'fast')
    
    mode = mode.lower().strip()
    
    if mode not in ['fast', 'slow']:
        logger.warning(f"Invalid thinking mode: {mode}, defaulting to 'fast'")
        return 'fast'
    
    return mode


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """
        验证配置的完整性和合法性
        
        Args:
            config: 配置字典
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # 检查必要的顶级键
            required_keys = ['model', 'inference', 'generation', 'server']
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing required config key: {key}")
                    return False
            
            # 验证模型配置
            model_config = config['model']
            if 'path' not in model_config:
                logger.error("Missing model path in config")
                return False
            
            # 验证推理配置
            inference_config = config['inference']
            if inference_config.get('max_model_len', 0) <= 0:
                logger.error("Invalid max_model_len")
                return False
            
            if inference_config.get('max_num_seqs', 0) <= 0:
                logger.error("Invalid max_num_seqs")
                return False
            
            # 验证服务器配置
            server_config = config['server']
            if server_config.get('port', 0) <= 0 or server_config.get('port', 0) > 65535:
                logger.error("Invalid server port")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False


if __name__ == "__main__":
    # 测试工具函数
    print("Testing utility functions...")
    
    # 测试环境设置
    setup_ascend_env()
    
    # 测试NPU检查
    npu_available = check_npu_available()
    print(f"NPU available: {npu_available}")
