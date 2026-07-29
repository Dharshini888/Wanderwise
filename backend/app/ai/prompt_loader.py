import os
from typing import Dict, Any

_PROMPT_CACHE: Dict[str, str] = {}

class PromptLoader:
    """Prompt template loader supporting versioning, caching, and parameter formatting."""

    @staticmethod
    def load(template_name: str, version: str = "v1", shared: bool = False) -> str:
        cache_key = f"{'shared' if shared else version}:{template_name}"
        if cache_key in _PROMPT_CACHE:
            return _PROMPT_CACHE[cache_key]

        base_dir = os.path.dirname(__file__)
        if shared:
            file_path = os.path.join(base_dir, "prompts", "shared", f"{template_name}.txt")
        else:
            file_path = os.path.join(base_dir, "prompts", version, f"{template_name}.txt")

        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        _PROMPT_CACHE[cache_key] = content
        return content

    @staticmethod
    def render(template_name: str, kwargs: Dict[str, Any], version: str = "v1") -> str:
        raw_tmpl = PromptLoader.load(template_name, version=version)
        try:
            return raw_tmpl.format(**kwargs)
        except Exception:
            return raw_tmpl
