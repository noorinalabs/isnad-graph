"""Search endpoints: full-text and semantic."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api.deps import get_neo4j
from src.api.models import SearchResult, SearchResultsResponse
from src.utils.neo4j_client import Neo4jClient

router = APIRouter()


@router.get("/search", response_model=SearchResultsResponse)
def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    neo4j: Neo4jClient = Depends(get_neo4j),
) -> SearchResultsResponse:
    """Full-text search across hadiths and narrators."""
    results: list[SearchResult] = []

    # Search narrators by name
    narrator_rows = neo4j.execute_read(
        """
        MATCH (n:Narrator)
        WHERE n.name_ar CONTAINS $q OR n.name_en CONTAINS $q
        RETURN n.id AS id, n.name_ar AS name_ar, n.name_en AS name_en,
               'narrator' AS type, 1.0 AS score
        LIMIT $limit
        """,
        {"q": q, "limit": limit},
    )
    for r in narrator_rows:
        results.append(
            SearchResult(
                id=r["id"],
                type="narrator",
                title=r.get("name_en") or r["name_ar"],
                title_ar=r["name_ar"],
                score=r["score"],
            )
        )

    # Search hadiths by matn text
    remaining = max(0, limit - len(results))
    if remaining > 0:
        hadith_rows = neo4j.execute_read(
            """
            MATCH (h:Hadith)
            WHERE h.matn_ar CONTAINS $q OR h.matn_en CONTAINS $q
            RETURN h.id AS id, h.matn_ar AS matn_ar, h.matn_en AS matn_en,
                   'hadith' AS type, 1.0 AS score
            LIMIT $limit
            """,
            {"q": q, "limit": remaining},
        )
        for r in hadith_rows:
            snippet = r.get("matn_en") or r["matn_ar"]
            results.append(
                SearchResult(
                    id=r["id"],
                    type="hadith",
                    title=snippet[:120] + "..." if len(snippet) > 120 else snippet,
                    title_ar=r["matn_ar"][:120],
                    score=r["score"],
                )
            )

    return SearchResultsResponse(results=results, total=len(results), query=q)


@router.get("/search/semantic", response_model=SearchResultsResponse)
def search_semantic(
    q: str = Query(..., min_length=1, max_length=500, description="Semantic search query"),
    limit: int = Query(10, ge=1, le=50),
) -> SearchResultsResponse:
    """Semantic similarity search using pgvector.

    Returns 503 when the pgvector backend is not available.
    """
    # pgvector integration is not yet wired up — return a graceful 503
    return JSONResponse(  # type: ignore[return-value]
        status_code=503,
        content={
            "detail": "Semantic search is not yet available. pgvector backend required.",
            "query": q,
        },
    )
