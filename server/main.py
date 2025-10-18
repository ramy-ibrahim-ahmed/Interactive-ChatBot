import os
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
    app.state.cachedb = redis.Redis(
        host="redis",
        port=SETTINGS.REDIS_PORT,
        decode_responses=True,
        password=SETTINGS.REDIS_PASSWORD,
    )
    app.state.generators = {
        "openai": NLPFactory.create_generator(provider="openai"),
        "cohere": NLPFactory.create_generator(provider="ollama"),
        "gemini": NLPFactory.create_generator(provider="gemini"),
    }
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
