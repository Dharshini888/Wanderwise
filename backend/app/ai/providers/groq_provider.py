import os
from app.ai.providers.base_provider import BaseAIProvider

class GroqProvider(BaseAIProvider):
    """Groq LLM Provider implementation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is missing")
        
        try:
            import urllib.request
            import json
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_instruction or "You are WanderWise AI."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Groq generation error: {e}")
