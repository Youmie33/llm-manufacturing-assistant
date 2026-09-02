from core.router.query_router import QueryRouter
from core.router.source_router import SourceRouter


class Router:
    def __init__(self, embedder):
        self.query_router = QueryRouter()
        self.source_router = SourceRouter(embedder)

    def route(self, query, sources=None):
        mode = self.query_router.route(query)

        selected_sources = []
        if sources:
            selected_sources = self.source_router.select_sources(query, sources)

        return {
            "mode": mode,
            "sources": selected_sources
        }