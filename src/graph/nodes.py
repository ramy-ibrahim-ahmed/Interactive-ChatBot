from .state import State
from .utils import search_keywords
from ..core.enums.chat_roles import OpenAIRolesEnum
from ..core.schemas.guide import SearchResult, ManySearchResults, SearchQueries
from ..store.nlp import NLPInterface, PromptFactory
from ..store.vectordb import VectorDBInterface


async def intent_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = await nlp_openai.chat(messages, "gpt-4.1-mini", temperature=0.0, top_p=1.0)
    return {"intent": intent}


async def query_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    enhanced_query = await nlp_openai.structured_chat(
        SearchQueries, "gpt-4.1-mini", messages
    )
    return {"enhanced_query": enhanced_query}


def system_node(state: State, nlp_openai: NLPInterface) -> State:
    return {"system_name": "customers_v1"}


def search_node(
    state: State,
    nlp_openai: NLPInterface,
    nlp_cohere: NLPInterface,
    vectordb: VectorDBInterface,
) -> State:
    enhanced_query = state.get("enhanced_query")
    system_name = state.get("system_name")
    embeddings = nlp_cohere.embed(enhanced_query.semantic_queries)
    nearest = vectordb.query_chunks(embeddings, system_name, max_retrieved=10)
    nearest_unique = [dict(t) for t in {tuple(sorted(d.items())) for d in nearest}]
    keywords = search_keywords(enhanced_query.lexical_search_query, 10)
    reranked_nearest = nlp_cohere.rerank(
        enhanced_query.reranker_query, keywords + nearest_unique, "rerank-v3.5", 5
    )
    search_results = ManySearchResults(
        results=[
            SearchResult(
                score=float(item["score"]), topic=str(item["topic"]), text=item["text"]
            )
            for item in reranked_nearest
        ]
    )
    return {"search_results": search_results}


def formate_node(state: State) -> State:
    search_results: ManySearchResults = state.get("search_results", "")
    search_as_list = list()
    for result in search_results.results:
        search_as_list.append(result.text)
    search_as_text = "\n\n\n---\n\n\n".join(search_as_list)
    with open("search_results.txt", "w", encoding="utf-8") as f:
        f.write(search_as_text)
    return {"formated_search": search_as_text}


async def chat_node(state: State, nlp_openai):
    answer_prompt = PromptFactory().get_prompt("answer-one-step")
    user_message = state.get("user_message")
    formated_search = state.get("formated_search")
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": answer_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": formated_search},
    ]
    model_name = "gpt-4.1"
    state["response"] = ""
    async for chunk in nlp_openai.stream_chat(messages, model_name):
        state["response"] += chunk
        yield {"chunk": chunk}
