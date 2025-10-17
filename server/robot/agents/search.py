import structlog
from ..state import State
from ...store.nlp.interfaces import BaseEmbeddings, BaseReranker
from ...store.semantic import VectorDBInterface
from ...core.schemas.search import SearchResults
from ...store.lexical.search import LexicalSearch
from ...core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.get_logger(__name__)


async def SearchAgent(
    state: State,
    embeddings: BaseEmbeddings,
    reranker: BaseReranker,
    vectordb: VectorDBInterface,
    lexical_search: LexicalSearch,
) -> State:

    system_name = state.get("system_name")
    queries_obj = state.get("queries")

    semantic_queries = queries_obj.semantic_queries
    lexical_query = queries_obj.lexical_search_query
    reranker_query = queries_obj.reranker_query

    # ----------------------- SEARCH PIPELINE -----------------------------#
    LOGGER.info("Search pipeline started", agent="Search")

    embeddings = await embeddings.embed(semantic_queries, SETTINGS.EMBEDDING_MODEL)
    LOGGER.info("   1. Embedding success", agent="Search")

    nearest_semantic = vectordb.query_chunks(
        embeddings,
        system_name,
        SETTINGS.SEMANTIC_TOP_K,
    )
    LOGGER.info(
        "   2. Cosine similarity success",
        agent="Search",
        num_docs={len(nearest_semantic)},
    )

    nearest_lexical = lexical_search.search(
        lexical_query,
        SETTINGS.LEXICAL_TOP_K,
        system_name,
    )
    LOGGER.info(
        "   3. Probabilistic success",
        agent="Search",
        num_docs={len(nearest_lexical)},
    )

    unique_chunks = {n["text"] for n in nearest_semantic}
    unique_chunks.update(k["text"] for k in nearest_lexical)
    unique_chunks_list = list(unique_chunks)

    reranked_nearest: SearchResults = await reranker.rerank(
        query=reranker_query,
        documents=unique_chunks_list,
        model_name=SETTINGS.RERANKER_MODEL,
        top_n=min(SETTINGS.RERANKER_TOP_K, len(unique_chunks_list)),
    )
    LOGGER.info(
        "   4. Cross encoder product success",
        agent="Search",
        num_docs={len(reranked_nearest.results)},
    )
    # ----------------------- SEARCH PIPELINE -----------------------------#

    search_as_text = "\n\n---\n\n".join(
        f"Information retrieving score: {item.score}\n\n{item.text}"
        for item in reranked_nearest.results
    )

    LOGGER.info("Search pipeline end", agent="Search")

    return {"search": search_as_text}
