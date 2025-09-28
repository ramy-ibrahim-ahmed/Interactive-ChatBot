from tqdm import tqdm
from pathlib import Path
from ..store.nlp import NLPInterface, PromptFactory
from ..store.vectordb import VectorDBInterface
from ..core.schemas.guide import Chunks
from ..core.enums import OpenAIRolesEnum


class ProcessService:
    def __init__(self, nlp, vectordb):
        self.nlp: NLPInterface = nlp
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

    def chunk(self, file_path, separator, boundaries, num_toc_pages):
        pages = self.split_md_file(file_path, separator)
        topics = self.split_at_boundaries(pages, boundaries, num_toc_pages)

        many_chunks = list()
        for topic in tqdm(topics, total=len(topics), desc="chunking"):
            response = self.nlp.structured_chat(
                response_model=Chunks,
                model_name="gpt-4.1",
                messages=[
                    {
                        "role": OpenAIRolesEnum.SYSTEM.value,
                        "content": PromptFactory().get_prompt("llm_chunk"),
                    },
                    {"role": OpenAIRolesEnum.USER.value, "content": topic},
                ],
            )
            many_chunks.append(response)
        return many_chunks

    def upload(self, collection_name: str, topics_chunks):
        self.vectordb.create_collection(name=collection_name)

        for topic_id, chunks in tqdm(
            enumerate(topics_chunks), total=len(topics_chunks), desc="uploading"
        ):
            print(len(chunks))
            embeddings = self.nlp.embed(chunks.chunks)
            metadata = list()
            for text in chunks.chunks:
                metadata.append({"topic_id": topic_id + 1, "text": text})
            self.vectordb.upsert(embeddings, metadata, collection_name, 100)
