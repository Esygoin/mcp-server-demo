Adding MCP to your python project
We recommend using uv to manage your Python projects.

If you haven't created a uv-managed project yet, create one:

uv init mcp-server-demo
cd mcp-server-demo
Then add MCP to your project dependencies:

uv add "mcp[cli]"
Alternatively, for projects using pip for dependencies:

pip install "mcp[cli]"

Using Qwen need dashscope

uv pip install dashscope python-dotenv

来源：https://github.com/modelcontextprotocol/python-sdk/tree/main