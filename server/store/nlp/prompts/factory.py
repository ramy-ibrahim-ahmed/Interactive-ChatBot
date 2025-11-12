from typing import Literal
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
PROMPT_DIR = BASE_DIR.joinpath("nlp", "prompts", "md")


class PromptFactory:
    def __init__(self):
        self.prompt_dir = PROMPT_DIR
        self.prompts = {
            "chat": self._load_prompt,
            "chunk": self._load_prompt,
            "classify": self._load_prompt,
            "history": self._load_prompt,
            "ocr": self._load_prompt,
            "queries": self._load_prompt,
            "semantic": self._load_prompt,
        }

    def get_prompt(
        self,
        prompt_type: Literal[
            "chat", "chunk", "classify", "history", "ocr", "queries", "semantic"
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
