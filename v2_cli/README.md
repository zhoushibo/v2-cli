# 🖥️ V2 CLI

> **V2 学习系统的命令行界面**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)]()

---

## 📖 简介

**V2 CLI** 是 V2 学习系统的命令行入口，提供交互式对话、学习命令、Gateway 管理等功能。基于 Worker Pool 架构，支持流式输出和多任务并行处理。

### 🎯 核心特性

- **💬 交互式对话**：支持流式输出，实时显示 AI 响应
- **🎓 学习命令**：`learn` 命令启动并行学习（3 个视角）
- **🔧 Gateway 管理**：自动连接统一 Gateway 服务
- **⚡ Worker Pool**：多 Worker 并行处理，提升效率
- **📊 进度显示**：实时显示学习和执行进度
- **🛡️ 超时保护**：内置 Timeout Wrapper，防止卡死

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Gateway 服务运行中（`ws://127.0.0.1:8001`）

### 安装依赖

```bash
cd v2_cli
pip install -r requirements.txt
```

### 启动 CLI

```bash
python cli.py
```

### 基本命令

```bash
# 交互式对话
python cli.py

# 学习新知识（3 个视角并行）
python cli.py learn "量子力学基础"

# 执行单条命令
python cli.py -c "解释一下相对论"

# 查看帮助
python cli.py --help
```

---

## 📦 项目结构

```
v2_cli/
├── cli.py                      # 主入口（命令行界面）
├── gateway_manager.py          # Gateway 连接管理
├── learn_command.py            # learn 命令实现
├── auto_test.py                # 自动测试脚本
├── interactive_test.py         # 交互式测试
├── test_cli.py                 # CLI 单元测试
├── test_gateway_auto_start.py  # Gateway 自动启动测试
├── requirements.txt            # 依赖
└── README.md                   # 本文档
```

---

## 🎯 使用示例

### 1. 交互式对话

```bash
$ python cli.py

🤖 V2 CLI v1.0 - 按 Ctrl+C 退出

你：你好，介绍一下你自己
🤖 你好！我是 V2 CLI，一个基于 V2 学习系统的命令行助手...
```

### 2. 学习命令

```bash
$ python cli.py learn "Python 装饰器"

🎓 启动并行学习：Python 装饰器
├─ Worker 1: 基础概念... ✅
├─ Worker 2: 实际用例... ✅
└─ Worker 3: 最佳实践... ✅

✅ 学习完成！已保存到知识库。
```

### 3. 单条命令

```bash
$ python cli.py -c "计算 1+2+3"

🤖 1+2+3 = 6
```

---

## 🔧 配置

创建 `.env` 文件：

```bash
# Gateway 配置
GATEWAY_URL=ws://127.0.0.1:8001

# Worker 配置
WORKER_COUNT=3
TIMEOUT_SECONDS=300

# 输出配置
ENABLE_STREAMING=true
```

---

## 🧪 测试

```bash
# 运行单元测试
python test_cli.py

# 交互式测试
python interactive_test.py

# Gateway 自动启动测试
python test_gateway_auto_start.py
```

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **首字延迟** | <500ms | 流式响应 |
| **学习速度** | 3× 并行 | 3 Worker 同时学习 |
| **超时保护** | 300s | LLM 操作超时限制 |
| **Worker 复用** | LRU 缓存 | 减少重复初始化 |

---

## 🔗 相关链接

- **V2 学习系统**：https://github.com/zhoushibo/v2_learning_system_real
- **OpenClaw Gateway**：https://github.com/zhoushibo/openclaw-gateway
- **MVP JARVIS**：https://github.com/zhoushibo/mvp-jarvis

---

<div align="center">

**V2 CLI - 命令行也能很强大** ⚡

*最后更新：2026-02-20*

</div>
