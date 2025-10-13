from langgraph.graph import StateGraph, END
from functools import partial
from .state import State
from .agents import (
    query_node,
    search_node,
    formate_node,
    chat_node,
    intent_node,
    system_node,
    history_node,
)


def router_intent(state: State):
    if state.get("intent") == "ERP":
        return "query_write"
    return END


def init_workflow(generator, embeddings, reranker, vectordb, cachedb):
    query_agent = partial(query_node, generator=generator)
    search_agent = partial(
        search_node, embeddings=embeddings, reranker=reranker, vectordb=vectordb
    )
    formate_agent = formate_node
    chat_agent = partial(chat_node, generator=generator, cachedb=cachedb)
    intent_agent = partial(intent_node, generator=generator)
    system_agent = partial(system_node, generator=generator)
    history_agent = partial(history_node, cachedb=cachedb)

    workflow = StateGraph(State)
    workflow.add_node("classify_intent", intent_agent)
    workflow.add_node("system_recognize", system_agent)
    workflow.add_node("query_write", query_agent)
    workflow.add_node("search", search_agent)
    workflow.add_node("formate_search", formate_agent)
    workflow.add_node("chat", chat_agent)
    workflow.add_node("history", history_agent)

    workflow.set_entry_point("history")
    workflow.add_edge("history", "query_write")

    # workflow.add_edge("history", "classify_intent")

    # workflow.add_conditional_edges(
    #     "classify_intent",
    #     router_intent,
    #     {"query_write": "query_write", END: END},
    # )

    workflow.add_edge("query_write", "system_recognize")
    workflow.add_edge("system_recognize", "search")
    workflow.add_edge("search", "formate_search")
    workflow.add_edge("formate_search", "chat")
    workflow.add_edge("chat", END)
    return workflow.compile()
