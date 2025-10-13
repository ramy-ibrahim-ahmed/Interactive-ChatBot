import os
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import get_settings
from .store.semantic import VectorDBFactory
from .store.lexical.search import LexicalSearch
from .store.nlp import NLPFactory
from .routes.api import api_router as api_router_v1


SETTINGS = get_settings()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cachedb = redis.Redis(
        host="localhost",
        port=SETTINGS.REDIS_PORT,
        decode_responses=True,
        password=SETTINGS.REDIS_PASSWORD,
    )
    app.state.generator = NLPFactory.create_generator(provider="gemini")
    app.state.embeddings = NLPFactory.create_embeddings(provider="cohere")
    app.state.reranker = NLPFactory.create_reranker(provider="cohere")
    app.state.stt = NLPFactory.create_stt(provider="openai")
    app.state.tts = NLPFactory.create_tts(provider="openai")

    vectordb_factory = VectorDBFactory()
    vectordb = vectordb_factory.create(provider="pinecone", settings=SETTINGS)
    vectordb.connect()
    app.state.vectordb = vectordb

    app.state.lexical_search = LexicalSearch(
        api_key=SETTINGS.PINECONE_API_KEY,
        host=SETTINGS.PINECONE_HOST_SPARSE,
        model_path=SETTINGS.PROB_MODEL_FILE,
    )

    app.state.settings = SETTINGS

    yield
    vectordb.disconnect()
    await app.state.cachedb.flushdb()
    await app.state.cachedb.close()


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

app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(BASE_DIR, "assets")),
    name="assets",
)

app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="root")
