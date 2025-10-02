from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    score: float
    topic: str
    text: str


class ManySearchResults(BaseModel):
    results: list[SearchResult]


class SearchQueries(BaseModel):
    semantic_queries: list[str] = Field(
        description="List of queries optimized for semantic search (embeddings-based), rephrasing and expanding the user question for better vector matching."
    )
    lexical_search_query: str = Field(
        description="Exact keywords from the user question, preserved as-is (especially for accounting methodologies), for keyword-based (lexical) search."
    )
    reranker_query: str = Field(
        description="An expanded query that stays within the user's needs, used for reranking retrieved results."
    )


class Chunks(BaseModel):
    chunks: list[str] = Field(..., description="Semanticly seperated chunks.")
