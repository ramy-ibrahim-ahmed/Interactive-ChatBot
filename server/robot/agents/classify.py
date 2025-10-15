from ..state import State
from ...store.nlp.interfaces import BaseGenerator


async def ClassifyAgent(state: State, generator: BaseGenerator) -> State:
    return {"system_name": "customers"}
