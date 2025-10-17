<https://gemini.google.com/share/331756d11a06>


can we collect the final ai answer on stream_workflow_events

onyx-ix-guide-api  | 2025-10-16T13:58:25.744346Z [info     ] Routed --> __classify__        [server.robot.agents.semantic]
onyx-ix-guide-api  | 2025-10-16T13:58:31.559246Z [info     ] Fusion: 5 queries, Lexical: 1 queries, Cross Encoder: 1 queries [server.robot.agents.queries]
onyx-ix-guide-api  | 2025-10-16T13:58:31.561723Z [info     ] Search pipeline started        [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:32.547221Z [info     ]    1. Embedding success        [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:35.215676Z [info     ]    2. Cosine similarity success [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:35.715100Z [info     ]    3. Probabilistic success    [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:36.761932Z [info     ]    4. Cross encoder product success [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:36.762108Z [info     ] Search pipeline end            [server.robot.agents.search]
onyx-ix-guide-api  | 2025-10-16T13:58:36.764462Z [info     ] Chat History:                  [server.robot.agents.chat]
onyx-ix-guide-api  | 2025-10-16T13:58:36.764618Z [info     ] Streaming response...          [server.robot.agents.chat]
onyx-ix-guide-api  | 2025-10-16T13:58:57.512117Z [warning  ] Chat history update skipped: user_message=True, final_ai_response=False [server.routes.endpoints.chat]

```
import structlog
from ..state import State
from ...store.nlp import PromptFactory
from ...core.enums import OpenAIRolesEnum
from ...core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.getLogger(__name__)


async def ChatAgent(state: State, generator):

    instructions = PromptFactory().get_prompt("chat")
    user_message = state.get("user_message")
    search = state.get("search", "No Search")
    history = state.get("history")

    chat_history = "Chat History: " + history
    LOGGER.info(chat_history)

    retrieved = "Retrieved Context:\n\n" + search
    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": chat_history},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": retrieved},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    LOGGER.info("Streaming response...", agent="Chat")

    async for chunk in generator.stream_chat(messages, SETTINGS.GENERATOR_LARGE):
        yield {"chunk": chunk}

```

```
import os
import json
import shutil
import asyncio
import tempfile
import logging

from typing import AsyncGenerator
from fastapi import APIRouter, Request, HTTPException, Form, BackgroundTasks
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse

from ...robot import init_workflow
from ...services import ChatHistoryServie
from ..background import update_chat_history_task
from ..utils import stream_workflow_events, _format_sse_message

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("")
async def chat(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: str = Form("default-session"),
    query: str = Form(None),
    audio: UploadFile = File(None),
):

    generator = request.app.state.generator
    embeddings = request.app.state.embeddings
    reranker = request.app.state.reranker
    vectordb = request.app.state.vectordb
    lexical_search = request.app.state.lexical_search
    cachedb = request.app.state.cachedb
    stt = request.app.state.stt

    if not query and not audio:
        raise HTTPException(
            status_code=400, detail="Either 'query' or 'audio' must be provided."
        )

    history_service = ChatHistoryServie(cachedb=cachedb, generator=generator)
    try:
        previous_summary = await history_service.get_summary(session_id)
        logger.debug(
            f"Retrieved previous summary for session {session_id}: {previous_summary}"
        )
    except Exception as e:
        logger.error(
            f"Error retrieving chat history summary for session {session_id}: {str(e)}"
        )
        previous_summary = None  # Fallback to None if retrieval fails

    workflow = init_workflow(generator, embeddings, reranker, vectordb, lexical_search)

    async def event_generator() -> AsyncGenerator[str, None]:
        user_message = query
        audio_path = None
        final_ai_response = None
        final_search_results = None

        try:
            if audio:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    shutil.copyfileobj(audio.file, tmp)
                    audio_path = tmp.name

                transcribed_text = await stt.speech_to_text(audio_path)
                user_message = transcribed_text

                transcribed_event = {
                    "event": "transcribed",
                    "data": {"user_message": user_message},
                }
                yield _format_sse_message(transcribed_event)
                await asyncio.sleep(0.01)

            streamer = stream_workflow_events(
                workflow, user_message, previous_summary or ""
            )

            async for event_str in streamer:
                if event_str.startswith("data:"):
                    try:
                        event_json = json.loads(event_str[len("data: ") : -2])
                        if event_json.get("event") == "final_answer":
                            final_data = event_json.get("data", {})
                            final_ai_response = final_data.get("answer")
                            final_search_results = final_data.get("search_results")
                            logger.debug(
                                f"Captured final AI response: {final_ai_response}"
                            )
                    except json.JSONDecodeError as json_err:
                        logger.error(
                            f"JSON decode error in event stream: {str(json_err)} - Event: {event_str}"
                        )
                    except Exception as parse_err:
                        logger.error(
                            f"Error parsing event stream: {str(parse_err)} - Event: {event_str}"
                        )
                yield event_str

            if user_message and final_ai_response:
                search_str = (
                    json.dumps(final_search_results) if final_search_results else ""
                )

                try:
                    background_tasks.add_task(
                        update_chat_history_task,
                        session_id=session_id,
                        user_message=user_message,
                        search=search_str,
                        ai_response=final_ai_response,
                        cachedb=cachedb,
                        generator=generator,
                    )
                    logger.debug(
                        f"Added background task to update chat history for session {session_id}"
                    )
                except Exception as bg_err:
                    logger.error(
                        f"Error adding background task for chat history update: {str(bg_err)}"
                    )
            else:
                logger.warning(
                    f"Chat history update skipped: user_message={bool(user_message)}, final_ai_response={bool(final_ai_response)}"
                )

        except Exception as gen_err:
            logger.error(f"Error in event generator: {str(gen_err)}")
            raise  # Re-raise to propagate the error if needed
        finally:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

```

```
import os
import time
from ..services import ChatHistoryServie
from ..core.enums import OpenAIRolesEnum
from ..store.nlp import PromptFactory


async def update_chat_history_task(
    session_id: str,
    user_message: str,
    search: str,
    ai_response: str,
    cachedb,
    generator,
):
    try:
        history_service = ChatHistoryServie(cachedb=cachedb, generator=generator)

        instructions = PromptFactory().get_prompt("history")
        previous_summary = await history_service.get_summary(session_id) or ""
        retrieved = "Retrieved Context:\n\n" + search
        old_history = "Chat History: " + previous_summary

        messages = [
            {"role": OpenAIRolesEnum.SYSTEM.value, "content": instructions},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": old_history},
            {"role": OpenAIRolesEnum.USER.value, "content": user_message},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": retrieved},
            {"role": OpenAIRolesEnum.ASSISTANT.value, "content": ai_response},
        ]

        await history_service.update_summary(session_id, messages)

    except Exception as e:
        print(f"Error in background history update for session {session_id}: {e}")


def cleanup_file_task(path: str):
    try:
        time.sleep(60)
        os.remove(path)
        print(f"Cleaned up temp file: {path}")
    except OSError as e:
        print(f"Error cleaning up file {path}: {e}")

```

```
import json
import asyncio
from typing import AsyncGenerator, Dict, Any


def _format_sse_message(event_data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event_data)}\n\n"


def _serialize_if_needed(data: Any) -> Any:
    return data.dict() if hasattr(data, "dict") else data


async def stream_workflow_events(
    workflow, user_message: str, history: str
) -> AsyncGenerator[str, None]:
    """
    Streams events from the workflow, yielding them as SSE messages.
    Captures the final AI response to be used for history update.
    """
    final_response = None
    try:
        # --- Pass history into the workflow's initial state ---
        async for event in workflow.astream_events(
            {
                "user_message": user_message,
                "history": history,
            },
            version="v2",
        ):
            kind = event["event"]
            name = event["name"]

            if kind == "on_chain_start" and name != "LangGraph":
                event_data = {"event": "start_node", "node": name}
                yield _format_sse_message(event_data)
                await asyncio.sleep(0.1)

            elif kind == "on_chain_stream" and name == "__chat__":
                if chunk := event["data"].get("chunk"):
                    event_data = {"event": "stream_chunk", "data": chunk}
                    yield _format_sse_message(event_data)
                    await asyncio.sleep(0.01)

            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"]["output"]

                final_response = final_state.get("response")
                final_payload = {
                    "answer": final_response,
                    "enhanced_query": _serialize_if_needed(final_state.get("queries")),
                    "search_results": final_state.get("search"),
                    "user_message": final_state.get("user_message"),
                }
                event_data = {"event": "final_answer", "data": final_payload}
                yield _format_sse_message(event_data)

    except Exception as e:
        print(f"Error during streaming: {e}")
        error_data = {"event": "error", "message": str(e)}
        yield _format_sse_message(error_data)

```

```
import structlog
import redis.asyncio as redis
from typing import List, Dict, Any, Optional
from ..store.nlp.interfaces.generator import BaseGenerator
from ..core.config import get_settings

SETTINGS = get_settings()
LOGGER = structlog.get_logger(__name__)


class ChatHistoryServie:
    _CACHE_KEY_PREFIX = "chat_summary"

    def __init__(self, cachedb: redis.Redis, generator: BaseGenerator):
        self.cachedb = cachedb
        self.generator = generator

    def _get_cache_key(self, session_id: str) -> str:
        return f"{self._CACHE_KEY_PREFIX}:{session_id}"

    async def get_summary(self, session_id: str) -> Optional[str]:
        cache_key = self._get_cache_key(session_id)
        summary_bytes = await self.cachedb.get(cache_key)

        if summary_bytes:
            LOGGER.info(summary_bytes.decode("utf-8"))
            return summary_bytes.decode("utf-8")

        return None

    async def update_summary(self, session_id: str, messages: List[Dict[str, Any]]):
        new_summary = await self.generator.chat(messages, SETTINGS.GENERATOR_LARGE)
        cache_key = self._get_cache_key(session_id)
        LOGGER.info(new_summary)
        await self.cachedb.set(cache_key, new_summary)

    async def delete_summary(self, session_id: str) -> int:
        cache_key = self._get_cache_key(session_id)
        await self.cachedb.delete(cache_key)

```

```
import os
import nltk
import structlog
import uvicorn
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .store.semantic import VectorDBFactory
from .store.lexical.search import LexicalSearch
from .store.lexical.index import LexicalTrainer
from .store.nlp import NLPFactory
from .routes.api import api_router as api_router_v1
from .core.logs import setup_logging

setup_logging()

LOGGER = structlog.getLogger(__name__)
SETTINGS = get_settings()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    nltk.download("stopwords")
    app.state.cachedb = redis.Redis(
        host="redis",
        port=SETTINGS.REDIS_PORT,
        decode_responses=True,
        password=SETTINGS.REDIS_PASSWORD,
    )
    app.state.generator = NLPFactory.create_generator(
        provider=SETTINGS.PROVIDER_GENERATOR
    )
    app.state.embeddings = NLPFactory.create_embeddings(
        provider=SETTINGS.PROVIDER_EMBEDDINGS
    )
    app.state.reranker = NLPFactory.create_reranker(provider=SETTINGS.PROVIDER_RERANKER)
    app.state.stt = NLPFactory.create_stt(provider=SETTINGS.PROVIDER_STT)
    app.state.tts = NLPFactory.create_tts(provider=SETTINGS.PROVIDER_TTS)

    vectordb_factory = VectorDBFactory()
    vectordb = vectordb_factory.create(provider="pinecone", settings=SETTINGS)
    vectordb.connect()
    app.state.vectordb = vectordb

    app.state.lexical_search = LexicalSearch(
        api_key=SETTINGS.PINECONE_API_KEY,
        host=SETTINGS.PINECONE_HOST_SPARSE,
        model_path=SETTINGS.PROB_MODEL_FILE,
    )

    app.state.lexical_trainer = LexicalTrainer(
        api_key=SETTINGS.PINECONE_API_KEY, host=SETTINGS.PINECONE_HOST_SPARSE
    )

    LOGGER.info("APP init success")

    yield
    vectordb.disconnect()
    await app.state.cachedb.flushdb()
    await app.state.cachedb.close()
    LOGGER.info("APP shut down success")


app = FastAPI(
    lifespan=lifespan,
    title="onyx API",
    version="0.1.0",
    contact={"email": "ramyibrahim.ai@gmail.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router_v1, prefix="/api/v1")

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

```

```
from langgraph.graph import StateGraph, END
from functools import partial
from .state import State
from .agents import ChatAgent, ClassifyAgent, QueriesAgent, SearchAgent, SemanticAgent
from ..core.enums import NodesEnum


def init_workflow(generator, embeddings, reranker, vectordb, lexical_search):

    nodes = {
        NodesEnum.CHAT.value: partial(ChatAgent, generator=generator),
        NodesEnum.CLASSIFY.value: partial(ClassifyAgent, generator=generator),
        NodesEnum.QUERIES.value: partial(QueriesAgent, generator=generator),
        NodesEnum.SEMANTIC_ROUTER.value: partial(SemanticAgent, generator=generator),
        NodesEnum.SEARCH.value: partial(
            SearchAgent,
            embeddings=embeddings,
            reranker=reranker,
            vectordb=vectordb,
            lexical_search=lexical_search,
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
            "__end__": END,
        },
    )

    workflow.add_edge(NodesEnum.CLASSIFY.value, NodesEnum.QUERIES.value)
    workflow.add_edge(NodesEnum.QUERIES.value, NodesEnum.SEARCH.value)
    workflow.add_edge(NodesEnum.SEARCH.value, NodesEnum.CHAT.value)
    workflow.add_edge(NodesEnum.CHAT.value, END)

    return workflow.compile()
```

```
from typing_extensions import TypedDict
from ..core.schemas import Queries


class State(TypedDict):
    user_message: str
    intent: str
    system_name: str
    queries: Queries
    search: str
    response: str
    history: str
    route: str
```


```
from enum import Enum


class NodesEnum(Enum):
    SEMANTIC_ROUTER = "__semantic__"
    CLASSIFY = "__classify__"
    QUERIES = "__queries__"
    SEARCH = "__search__"
    CHAT = "__chat__"
    TTS = "__tts__"
    STT = "__stt__"
```