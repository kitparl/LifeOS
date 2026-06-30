from pydantic import BaseModel


class SearchResultItem(BaseModel):
    module: str
    entity_type: str
    id: str
    title: str
    subtitle: str | None = None
    route: str


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem]
