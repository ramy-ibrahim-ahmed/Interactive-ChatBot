from langgraph.graph import StateGraph, END
from functools import partial
from .state import State
from .agents import ChatAgent, ClassifyAgent, QueriesAgent, SearchAgent, SemanticAgent
from ..core.enums import NodesEnum


def init_workflow(generator, embeddings, reranker, vectordb):

    nodes = {
        NodesEnum.CHAT.value: partial(ChatAgent, generator=generator),
        NodesEnum.CLASSIFY.value: partial(ClassifyAgent, generator=generator),
        NodesEnum.QUERIES.value: partial(QueriesAgent, generator=generator),
        NodesEnum.SEMANTIC_ROUTER.value: partial(SemanticAgent, generator=generator),
        NodesEnum.SEARCH.value: partial(
            SearchAgent, embeddings=embeddings, reranker=reranker, vectordb=vectordb
        ),
    }

    workflow = StateGraph(State)

    for name, node in nodes.items():
        workflow.add_node(name, node)

    workflow.set_entry_point(NodesEnum.SEMANTIC_ROUTER.value)

    workflow.add_conditional_edges(
        NodesEnum.SEMANTIC_ROUTER.value,
        lambda state: state.get("route", "__end__"),
        {
            "__classify__": NodesEnum.CLASSIFY.value,
            "__chat__": NodesEnum.CHAT.value,
        },
    )

    workflow.add_edge(NodesEnum.CLASSIFY.value, NodesEnum.QUERIES.value)
    workflow.add_edge(NodesEnum.QUERIES.value, NodesEnum.SEARCH.value)
    workflow.add_edge(NodesEnum.SEARCH.value, NodesEnum.CHAT.value)
    workflow.add_edge(NodesEnum.CHAT.value, END)

    return workflow.compile()
