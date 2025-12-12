#!/bin/bash
# Run script for vLLM-Ascend Docker container
# Docker容器运行脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
IMAGE_NAME=${IMAGE_NAME:-"vllm-ascend"}
IMAGE_TAG=${IMAGE_TAG:-"v0.1"}
CONTAINER_NAME_PREFIX=${CONTAINER_NAME_PREFIX:-"vllm"}
MODEL_PATH=${MODEL_PATH:-"$(pwd)/models"}
PORT=${PORT:-8000}

# 获取运行模式
MODE=${1:-"fast"}

# 验证模式
if [[ "$MODE" != "fast" && "$MODE" != "slow" ]]; then
    echo -e "${RED}Error: Invalid mode '${MODE}'. Must be 'fast' or 'slow'${NC}"
    echo "Usage: $0 [fast|slow]"
    exit 1
fi

CONTAINER_NAME="${CONTAINER_NAME_PREFIX}-${MODE}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Starting vLLM-Ascend Container${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Mode: ${MODE}${NC}"
echo -e "${GREEN}Container name: ${CONTAINER_NAME}${NC}"
echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}${NC}"
echo -e "${GREEN}Port: ${PORT}${NC}"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# 检查镜像是否存在
if ! docker image inspect "${FULL_IMAGE_NAME}" &> /dev/null; then
    echo -e "${RED}Error: Image ${FULL_IMAGE_NAME} not found${NC}"
    echo -e "${YELLOW}Please build the image first: ./scripts/build.sh${NC}"
    exit 1
fi

# 检查模型路径
if [ ! -d "$MODEL_PATH" ]; then
    echo -e "${YELLOW}Warning: Model path does not exist: ${MODEL_PATH}${NC}"
    echo -e "${YELLOW}Creating directory...${NC}"
    mkdir -p "$MODEL_PATH"
    echo -e "${YELLOW}Please download the model to: ${MODEL_PATH}/qwen3-0.6b${NC}"
    echo -e "${YELLOW}Example: huggingface-cli download Qwen/Qwen3-0.6B --local-dir ${MODEL_PATH}/qwen3-0.6b${NC}"
fi

# 检查是否已有同名容器运行
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Container ${CONTAINER_NAME} already exists${NC}"
    read -p "Do you want to remove it and start a new one? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Stopping and removing existing container...${NC}"
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    else
        echo -e "${YELLOW}Exiting...${NC}"
        exit 0
    fi
fi

# 启动容器
echo -e "${GREEN}Starting container...${NC}"
echo ""

docker run -d \
    --name "${CONTAINER_NAME}" \
    --device=/dev/davinci0 \
    --device=/dev/davinci_manager \
    --device=/dev/devmm_svm \
    --device=/dev/hisi_hdc \
    -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
    -v "${MODEL_PATH}:/models:ro" \
    -e THINKING_MODE="${MODE}" \
    -e ASCEND_DEVICE_ID=0 \
    -p "${PORT}:8000" \
    --restart unless-stopped \
    --shm-size=16g \
    "${FULL_IMAGE_NAME}" \
    "${MODE}"

# 检查容器是否成功启动
sleep 2
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  Container started successfully!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Container name: ${CONTAINER_NAME}${NC}"
    echo -e "${GREEN}Mode: ${MODE}${NC}"
    echo -e "${GREEN}API endpoint: http://localhost:${PORT}${NC}"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo -e "  View logs:        ${GREEN}docker logs -f ${CONTAINER_NAME}${NC}"
    echo -e "  Stop container:   ${GREEN}docker stop ${CONTAINER_NAME}${NC}"
    echo -e "  Remove container: ${GREEN}docker rm ${CONTAINER_NAME}${NC}"
    echo -e "  Shell access:     ${GREEN}docker exec -it ${CONTAINER_NAME} bash${NC}"
    echo ""
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    echo -e "${YELLOW}You can check logs with: docker logs -f ${CONTAINER_NAME}${NC}"
    
    # 显示实时日志（可选）
    echo ""
    read -p "Do you want to see container logs? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker logs -f "${CONTAINER_NAME}"
    fi
else
    echo ""
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  Container failed to start!${NC}"
    echo -e "${RED}================================================${NC}"
    echo -e "${YELLOW}Check logs with: docker logs ${CONTAINER_NAME}${NC}"
    exit 1
fi
