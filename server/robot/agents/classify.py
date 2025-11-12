import structlog
from ..state import State
from ...store.nlp.interfaces import BaseGenerator

LOGGER = structlog.get_logger(__name__)


async def ClassifyAgent(state: State, generator: BaseGenerator) -> State:
    system_name = "customers"
    LOGGER.info(f"System: {system_name}")
    return {"system_name": system_name}
