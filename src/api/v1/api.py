from fastapi import APIRouter
from .endpoints import chat, extract, process

api_router = APIRouter()

api_router.include_router(chat.router)
api_router.include_router(extract.router)
api_router.include_router(process.router)
