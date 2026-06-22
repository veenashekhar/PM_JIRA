import os
from typing import Any, Dict, List, Optional

import httpx

MODEL = "openai/gpt-oss-120b"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MOCK_ENV = "PM_AI_MOCK"


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


async def call_openrouter(prompt: str) -> str:
    if os.environ.get(MOCK_ENV, "").lower() == "true":
        return "4"
    return await call_openrouter_chat(messages=[{"role": "user", "content": prompt}])


async def call_openrouter_chat(
    messages: List[Dict[str, str]], response_format: Optional[Dict[str, Any]] = None
) -> str:
    if os.environ.get(MOCK_ENV, "").lower() == "true":
        return "{\"response\":\"Mock response\",\"board_update\":null}"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)

    if response.is_error:
        raise httpx.HTTPStatusError(
            f"OpenRouter error {response.status_code}: {response.text}",
            request=response.request,
            response=response,
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]
