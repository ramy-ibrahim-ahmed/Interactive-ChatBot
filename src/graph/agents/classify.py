from ..state import State
from ...store.nlp import NLPInterface


def system_node(state: State, nlp_openai: NLPInterface) -> State:
    return {"system_name": "customers_v3"}
