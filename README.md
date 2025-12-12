# vLLM-Ascend 部署项目

基于华为昇腾Atlas 300I Duo的vLLM推理框架部署方案，支持Qwen3模型的快/慢思考双模式。

## 📋 项目信息

- **硬件平台**: Atlas 300I Duo
- **芯片架构**: x86_64
- **CANN版本**: 8.2.RC1
- **推理框架**: vLLM-Ascend
- **支持模型**: Qwen3-0.6B (支持快/慢思考模式)

## 🚀 快速开始

### 前置要求

1. 已安装昇腾驱动和CANN Toolkit 8.2.RC1
2. Docker已安装并配置
3. 至少16GB内存和一块Ascend NPU

### 一键部署
```bash
# 克隆项目
git clone https://github.com/lvhuaqing20/vllm-ascend-deployment.git
cd vllm-ascend-deployment

# 构建Docker镜像
./scripts/build.sh

# 启动服务（快思考模式）
./scripts/run.sh fast

# 或启动慢思考模式
./scripts/run.sh slow
```

## 📁 项目结构
```
vllm-ascend-deployment/
├── README.md                 # 项目说明文档
├── LICENSE                   # 开源许可证
├── .gitignore               # Git忽略规则
├── Dockerfile               # Docker镜像构建文件
├── requirements.txt         # Python依赖
├── config/                  # 配置文件目录
│   ├── fast_mode.yaml      # 快思考模式配置
│   └── slow_mode.yaml      # 慢思考模式配置
├── scripts/                 # 脚本目录
│   ├── build.sh            # 构建脚本
│   ├── run.sh              # 运行脚本
│   ├── test.sh             # 测试脚本
│   └── setup_env.sh        # 环境设置脚本
├── src/                     # 源代码目录
│   ├── server.py           # 服务器主程序
│   └── utils.py            # 工具函数
├── tests/                   # 测试目录
│   ├── test_api.py         # API测试
│   └── benchmark.py        # 性能测试
└── docs/                    # 文档目录
    ├── deployment.md       # 部署文档
    ├── api.md              # API文档
    └── troubleshooting.md  # 故障排除
```

## 🎯 功能特性

### 快思考模式 (Fast Mode)
- **适用场景**: 快速问答、实时对话
- **最大序列长度**: 4096 tokens
- **并发请求数**: 64
- **推理延迟**: < 1s
- **Temperature**: 0.7-1.0

### 慢思考模式 (Slow Mode)
- **适用场景**: 复杂推理、长文本生成
- **最大序列长度**: 8192 tokens
- **并发请求数**: 32
- **推理延迟**: 2-5s
- **Temperature**: 0.1-0.5

## 📊 性能指标

| 模式 | 吞吐量 (req/s) | P50延迟 (ms) | P99延迟 (ms) |
|------|---------------|--------------|--------------|
| Fast | 45-60         | 800          | 1500         |
| Slow | 15-25         | 2500         | 4500         |

*测试环境: Atlas 300I Duo, Qwen3-0.6B, batch_size=1*

## 🔧 配置说明

### 快思考模式配置 (config/fast_mode.yaml)
```yaml
model:
  name: "Qwen3-0.6B"
  path: "/models/qwen3-0.6b"
  
inference:
  max_model_len: 4096
  max_num_seqs: 64
  dtype: "bfloat16"
  gpu_memory_utilization: 0.85
  
generation:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 256
```

### 慢思考模式配置 (config/slow_mode.yaml)
```yaml
model:
  name: "Qwen3-0.6B"
  path: "/models/qwen3-0.6b"
  
inference:
  max_model_len: 8192
  max_num_seqs: 32
  dtype: "bfloat16"
  gpu_memory_utilization: 0.90
  
generation:
  temperature: 0.3
  top_p: 0.95
  max_tokens: 1024
```

## 🛠️ 环境安装

### 方法1: Docker部署（推荐）
```bash
# 构建镜像
docker build -t vllm-ascend:v0.1 .

# 运行容器（快思考模式）
docker run -d \
  --name vllm-fast \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  --device=/dev/hisi_hdc \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  -v $(pwd)/models:/models \
  -e THINKING_MODE=fast \
  -p 8000:8000 \
  vllm-ascend:v0.1
```

### 方法2: 本地安装
```bash
# 1. 安装CANN Toolkit
wget https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/CANN/8.2.RC1/Ascend-cann-toolkit_8.2.RC1_linux-x86_64.run
chmod +x Ascend-cann-toolkit_8.2.RC1_linux-x86_64.run
./Ascend-cann-toolkit_8.2.RC1_linux-x86_64.run --install

# 2. 设置环境变量
source /usr/local/Ascend/ascend-toolkit/set_env.sh

# 3. 创建Python环境
conda create -n vllm-ascend python=3.9
conda activate vllm-ascend

# 4. 安装PyTorch和torch_npu
pip install torch==2.1.0
pip install torch_npu==2.1.0.post3

# 5. 克隆并安装vllm-ascend
git clone https://github.com/PannenetsF/vllm.git -b ascend_develop
cd vllm
pip install -r requirements-npu.txt
VLLM_TARGET_DEVICE=npu python setup.py install

# 6. 下载模型
mkdir -p models
cd models

# 使用新的 hf 命令
hf download Qwen/Qwen3-0.6B --local-dir qwen3-0.6b

# 或使用 git clone（较慢）
git clone https://huggingface.co/Qwen/Qwen3-0.6B qwen3-0.6b

# 国内用户可以使用镜像
export HF_ENDPOINT=https://hf-mirror.com
hf download Qwen/Qwen3-0.6B --local-dir qwen3-0.6b

## 📡 API使用

### 启动服务
```bash
# 快思考模式
python -m vllm.entrypoints.openai.api_server \
  --model /models/qwen3-0.6b \
  --device npu \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 4096 \
  --max-num-seqs 64
```

### API调用示例

#### Python
```python
import requests

url = "http://localhost:8000/v1/completions"

payload = {
    "model": "/models/qwen3-0.6b",
    "prompt": "什么是人工智能？",
    "max_tokens": 100,
    "temperature": 0.7
}

response = requests.post(url, json=payload)
print(response.json()["choices"][0]["text"])
```

#### cURL
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/qwen3-0.6b",
    "prompt": "什么是人工智能？",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## 🧪 测试

### 运行单元测试
```bash
# 运行所有测试
./scripts/test.sh

# 或使用pytest
pytest tests/ -v
```

### 性能基准测试
```bash
# 运行性能测试
python tests/benchmark.py --mode fast --requests 100 --concurrency 10

# 对比两种模式
python tests/benchmark.py --mode fast --requests 100
python tests/benchmark.py --mode slow --requests 100
```

## 🐛 故障排除

### 常见问题

#### 1. NPU设备未识别
```bash
# 检查NPU设备
npu-smi info

# 如果未识别，检查驱动
cat /usr/local/Ascend/driver/version.info

# 设置环境变量
export ASCEND_DEVICE_ID=0
```

#### 2. CANN版本不匹配

确保以下组件版本一致：
- CANN Toolkit: 8.2.RC1
- CANN Driver: 8.2.RC1
- torch_npu: 2.1.0.post3

#### 3. 内存不足 (OOM)
```bash
# 减少并发数
--max-num-seqs 32

# 减少序列长度
--max-model-len 2048

# 降低内存使用率
--gpu-memory-utilization 0.7
```

#### 4. Docker容器无法访问NPU
```bash
# 确保挂载所有必要的设备
docker run \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  --device=/dev/hisi_hdc \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  ...
```

## 📚 文档

- [部署指南](docs/deployment.md) - 详细的部署步骤
- [API文档](docs/api.md) - 完整的API参考
- [故障排除](docs/troubleshooting.md) - 常见问题解决

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [vLLM](https://github.com/vllm-project/vllm) - 原始vLLM项目
- [vLLM-Ascend](https://github.com/PannenetsF/vllm/tree/ascend_develop) - 昇腾适配版本
- [Qwen](https://github.com/QwenLM/Qwen) - Qwen模型
- [华为昇腾](https://www.hiascend.com/) - 昇腾AI处理器

## 📧 联系方式

- 作者: lvhuaqing20
- 邮箱: jianuolei662@gmail.com
- 项目链接: https://github.com/lvhuaqing20/vllm-ascend-deployment
