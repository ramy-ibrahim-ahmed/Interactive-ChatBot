from .state import State
from ..core.enums.chat_roles import OpenAIRolesEnum
from ..core.schemas.guide import SearchResult, ManySearchResults, SearchQueries
from ..store.nlp import NLPInterface, PromptFactory
from ..store.vectordb import VectorDBInterface


def intent_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = nlp_openai.chat(messages, "gpt-4.1")
    return {"intent": intent}


def query_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    enhanced_query = nlp_openai.structured_chat(SearchQueries, "gpt-4.1", messages)
    return {"enhanced_query": enhanced_query}


def system_node(state: State, nlp_openai: NLPInterface) -> State:
    return {"system_name": "customers_and_sales"}


def search_node(
    state: State,
    nlp_openai: NLPInterface,
    nlp_cohere: NLPInterface,
    vectordb: VectorDBInterface,
) -> State:
    enhanced_query = state.get("enhanced_query")
    system_name = state.get("system_name")
    embeddings = nlp_openai.embed(enhanced_query.queries)

    nearest = vectordb.query_chunks(embeddings, system_name, max_retrieved=40)
    nearest_unique = [dict(t) for t in {tuple(sorted(d.items())) for d in nearest}]
    reranked_nearest = nlp_cohere.rerank(
        enhanced_query.reranker_query, nearest_unique, "rerank-v3.5", 10
    )

    search_results = ManySearchResults(
        results=[
            SearchResult(
                score=float(item["score"]),
                topic=str(item["topic"]),
                text=item["text"],
            )
            for item in reranked_nearest
        ]
    )
    return {"search_results": search_results}


def formate_node(state: State) -> State:
    search_results: ManySearchResults = state.get("search_results", "")

    search_as_list = list()
    for result in search_results.results:
        search_as_list.append(f"Topic: {result.topic}\nChunk Text:\n{result.text}")

    search_as_text = "\n\n---\n\n".join(search_as_list)
    return {"formated_search": search_as_text}


def analysis_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    formated_search: ManySearchResults = state.get("formated_search", "")
    analysis_prompt = PromptFactory().get_prompt("analysis")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": analysis_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": formated_search},
    ]

    analysis = nlp_openai.chat(messages, "gpt-4.1")
    return {"analysis": analysis}


def chat_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_chat = PromptFactory().get_prompt("chat")
    user_message = state.get("user_message", "")
    analysis: ManySearchResults = state.get("analysis", "")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_chat},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": analysis},
    ]

    response = nlp_openai.chat(messages, "gpt-4.1")
    return {"response": response}


def tts_node(state: State, nlp_openai: NLPInterface) -> State:
    audio_path = nlp_openai.text_to_speech(state.get("response"))
    print(audio_path)
    return {"audio_path": audio_path}


def stt_node(state: State, nlp_openai: NLPInterface) -> State:
    user_message = nlp_openai.speech_to_text(state.get("audio_path"))
    return {"user_message": user_message}
