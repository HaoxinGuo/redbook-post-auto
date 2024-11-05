import requests
import json
import asyncio

class AIHelper:
    def __init__(self):
        self.api_key = '你的智谱AI API密钥'
        self.api_url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
        
    async def polish_text(self, content):
        try:
            response = await self.call_api(content)
            return self.process_response(response)
        except Exception as e:
            print(f"AI处理错误: {str(e)}")
            return content
            
    async def call_api(self, content):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            "model": "glm-4-plus",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的文字润色助手。"
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 4095
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                return await response.json()
                
    def process_response(self, response):
        try:
            return response['choices'][0]['message']['content']
        except:
            return "AI处理失败" 