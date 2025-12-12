#!/bin/bash
# Build script for vLLM-Ascend Docker image
# Docker镜像构建脚本

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
REGISTRY=${REGISTRY:-""}

FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${FULL_IMAGE_NAME}"
fi

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Building vLLM-Ascend Docker Image${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Image name: ${FULL_IMAGE_NAME}${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# 检查Dockerfile是否存在
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found in current directory${NC}"
    exit 1
fi

# 显示构建信息
echo -e "${YELLOW}Build configuration:${NC}"
echo -e "  Image: ${FULL_IMAGE_NAME}"
echo -e "  Docker version: $(docker --version)"
echo -e "  Build context: $(pwd)"
echo ""

# 确认构建
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Build cancelled${NC}"
    exit 0
fi

# 开始构建
echo -e "${GREEN}Starting build...${NC}"
echo ""

# 构建镜像
docker build \
    --tag "${FULL_IMAGE_NAME}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    . 2>&1 | tee build.log

# 检查构建结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  Build completed successfully!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}${NC}"
    
    # 显示镜像信息
    echo ""
    echo -e "${YELLOW}Image details:${NC}"
    docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Run fast mode:  ${GREEN}./scripts/run.sh fast${NC}"
    echo -e "  2. Run slow mode:  ${GREEN}./scripts/run.sh slow${NC}"
    echo -e "  3. Run tests:      ${GREEN}./scripts/test.sh${NC}"
    
    if [ -n "$REGISTRY" ]; then
        echo -e "  4. Push to registry: ${GREEN}docker push ${FULL_IMAGE_NAME}${NC}"
    fi
    
else
    echo ""
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  Build failed!${NC}"
    echo -e "${RED}================================================${NC}"
    echo -e "${YELLOW}Check build.log for details${NC}"
    exit 1
fi
