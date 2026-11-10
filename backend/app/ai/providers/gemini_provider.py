import os
from app.ai.providers.base_provider import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI Provider implementation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction if system_instruction else None
            )
            try:
                response = model.generate_content(prompt, request_options={"timeout": 12.0})
            except TypeError:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback import check or error propagation
            raise RuntimeError(f"Gemini generation error: {e}")
