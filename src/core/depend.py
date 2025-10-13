# app/dependencies.py

from functools import lru_cache
from ..store.nlp import NLPFactory, BaseNLP
from ..store.semantic import VectorDBFactory, BaseVectorDB
from .config import get_settings

# This dictionary will act as a simple in-memory cache for our clients.
# This ensures we only create one instance of each client for the entire application life.
_clients = {}

# Use settings singleton for convenience
SETTINGS = get_settings()


def get_vectordb() -> BaseVectorDB:
    if "vectordb" not in _clients:
        vectordb_factory = VectorDBFactory()
        vectordb = vectordb_factory.create(provider="pinecone", settings=SETTINGS)
        vectordb.connect()
        _clients["vectordb"] = vectordb
    return _clients["vectordb"]


def get_openai_client() -> BaseNLP:
    if "openai" not in _clients:
        _clients["openai"] = NLPFactory.create(provider="openai")
    return _clients["openai"]


def get_gemini_client() -> BaseNLP:
    if "gemini" not in _clients:
        _clients["gemini"] = NLPFactory.create(provider="gemini")
    return _clients["gemini"]


def get_cohere_client() -> BaseNLP:
    if "cohere" not in _clients:
        _clients["cohere"] = NLPFactory.create(provider="cohere")
    return _clients["cohere"]


def get_ollama_client() -> BaseNLP:
    if "ollama" not in _clients:
        _clients["ollama"] = NLPFactory.create(provider="ollama")
    return _clients["ollama"]
