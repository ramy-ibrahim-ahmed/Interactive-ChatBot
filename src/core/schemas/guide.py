from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    score: float
    topic: str
    text: str


class ManySearchResults(BaseModel):
    results: list[SearchResult]


class SearchQueries(BaseModel):
    queries: list[str] = Field(
        ...,
        description="A list of relevant search queries in Arabic designed to maximize semantic search recall from a knowledge base.",
    )
    reranker_query: str = Field(
        ...,
        description="A single, comprehensive declarative sentence in Arabic that encapsulates the core information need. This is used by a reranker to improve the precision of the final search results.",
    )


class Chunks(BaseModel):
    chunks: list[str] = Field(..., description="Semanticly seperated chunks.")
