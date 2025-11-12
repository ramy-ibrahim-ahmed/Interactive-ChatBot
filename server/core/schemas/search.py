from pydantic import BaseModel


class Result(BaseModel):
    score: float
    text: str


class SearchResults(BaseModel):
    results: list[Result]
