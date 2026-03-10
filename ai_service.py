import os
import json
import re
import httpx
from typing import Any, Dict, List

AI_ENDPOINT = "https://inference.do-ai.run/v1/chat/completions"
DEFAULT_MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")

def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    timeout = httpx.Timeout(90.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(AI_ENDPOINT, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Assume the model returns a 'content' field in the first choice
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_str = _extract_json(content)
            return json.loads(json_str)
        except Exception as e:
            # Log could be added here
            return {"note": "AI service temporarily unavailable", "error": str(e)}

async def generate_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    max_sentences = params.get("max_sentences", 2)
    system_msg = {
        "role": "system",
        "content": "You are a concise summarizer. Return a JSON object with keys 'summary' (string) and 'confidence' (float 0‑1)."
    }
    user_msg = {
        "role": "user",
        "content": f"Summarize the content at {url} in up to {max_sentences} sentences."
    }
    return await _call_inference([system_msg, user_msg], max_tokens=512)

async def suggest_tags(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    system_msg = {
        "role": "system",
        "content": "You are a tag assistant. Return a JSON array under the key 'tags', each element being an object with 'tag' (string) and 'confidence' (float 0‑1). Suggest up to 7 relevant tags."
    }
    user_msg = {
        "role": "user",
        "content": f"Suggest tags for the page at {url}."
    }
    return await _call_inference([system_msg, user_msg], max_tokens=512)
