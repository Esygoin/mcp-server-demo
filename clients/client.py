import asyncio

from contextlib import AsyncExitStack
from pathlib import Path

import json
import os
import system_prompt
from dotenv import load_dotenv
from dashscope import Generation
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
print(f"正在从以下路径加载环境变量: {env_path}")
load_dotenv(dotenv_path=env_path)
import dashscope
api_key = os.getenv("DASHSCOPE_API_KEY")
if api_key:
    dashscope.api_key = api_key
    dashscope.region = "cn-beijing"
    print("API 密钥已设置")
else:
    print("未找到 API 密钥，请检查 .env 文件")
Qwen_model = os.getenv("QWEN_MODEL")
print(f"已选择模型{Qwen_model}")

class MCPClient:
    def __init__(self):
        self.session: ClientSession | None = None  # MCP会话
        self.exit_stack = AsyncExitStack()  # 异步资源管理器
        
    async def connect_to_server(self, server_script_path: str):
        """
        connect_to_server 的 Docstring
        连接到一个MCP服务器
        :param server_script_path: Path to the server script
        """
        is_python = server_script_path.endswith(".py")

        if is_python:
            path = Path(server_script_path).resolve()
            server_params = StdioServerParameters(
                command="uv",
                args=["--directory", str(path.parent), "run", path.name],
                env=None,
            )
        else:
            raise ValueError("Server script must be py file")

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """使用Qwen以及可用的工具处理query"""
        messages = [{"role": "user", "content": query}]
        
        response = await self.session.list_tools()
        available_tools = [
            {"names":tool.name, "description":tool.description, "input_schema": tool.inputSchema}
            for tool in response.tools
        ]
        history_text = [
                {"role": "system", "content": system_prompt.qwen_mcp_system_prompt(available_tools)},
                *messages
            ]
        raw = Generation.call(
            model = Qwen_model,
            messages = history_text,
            result_format = "message"
        )
        response = raw.output.choices[0].message["content"]
        data = json.loads(response)
        reply = []
        #先不考虑可能工具调用+文本输出的情况，规定只进行一次工具调用或输出，如果有工具调用再结合工具调用给出输出
        if data['type'] == "text": 
            history_text.append(response) 
            reply.append(data["text"])
        elif data['type'] == "tool_use": 
            tool_name = data['name']
            tool_args = data['input']       #可能需要转化为字典的形式
            # Execute tool call 
            result = await self.session.call_tool(tool_name, tool_args)
            history_text.append({"role":"system","content":f"Calling tool {tool_name} with args {tool_args}"}) #调用工具获取回复  
            history_text.append({"role":"system","content":result.content[0].text})
            reply.append(f"Calling Tool {tool_name} with args {tool_args}")
            reply.append(f"Result of Calling Tool {result.content[0].text}")
                    
            # Get next response from Qwen 
            raw = Generation.call(
                model = Qwen_model,
                messages = history_text,
                result_format = "message"
            )
            answer = raw.output.choices[0].message["content"]
            reply.append((json.loads(answer))["text"])
            history_text.append({"role":"assistant","content":answer})
        return reply
        
    async def chat_loop(self):
        """运行可交互的chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                response = await self.process_query(query)
                for statement in response:
                    print(statement)
                
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()

    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
