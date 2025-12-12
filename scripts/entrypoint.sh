#!/bin/bash
# Entrypoint script for vLLM-Ascend container
# 容器启动入口脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  vLLM-Ascend Container Starting...${NC}"
echo -e "${GREEN}================================================${NC}"

# 设置昇腾环境变量
echo -e "${YELLOW}Setting up Ascend environment...${NC}"
if [ -f /usr/local/Ascend/ascend-toolkit/set_env.sh ]; then
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
    echo -e "${GREEN}✓ Ascend environment configured${NC}"
else
    echo -e "${RED}✗ Ascend toolkit not found!${NC}"
    exit 1
fi

# 检查NPU设备
echo -e "${YELLOW}Checking NPU devices...${NC}"
if command -v npu-smi &> /dev/null; then
    npu-smi info || echo -e "${YELLOW}Warning: npu-smi info failed, but continuing...${NC}"
else
    echo -e "${YELLOW}Warning: npu-smi command not found${NC}"
fi

# 获取运行模式
THINKING_MODE=${1:-${THINKING_MODE:-fast}}
echo -e "${GREEN}Running mode: ${THINKING_MODE}${NC}"

# 验证模式
if [[ "$THINKING_MODE" != "fast" && "$THINKING_MODE" != "slow" ]]; then
    echo -e "${RED}Invalid mode: ${THINKING_MODE}. Must be 'fast' or 'slow'${NC}"
    exit 1
fi

# 检查模型是否存在
MODEL_PATH=${MODEL_PATH:-/models/qwen3-0.6b}
echo -e "${YELLOW}Checking model path: ${MODEL_PATH}${NC}"

if [ ! -d "$MODEL_PATH" ]; then
    echo -e "${RED}✗ Model path does not exist: ${MODEL_PATH}${NC}"
    echo -e "${YELLOW}Please mount the model directory with: -v /path/to/models:/models${NC}"
    exit 1
fi

# 检查必要的模型文件
if [ ! -f "$MODEL_PATH/config.json" ]; then
    echo -e "${RED}✗ Model config.json not found in ${MODEL_PATH}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Model found at ${MODEL_PATH}${NC}"

# 设置设备ID
export ASCEND_DEVICE_ID=${ASCEND_DEVICE_ID:-0}
echo -e "${GREEN}Using NPU device: ${ASCEND_DEVICE_ID}${NC}"

# 根据模式选择配置文件
CONFIG_FILE="/workspace/config/${THINKING_MODE}_mode.yaml"
echo -e "${GREEN}Using config: ${CONFIG_FILE}${NC}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ Config file not found: ${CONFIG_FILE}${NC}"
    exit 1
fi

# 显示配置信息
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Configuration:${NC}"
cat "$CONFIG_FILE" | grep -E "max_model_len|max_num_seqs|temperature" || true
echo -e "${GREEN}================================================${NC}"

# 启动服务器
echo -e "${GREEN}Starting vLLM server...${NC}"

# 使用Python启动服务器
cd /workspace
python -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_PATH}" \
    --device npu \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len $(grep max_model_len "$CONFIG_FILE" | awk '{print $2}') \
    --max-num-seqs $(grep max_num_seqs "$CONFIG_FILE" | awk '{print $2}') \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.85 \
    --enable-prefix-caching \
    --disable-log-requests \
    "$@"
