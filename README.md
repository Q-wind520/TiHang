# 题航 TiHang

> **高度集成 LLM 的智能刷题软件** — 让 AI 陪练成为你的最强备考搭档

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green?logo=qt)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Anthropic-orange)](https://platform.openai.com/)

---

## 📖 简介

**题航（TiHang）** 是一款基于 PySide6 构建的桌面端智能刷题软件，深度集成 OpenAI 与 Anthropic 两大 LLM 平台，为你的备考之路提供 AI 级别的陪伴式辅导。

无论你是在备战期末考试、考研、技术认证，还是准备编程面试，题航都能帮你系统化管理题库、追踪练习进度，并通过 AI 实时获得解题提示、答案解析、概念讲解和代码审查。

### ✨ 核心特性

| 模块 | 功能 |
| ------- | ------- |
| **AI 辅导** | 多模式 AI 对话：通用问答、渐进式提示、答案解析、概念教学、代码审查 |
| **全题型支持** | 单选题 · 多选题 · 填空题 · 简答题 · 判断题 · 编程题 |
| **题库管理** | 自定义题库分类，按标签/难度/状态筛选，灵活组织题目 |
| **代码高亮** | 基于 Pygments 的语法高亮，支持 6 种编辑器主题 |
| **流式对话** | SSE 流式响应，逐字输出 AI 回答，体验流畅 |
| **多 Provider** | 同时支持 OpenAI（GPT-4o 等）和 Anthropic（Claude Sonnet 4 等），随时切换 |
| **本地存储** | 纯 JSON 文件存储，零数据库依赖，数据归你所有 |
| **中文原生** | 完整的中文界面与系统提示词，为中文教育场景优化 |

---

## 🚀 快速开始

### 环境要求

- **Python** ≥ 3.12
- **系统**：Windows / macOS / Linux（带 GUI 环境）

### 安装与运行

```bash
# 1. 克隆项目
git clone <your-repo-url> tihang
cd tihang

# 2. 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# 或
.venv\Scripts\activate       # Windows

# 3. 安装依赖
pip install -e .
# 带开发依赖（含测试/格式化工具）：
pip install -e ".[dev]"

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key，或启动后在设置界面中配置

# 5. 启动
tihang
# 或直接运行
python run.py
```

### 配置 LLM

题航支持两种配置方式：

**方式一：环境变量（`.env` 文件）**

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

**方式二：应用内设置**

启动后点击菜单栏 `设置 → 打开设置`，在对话框中填写 API Key、选择模型。

---

## 🏗️ 项目架构

```
TiHang/
├── run.py                  # 应用入口
├── config/                 # 常量与默认配置
│   ├── constants.py        # 枚举定义（题型、难度、状态）
│   └── defaults.py         # 默认设置与主题
├── models/                 # 数据模型（dataclass）
│   ├── question.py         # 题目模型
│   ├── bank.py             # 题库模型
│   ├── category.py         # 分类模型
│   ├── tag.py              # 标签模型
│   ├── chat.py             # 对话模型
│   └── settings_model.py   # 设置模型
├── storage/                # JSON 文件持久化层
│   ├── base_store.py       # 存储基类
│   ├── question_store.py   # 题目 CRUD
│   ├── bank_store.py       # 题库 CRUD
│   ├── category_store.py   # 分类 CRUD
│   ├── tag_store.py        # 标签 CRUD
│   ├── chat_store.py       # 对话存储
│   └── settings_store.py   # 设置存储
├── llm/                    # LLM 集成层
│   ├── base_provider.py    # Provider 抽象基类
│   ├── openai_provider.py  # OpenAI 适配器
│   ├── anthropic_provider.py # Anthropic 适配器
│   ├── provider_registry.py  # Provider 注册中心
│   ├── llm_manager.py      # LLM 管理器（信号驱动）
│   ├── api_worker.py       # 异步 API 工作线程
│   └── prompt_templates.py # 系统提示词模板
├── ui/                     # PySide6 前端
│   ├── main_window.py      # 主窗口（三栏布局）
│   ├── widgets/            # UI 组件
│   │   ├── question_list.py    # 题目列表
│   │   ├── question_detail.py  # 题目详情
│   │   ├── chat_panel.py       # AI 对话面板
│   │   ├── chat_bubble.py      # 聊天气泡
│   │   ├── code_editor.py      # 代码编辑器
│   │   ├── markdown_editor.py  # Markdown 编辑
│   │   ├── difficulty_badge.py # 难度徽章
│   │   ├── tag_badge.py        # 标签徽章
│   │   ├── status_indicator.py # 状态指示器
│   │   └── syntax_highlighter.py # 语法高亮
│   └── dialogs/            # 对话框
│       ├── question_dialog.py  # 题目编辑弹窗
│       ├── settings_dialog.py  # 设置弹窗
│       └── bank_dialog.py      # 题库管理弹窗
├── assets/
│   └── styles/
│       └── app.qss         # Qt 样式表
├── data/                   # 用户数据（JSON 文件）
├── tests/                  # 单元测试
├── .env.example            # 环境变量模板
├── .gitignore
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖清单（简化版）
└── README.md
```

### 设计理念

- **信号驱动**：LLM 管理器通过 Qt 信号与 UI 通信，异步非阻塞
- **Provider 模式**：LLM 接入层使用抽象基类 + 注册中心，新增 Provider 只需实现接口
- **分层清晰**：Models → Storage → LLM → UI，数据流单向
- **本地优先**：零云服务依赖（除了 LLM API），数据完全本地存储

---

## 🧪 开发指南

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
# Ruff 格式化 + 检查
ruff check .
ruff format --check .

# Mypy 类型检查
mypy models/ llm/ --ignore-missing-imports
```

### 添加新的 LLM Provider

1. 在 `llm/` 下创建 `<name>_provider.py`
2. 继承 `LLMProvider` 抽象基类
3. 实现 `chat()` 和 `chat_stream()` 方法
4. 在 `llm/__init__.py` 中注册

```python
# 示例：注册自定义 Provider
from llm.provider_registry import register_provider
from mymodule import MyProvider
register_provider("myprovider", MyProvider)
```

### 添加新题型

1. 在 `config/constants.py` 中添加 `QuestionType` 枚举值
2. 在 `models/question.py` 中添加题型特定字段（如需要）
3. 在 `ui/dialogs/question_dialog.py` 中添加题型专属 UI
4. 在 `ui/widgets/question_detail.py` 中添加答题 UI

---

## 🛠️ 依赖

| 类别 | 依赖 | 说明 |
| ------ | ------ | ------ |
| GUI 框架 | [PySide6](https://doc.qt.io/qtforpython-6/) | Qt 6 for Python，原生跨平台 |
| 代码高亮 | [Pygments](https://pygments.org/) | 多语言语法高亮 |
| LLM SDK | [OpenAI Python](https://github.com/openai/openai-python) | OpenAI API 客户端 |
| LLM SDK | [Anthropic Python](https://github.com/anthropics/anthropic-sdk-python) | Anthropic API 客户端 |
| 格式化 | [Ruff](https://docs.astral.sh/ruff/) | 快速 Python linter/formatter |
| 类型检查 | [Mypy](https://mypy-lang.org/) | 静态类型检查 |

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  <b>题航 TiHang</b> — 以 AI 为帆，驶向知识的彼岸 🚢
</p>
