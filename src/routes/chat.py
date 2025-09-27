from pydantic import BaseModel
from fastapi import APIRouter, Request
from ..store.nlp import NLPInterface
from ..store.vectordb import VectorDBInterface
from ..graph import init_workflow

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)


class Query(BaseModel):
    query: str


@router.post("")
async def chat(request: Request, query: Query):
    vectordb: VectorDBInterface = request.app.state.vectordb
    nlp_openai: NLPInterface = request.app.state.nlp_openai
    nlp_cohere: NLPInterface = request.app.state.nlp_cohere

    workflow = init_workflow(nlp_openai, nlp_cohere, vectordb)
    config = {"configurable": {"thread_id": "user-123"}}
    response = workflow.invoke({"user_message": query.query}, config)

    if response.get("intent") != "ERP":
        return {
            "answer": "I cant help.",
            "intent": response["intent"],
            "search_results": "",
        }

    return {
        "answer": response.get("response"),
        "analysis": response.get("analysis"),
        "enhanced_query": response.get("enhanced_query"),
        "search_results": response.get("search_results"),
    }
