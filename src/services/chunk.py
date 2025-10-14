from tqdm import tqdm
from pathlib import Path
from ..store.nlp import PromptFactory
from ..store.nlp.interfaces import BaseGenerator
from ..store.semantic import VectorDBInterface
from ..core.schemas.guide import Chunks
from ..core.enums import OpenAIRolesEnum
from ..core.config import get_settings

SETTINGS = get_settings()


class ChunkService:
    def __init__(self, nlp, nlp_cohere, vectordb):
        self.nlp: BaseGenerator = nlp
        self.nlp_cohere = nlp_cohere
        self.vectordb: VectorDBInterface = vectordb

    def split_md_file(self, file_path, separator="---#---"):
        content = Path(file_path).read_text(encoding="utf-8")
        pages = content.split(separator)
        pages = [page.strip() for page in pages if page.strip()]
        return pages

    def split_at_boundaries(self, pages, boundaries, num_toc_pages):
        boundaries = sorted(set(boundaries))
        boundaries = [b + num_toc_pages for b in boundaries]

        start = 0
        out = []
        for b in boundaries:
            out.append(pages[start:b])
            start = b
        out.append(pages[start:])
        out.pop(0)
        return ["\n\n---\n\n".join(map(str, sublist)) for sublist in out]

    async def chunk(self, file_path, separator, boundaries, num_toc_pages):
        pages = self.split_md_file(file_path, separator)
        topics = self.split_at_boundaries(pages, boundaries, num_toc_pages)
        all_chunks = list()
        for topic in tqdm(topics, total=len(topics), desc="chunking"):
            response = await self.nlp.structured_chat(
                response_model=Chunks,
                model_name=SETTINGS.GENERATOR_LARGE,
                messages=[
                    {
                        "role": OpenAIRolesEnum.SYSTEM.value,
                        "content": PromptFactory().get_prompt("chunk-hybird"),
                    },
                    {"role": OpenAIRolesEnum.USER.value, "content": topic},
                ],
            )
            all_chunks.append(response)
        return all_chunks
