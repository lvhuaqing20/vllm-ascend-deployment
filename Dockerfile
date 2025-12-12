# vLLM-Ascend Dockerfile
# 基于昇腾CANN环境构建vLLM推理服务

# 使用昇腾官方基础镜像
FROM cosdt/cann:8.2.rc1-pytorch-2.1.0-py3.9-ubuntu22.04

# 设置维护者信息
LABEL maintainer="your.email@example.com"
LABEL description="vLLM-Ascend inference server for Qwen3 models"
LABEL version="0.1"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV ASCEND_HOME=/usr/local/Ascend
ENV LD_LIBRARY_PATH=${ASCEND_HOME}/driver/lib64:${LD_LIBRARY_PATH}

# 设置工作目录
WORKDIR /workspace

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    cmake \
    build-essential \
    ninja-build \
    wget \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制requirements文件
COPY requirements.txt /workspace/

# 安装Python依赖
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 克隆vllm-ascend源码
RUN git clone https://github.com/PannenetsF/vllm.git -b ascend_develop /workspace/vllm-ascend

# 安装vllm依赖
WORKDIR /workspace/vllm-ascend
RUN pip install --no-cache-dir -r requirements-npu.txt

# 编译安装vllm-ascend
RUN VLLM_TARGET_DEVICE=npu python setup.py install

# 创建模型目录
RUN mkdir -p /models

# 复制配置文件
COPY config/ /workspace/config/

# 复制源代码
COPY src/ /workspace/src/

# 复制启动脚本
COPY scripts/entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/entrypoint.sh

# 设置Python路径
ENV PYTHONPATH=/workspace/src:${PYTHONPATH}

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置工作目录
WORKDIR /workspace

# 容器启动命令
ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD ["fast"]
