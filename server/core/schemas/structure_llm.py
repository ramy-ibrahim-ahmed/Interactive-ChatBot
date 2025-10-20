from pydantic import BaseModel, Field
from typing import Literal, List


class Decision(BaseModel):
    """
    Represents the output of the Main Router agent, deciding the next step.
    """

    decision: Literal["__classify__", "__chat__"] = Field(
        ...,
        description="The routing decision. `__classify__` initiates a search, while `__chat__` responds directly using chat history or for conversational replies.",
    )


class Queries(BaseModel):
    """
    Represents the structured query output from the User Query Rewrite (RAG) agent.
    """

    semantic_queries: List[str] = Field(
        ...,
        description="A list of 3-5 rephrased queries designed to capture the user's *intent* for semantic vector search.",
    )
    lexical_search_query: str = Field(
        ...,
        description="A single string of exact keywords from the user query, with no modifications. Used for traditional keyword-based (lexical) search, preserving all technical and Arabic terms.",
    )
    reranker_query: str = Field(
        ...,
        description="A single, elaborated query that clarifies the user's question. This query is used by the reranker model to score and reorder retrieved documents for relevance.",
    )


# class Chunks(BaseModel):
#     """
#     Represents the final, processed context to be sent to the Response Agent.
#     """

#     chunks: List[str] = Field(
#         ...,
#         description="A list of the most relevant text chunks retrieved from the knowledge base. This is the final context used by the Response Agent to generate its answer.",
#     )


class Chunks(BaseModel):
    chunks: list[str] = Field(..., description="Semanticly seperated chunks.")
