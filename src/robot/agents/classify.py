from ..state import State
from ...store.nlp.interfaces import BaseGenerator


def system_node(state: State, generator: BaseGenerator) -> State:
    return {"system_name": "customers"}
