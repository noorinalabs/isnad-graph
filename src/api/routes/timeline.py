"""Timeline data endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_neo4j
from src.api.models import TimelineEntry, TimelineResponse
from src.utils.neo4j_client import Neo4jClient

router = APIRouter()


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    start_year: int | None = Query(None, description="Start year AH (inclusive)"),
    end_year: int | None = Query(None, description="End year AH (inclusive)"),
    neo4j: Neo4jClient = Depends(get_neo4j),
) -> TimelineResponse:
    """Return historical events with narrator counts per period for timeline visualization."""
    where_clauses: list[str] = []
    params: dict[str, int] = {}
    if start_year is not None:
        where_clauses.append("e.year_ah >= $start_year")
        params["start_year"] = start_year
    if end_year is not None:
        where_clauses.append("e.year_ah <= $end_year")
        params["end_year"] = end_year

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    rows = neo4j.execute_read(
        f"""
        MATCH (e:HistoricalEvent)
        {where}
        OPTIONAL MATCH (n:Narrator)-[:ACTIVE_DURING]->(e)
        RETURN e.id AS id, e.name AS name, e.name_ar AS name_ar,
               e.year_ah AS year_ah, e.end_year_ah AS end_year_ah,
               e.event_type AS event_type, e.description AS description,
               count(DISTINCT n) AS narrator_count
        ORDER BY e.year_ah
        """,
        params,
    )

    entries = [
        TimelineEntry(
            id=r["id"],
            name=r.get("name", ""),
            name_ar=r.get("name_ar"),
            year_ah=r["year_ah"],
            end_year_ah=r.get("end_year_ah"),
            event_type=r.get("event_type"),
            description=r.get("description"),
            narrator_count=r.get("narrator_count", 0),
        )
        for r in rows
    ]
    return TimelineResponse(entries=entries, total=len(entries))
