from tqdm import tqdm
from pathlib import Path
from ..store.nlp import NLPInterface, PromptFactory
from ..store.vectordb import VectorDBInterface
from ..core.schemas.guide import Chunks
from ..core.enums import OpenAIRolesEnum


class ProcessService:
    def __init__(self, nlp, nlp_cohere, vectordb):
        self.nlp: NLPInterface = nlp
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

    def chunk(
        self,
        file_path,
        separator,
        boundaries,
        num_toc_pages,
        collection_name: str,
    ):
        pages = self.split_md_file(file_path, separator)
        topics = self.split_at_boundaries(pages, boundaries, num_toc_pages)

        for topic_id, topic in tqdm(
            enumerate(topics), total=len(topics), desc="chunking"
        ):
            response = self.nlp.structured_chat(
                response_model=Chunks,
                model_name="gpt-4.1",
                messages=[
                    {
                        "role": OpenAIRolesEnum.SYSTEM.value,
                        "content": PromptFactory().get_prompt("chunking_rewrite"),
                    },
                    {"role": OpenAIRolesEnum.USER.value, "content": topic},
                ],
            )
            embeddings = self.nlp_cohere.embed(response.chunks, batch_size=10)
            metadata = list()
            for text in response.chunks:
                metadata.append({"topic_id": topic_id + 1, "text": text})
            self.vectordb.upsert(embeddings, metadata, collection_name, 100)
