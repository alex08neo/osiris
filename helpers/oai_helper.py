import aiohttp
import os
import json
import random

with open(f"{os.path.realpath(os.path.dirname(__file__))}/../config.json") as file:
    data = json.load(file)

if "," in data["openai_api_key"]:
    API_KEY = data["openai_api_key"].split(",")
else:
    API_KEY = data["openai_api_key"]


API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

async def infer(messages: list, model: str, temp: float):
    API_KEY = random.choice(API_KEY) if isinstance(API_KEY, list) else API_KEY
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    url = f"{API_BASE}/chat/completions"
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temp,
        'max_tokens': 2048
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data['choices'][0]['message']['content']
            else:
                return int(response.status)