import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .store.vectordb import VectorDBFactory
from .store.nlp import NLPFactory
from .routes import chat_router, extract_router, process_router


SETTINGS = get_settings()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.nlp_openai = NLPFactory.create(provider="openai")
    app.state.nlp_cohere = NLPFactory.create(provider="cohere")
    vectordb_factory = VectorDBFactory()
    vectordb = vectordb_factory.create(provider="pinecone", settings=SETTINGS)
    vectordb.connect()
    app.state.vectordb = vectordb
    app.state.settings = SETTINGS

    yield
    vectordb.disconnect()


app = FastAPI(
    lifespan=lifespan,
    title="onyx-helpbot API",
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

app.include_router(chat_router)
app.include_router(extract_router)
app.include_router(process_router)
