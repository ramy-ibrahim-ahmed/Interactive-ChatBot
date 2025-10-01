from typing import Literal
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
PROMPT_DIR = BASE_DIR.joinpath("nlp", "prompts", "md")


class PromptFactory:
    def __init__(self):
        self.prompt_dir = PROMPT_DIR
        self.prompts = {
            "query_write": self._load_prompt,
            "chat": self._load_prompt,
            "user_intent": self._load_prompt,
            "memory": self._load_prompt,
            "analysis": self._load_prompt,
            "vlm_markdown": self._load_prompt,
            "chunk_fixed": self._load_prompt,
            "formate": self._load_prompt,
            "answer-one-step": self._load_prompt,
            "chunking_rewrite": self._load_prompt,
        }

    def get_prompt(
        self,
        prompt_type: Literal[
            "query_write",
            "chat",
            "user_intent",
            "memory",
            "analysis",
            "vlm_markdown",
            "chunk_fixed",
            "formate",
            "answer-one-step",
            "chunking_rewrite",
        ],
    ) -> str:
        if prompt_type not in self.prompts:
            raise ValueError(f"Invalid prompt type: {prompt_type}")
        return self.prompts[prompt_type](prompt_type)

    def _load_prompt(self, name: str) -> str:
        path = self.prompt_dir / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8")
