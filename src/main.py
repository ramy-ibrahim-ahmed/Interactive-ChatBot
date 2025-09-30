import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import get_settings
from .store.vectordb import VectorDBFactory
from .store.nlp import NLPFactory
from .api import api_router_v1


SETTINGS = get_settings()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.nlp_openai = NLPFactory.create(provider="openai")
    app.state.nlp_gemini = NLPFactory.create(provider="gemini")
    app.state.nlp_cohere = NLPFactory.create(provider="cohere")
    vectordb_factory = VectorDBFactory()
    vectordb = vectordb_factory.create(provider="pinecone", settings=SETTINGS)
    vectordb.connect()
    app.state.vectordb = vectordb
    app.state.settings = SETTINGS

    yield
    vectordb.disconnect()


# ... (imports and lifespan function) ...

app = FastAPI(
    lifespan=lifespan,
    title="onyx API",
    version="0.1.0",
    contact={"email": "ramyibrahim.ai@gmail.com"},
)

# Add Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Register the API router FIRST
app.include_router(api_router_v1, prefix="/api/v1")

# 2. Mount static files AFTER the API router
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets"
)

app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="root")
