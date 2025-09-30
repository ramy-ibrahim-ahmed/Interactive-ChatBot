from langgraph.graph import StateGraph, END
from functools import partial
from .state import State
from .nodes import (
    query_node,
    search_node,
    formate_node,
    chat_node,
    intent_node,
    analysis_node,
    system_node,
    tts_node,
)


def router_intent(state: State):
    if state.get("intent") == "ERP":
        return "query_write"
    return END


def init_workflow(nlp_openai, nlp_gemini, nlp_cohere, vectordb):
    query_agent = partial(query_node, nlp_openai=nlp_openai)
    search_agent = partial(
        search_node, nlp_openai=nlp_openai, nlp_cohere=nlp_cohere, vectordb=vectordb
    )
    formate_agent = formate_node
    chat_agent = partial(chat_node, nlp_openai=nlp_openai)
    intent_agent = partial(intent_node, nlp_openai=nlp_openai)
    analysis_agent = partial(analysis_node, nlp_openai=nlp_gemini)
    system_agent = partial(system_node, nlp_openai=nlp_openai)
    tts_agent = partial(tts_node, nlp_openai=nlp_openai)

    workflow = StateGraph(State)
    workflow.add_node("classify_intent", intent_agent)
    workflow.add_node("system_recognize", system_agent)
    workflow.add_node("query_write", query_agent)
    workflow.add_node("search", search_agent)
    workflow.add_node("formate_search", formate_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("chat", chat_agent)
    workflow.add_node("tts", tts_agent)

    workflow.set_entry_point("classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        router_intent,
        {"query_write": "query_write", END: END},
    )
    workflow.add_edge("query_write", "system_recognize")
    workflow.add_edge("system_recognize", "search")
    workflow.add_edge("search", "formate_search")
    workflow.add_edge("formate_search", "analysis")
    workflow.add_edge("analysis", "chat")
    workflow.add_edge("chat", "tts")
    workflow.add_edge("tts", END)

    return workflow.compile()
