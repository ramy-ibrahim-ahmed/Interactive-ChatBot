from pydantic import BaseModel, Field
from typing import Literal


class Decision(BaseModel):
    decision: Literal["__classify__", "__chat__", "__end__"] = Field(
        ..., description="The vlaue which will decide where to go next."
    )


class Queries(BaseModel):
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
