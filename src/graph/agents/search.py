from ..state import State
from ...store.nlp import NLPInterface
from ...store.vectordb import VectorDBInterface
from ...core.schemas.guide import ManySearchResults, SearchResult
from .utils import search_keywords


def search_node(
    state: State, nlp_cohere: NLPInterface, vectordb: VectorDBInterface
) -> State:
    enhanced_query = state.get("enhanced_query")
    system_name = state.get("system_name")

    embeddings = nlp_cohere.embed(enhanced_query.semantic_queries)
    nearest = vectordb.query_chunks(embeddings, system_name, max_retrieved=20)
    keywords = search_keywords(enhanced_query.lexical_search_query, 20)

    unique_chunks = {n["text"] for n in nearest}
    unique_chunks.update(k["text"] for k in keywords)
    unique_chunks_list = list(unique_chunks)

    reranked_nearest = nlp_cohere.rerank(
        query=enhanced_query.reranker_query,
        documents=unique_chunks_list,
        model_name="rerank-v3.5",
        top_n=min(3, len(unique_chunks_list)),
    )

    search_results = ManySearchResults(
        results=[
            SearchResult(score=item["score"], text=str(item["text"]))
            for item in reranked_nearest
        ]
    )

    return {"search_results": search_results}


def formate_node(state: State) -> State:
    search_results: ManySearchResults = state.get("search_results")
    if not search_results or not search_results.results:
        return {"formated_search": ""}

    search_as_text = "\n\n\n---\n\n\n".join(
        result.text for result in search_results.results
    )
    return {"formated_search": search_as_text}
