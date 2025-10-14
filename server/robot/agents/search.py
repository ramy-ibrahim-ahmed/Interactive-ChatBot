from ..state import State
from ...store.nlp.interfaces import BaseEmbeddings, BaseReranker
from ...store.semantic import VectorDBInterface
from ...core.schemas.guide import ManySearchResults, SearchResult
from ...store.lexical.search import LexicalSearch
from ...core.config import get_settings

SETTINGS = get_settings()


async def search_node(
    state: State,
    embeddings: BaseEmbeddings,
    reranker: BaseReranker,
    vectordb: VectorDBInterface,
    lexical_search: LexicalSearch,
) -> State:

    system_name = state.get("system_name")
    queries_obj = state.get("enhanced_query")

    semantic_queries = queries_obj.semantic_queries
    lexical_query = queries_obj.lexical_search_query
    reranker_query = queries_obj.reranker_query

    embeddings = await embeddings.embed(semantic_queries, SETTINGS.EMBEDDING_MODEL)

    nearest_semantic = vectordb.query_chunks(
        embeddings,
        system_name,
        SETTINGS.SEMANTIC_TOP_K,
    )

    nearest_lexical = lexical_search.search(
        lexical_query,
        SETTINGS.LEXICAL_TOP_K,
        system_name,
    )

    unique_chunks = {n["text"] for n in nearest_semantic}
    unique_chunks.update(k["text"] for k in nearest_lexical)
    unique_chunks_list = list(unique_chunks)

    reranked_nearest = await reranker.rerank(
        query=reranker_query,
        documents=unique_chunks_list,
        model_name=SETTINGS.RERANKER_MODEL,
        top_n=min(SETTINGS.RERANKER_TOP_K, len(unique_chunks_list)),
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

    search_as_text = "\n\n---\n\n".join(
        result.text for result in search_results.results
    )

    return {"formated_search": search_as_text}
