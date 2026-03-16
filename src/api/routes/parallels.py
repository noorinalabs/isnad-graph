"""Parallel hadith endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_neo4j
from src.api.models import ParallelHadithResponse, ParallelsResponse
from src.utils.neo4j_client import Neo4jClient

router = APIRouter()


@router.get("/parallels/{hadith_id}", response_model=ParallelsResponse)
def get_parallels(
    hadith_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100),
    neo4j: Neo4jClient = Depends(get_neo4j),
) -> ParallelsResponse:
    """Return parallel hadiths via PARALLEL_OF relationships."""
    exists = neo4j.execute_read(
        "MATCH (h:Hadith {id: $id}) RETURN h.id AS id",
        {"id": hadith_id},
    )
    if not exists:
        raise HTTPException(status_code=404, detail=f"Hadith '{hadith_id}' not found")

    skip = (page - 1) * limit

    rows = neo4j.execute_read(
        """
        MATCH (h:Hadith {id: $id})-[r:PARALLEL_OF]-(p:Hadith)
        RETURN p.id AS id, p.matn_ar AS matn_ar, p.matn_en AS matn_en,
               p.source_corpus AS source_corpus, p.grade_composite AS grade,
               r.similarity_score AS similarity_score,
               r.variant_type AS variant_type,
               r.cross_sect AS cross_sect
        ORDER BY r.similarity_score DESC
        SKIP $skip
        LIMIT $limit
        """,
        {"id": hadith_id, "skip": skip, "limit": limit},
    )

    parallels = [
        ParallelHadithResponse(
            id=r["id"],
            matn_ar=r["matn_ar"],
            matn_en=r.get("matn_en"),
            source_corpus=r.get("source_corpus", ""),
            grade=r.get("grade"),
            similarity_score=r.get("similarity_score"),
            variant_type=r.get("variant_type"),
            cross_sect=bool(r.get("cross_sect", False)),
        )
        for r in rows
    ]
    return ParallelsResponse(hadith_id=hadith_id, parallels=parallels, total=len(parallels))
