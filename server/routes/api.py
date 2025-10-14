from fastapi import APIRouter
from .endpoints import chat, chunk, extract, index

api_router = APIRouter()

api_router.include_router(chat.router)
api_router.include_router(extract.router)
api_router.include_router(chunk.router)
api_router.include_router(index.router)
