import aiohttp
import os
import json
import random

API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

async def infer(messages: list, model: str, temp: float, API_KEY: str):
    print(f"Debug: Running infer function with messages: {messages}, model: {model}, temp: {temp}")  # Debug print

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
    
    print(f"Debug: Sending POST request to: {url} with payload: {payload}")  # Debug print

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                print(f"Debug: Successful response with data: {response_data}")  # Debug print
                return response_data['choices'][0]['message']['content']
            else:
                print(f"Debug: Response error with status code: {response.status}")  # Debug print
                return int(response.status)
