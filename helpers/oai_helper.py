import aiohttp
import os

API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

async def infer(messages: list, model: str, temp: float, API_KEY: str):

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }

    # first we moderate the messages
    messages_soup = ""
    for message in messages:
        messages_soup += f"{message}\n"

    url = f"{API_BASE}/moderations"
    payload = {
        'data': messages_soup
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data['results'][0]['flagged']:
                    return 403

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
