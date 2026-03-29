"""Admin user management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_neo4j
from src.api.models import PaginatedResponse, UserUpdateRequest
from src.auth.models import UserPublic
from src.utils.neo4j_client import Neo4jClient

router = APIRouter(prefix="/users")


def _user_from_record(r: dict[str, Any]) -> UserPublic:
    """Build a UserPublic from a Neo4j user record, stripping password_hash."""
    u: dict[str, Any] = r["u"]
    return UserPublic(
        id=u["id"],
        email=u.get("email", ""),
        name=u.get("name", ""),
        provider=u.get("provider", ""),
        provider_user_id=u.get("provider_user_id", u["id"]),
        created_at=u.get("created_at", ""),
        is_admin=u.get("is_admin", False),
        is_suspended=u.get("is_suspended", False),
        role=u.get("role"),
    )


@router.get("", response_model=PaginatedResponse[UserPublic])
def list_users(
    neo4j: Neo4jClient = Depends(get_neo4j),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None),
) -> PaginatedResponse[UserPublic]:
    """List users with optional search and role filters."""
    params: dict[str, object] = {"skip": (page - 1) * limit, "limit": limit}
    where_clauses: list[str] = []

    if search:
        where_clauses.append("(u.name CONTAINS $search OR u.email CONTAINS $search)")
        params["search"] = search
    if role:
        where_clauses.append("u.role = $role")
        params["role"] = role

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_query = f"MATCH (u:USER) {where} RETURN count(u) AS total"
    count_result = neo4j.execute_read(count_query, params)
    total = count_result[0]["total"] if count_result else 0

    query = f"""
        MATCH (u:USER) {where}
        RETURN u ORDER BY u.created_at DESC
        SKIP $skip LIMIT $limit
    """
    records = neo4j.execute_read(query, params)
    items = [_user_from_record(r) for r in records]

    return PaginatedResponse[UserPublic](items=items, total=total, page=page, limit=limit)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: str,
    neo4j: Neo4jClient = Depends(get_neo4j),
) -> UserPublic:
    """Get a single user by ID."""
    query = "MATCH (u:USER {id: $user_id}) RETURN u"
    records = neo4j.execute_read(query, {"user_id": user_id})

    if not records:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_from_record(records[0])


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: str,
    body: UserUpdateRequest,
    neo4j: Neo4jClient = Depends(get_neo4j),
) -> UserPublic:
    """Update user properties (suspend, promote, change role)."""
    set_clauses: list[str] = []
    params: dict[str, object] = {"user_id": user_id}

    if body.is_admin is not None:
        set_clauses.append("u.is_admin = $is_admin")
        params["is_admin"] = body.is_admin
    if body.is_suspended is not None:
        set_clauses.append("u.is_suspended = $is_suspended")
        params["is_suspended"] = body.is_suspended
    if body.role is not None:
        set_clauses.append("u.role = $role")
        params["role"] = body.role

    if not set_clauses:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"""
        MATCH (u:USER {{id: $user_id}})
        SET {", ".join(set_clauses)}
        RETURN u
    """
    records = neo4j.execute_write(query, params)

    if not records:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_from_record(records[0])
