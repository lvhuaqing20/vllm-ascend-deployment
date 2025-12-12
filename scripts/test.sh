#!/bin/bash
# Test script for vLLM-Ascend deployment
# 测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
API_URL=${API_URL:-"http://localhost:8000"}
TIMEOUT=5

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Testing vLLM-Ascend API${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}API URL: ${API_URL}${NC}"
echo ""

# 检查curl是否安装
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed${NC}"
    exit 1
fi

# 测试1: 健康检查
echo -e "${YELLOW}Test 1: Health Check${NC}"
HEALTH_URL="${API_URL}/health"
echo "  GET ${HEALTH_URL}"

if curl -s -f -m ${TIMEOUT} "${HEALTH_URL}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Health check passed${NC}"
else
    echo -e "  ${RED}✗ Health check failed${NC}"
    echo -e "  ${YELLOW}Is the server running? Check with: docker ps${NC}"
    exit 1
fi

echo ""

# 测试2: 模型信息
echo -e "${YELLOW}Test 2: Get Models${NC}"
MODELS_URL="${API_URL}/v1/models"
echo "  GET ${MODELS_URL}"

MODELS_RESPONSE=$(curl -s -m ${TIMEOUT} "${MODELS_URL}")
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓ Models endpoint accessible${NC}"
    echo "  Response: ${MODELS_RESPONSE}" | head -c 200
    echo "..."
else
    echo -e "  ${RED}✗ Failed to get models${NC}"
fi

echo ""
echo ""

# 测试3: 简单生成（快思考）
echo -e "${YELLOW}Test 3: Simple Completion${NC}"
COMPLETION_URL="${API_URL}/v1/completions"
echo "  POST ${COMPLETION_URL}"

PAYLOAD='{
  "model": "/models/qwen3-0.6b",
  "prompt": "什么是人工智能？请简要回答。",
  "max_tokens": 50,
  "temperature": 0.7
}'

echo "  Prompt: 什么是人工智能？请简要回答。"
echo -n "  Response: "

RESPONSE=$(curl -s -m 10 -X POST "${COMPLETION_URL}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}")

if [ $? -eq 0 ]; then
    # 尝试提取生成的文本
    TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['text'])" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}${TEXT}${NC}"
        echo -e "  ${GREEN}✓ Completion test passed${NC}"
    else
        echo -e "${RED}✗ Failed to parse response${NC}"
        echo "  Raw response: ${RESPONSE}"
    fi
else
    echo -e "  ${RED}✗ Request failed${NC}"
fi

echo ""
echo ""

# 总结
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Basic tests completed!${NC}"
echo ""
echo -e "${YELLOW}For more comprehensive testing, run:${NC}"
echo -e "  Python tests:  ${GREEN}pytest tests/${NC}"
echo -e "  Benchmarks:    ${GREEN}python tests/benchmark.py${NC}"
echo ""
