import os
import dotenv
import base64

dotenv.load_dotenv()

from langchain.chat_models import init_chat_model

model = init_chat_model(
    model="qwen-flash",
    model_provider="openai",
    api_key="sk-7a58370bee5745a69b03f66e2d353d16",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient(
    {
        "Wan26Media":{
            "transport":"sse",
            "url":"https://dashscope.aliyuncs.com/api/v1/mcps/Wan26Media/sse",
            "headers":{
                "Authorization":"Bearer sk-7a58370bee5745a69b03f66e2d353d16"
            }
        }
    }
)

import asyncio
import requests
from langchain_core.tools import tool

async def create():
    
    tools = await client.get_tools()

    @tool
    def download_image(url, save_path):
        """
        下载图片并保存到本地
        :param url: 图片的完整网址
        :param save_path: 本地保存路径（如：'images/photo.png'）
        """
        try:
            # 发送GET请求
            response = requests.get(url, stream=True) # stream=True支持大文件流式下载[citation:4]
            response.raise_for_status() # 检查请求是否成功（状态码200）[citation:4]

            # 以二进制写入模式保存图片
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192): # 分块写入[citation:4]
                    file.write(chunk)
            print(f"图片已成功保存至：{save_path}")
        except requests.exceptions.RequestException as e:
            print(f"下载失败，错误信息：{e}")
    agent = create_agent(
        model=model,
        tools=tools+[download_image],
    )

    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "生成一张图片并保存到本地：一位神明手持巨斧劈开大海，文艺复兴风格"}]}
    )
    # for message in response["messages"]:
    #     if message.type == "tool":
    #     # Raw content in provider-native format
    #         print(f"Raw content: {message.content}")

    #     # Standardized content blocks  #
    #         for block in message.content_blocks:  
    #             if block["type"] == "text":  
    #                 print(f"Text: {block['text']}")  
    #             elif block["type"] == "image":  
    #                 print(f"Image URL: {block.get('url')}")  
    #                 print(f"Image base64: {block.get('base64', '')[:50]}...")
    print(type(response))
    print(response)

asyncio.run(create())

