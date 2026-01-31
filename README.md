## 项目概述
这是一个基于 Model Context Protocol (MCP) 的 Python 项目演示，集成了通义千问 (Qwen) 模型。项目展示了如何构建一个支持工具调用的 MCP 客户端。

## 项目初始化
使用uv进行项目管理：

```bash
# 初始化新的 uv 项目
uv init mcp-server-demo
cd mcp-server-demo

# 添加MCP到项目依赖
uv add "mcp[cli]"

# 安装Qwen相关依赖
uv pip install dashscope python-dotenv

#设置Qwen-api
cat > .env << EOF
DASHSCOPE_API_KEY=sk-你的API密钥
QWEN_MODEL=qwen-turbo
EOF

#运行项目
python python clients/client.py servers/quickstart.py
```

## 项目架构
```
mcp-server-demo/
├── clients/                    # 客户端代码
│   ├── client.py              # 主客户端程序
│   └── system_prompt.py       # 系统提示模板
├── servers/                   # MCP 服务器示例
│   └── quickstart.py          # 快速开始服务器，在服务器中注册工具
├── .env                       # 环境变量文件（API 密钥）
├── .gitignore                 # Git 忽略文件
├── pyproject.toml             # 项目配置
├── uv.lock                    # uv 锁文件
└── README.md                  # 项目文档
```