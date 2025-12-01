"""
Query History API Endpoints

Tracks and retrieves query history for analytics and audit.
Enhancement #2: Query History Backend
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.query_history import (
    QueryHistory,
    QueryHistoryCreate,
    QueryHistoryResponse,
    QueryHistoryListResponse,
    QueryHistoryStats,
)
from app.models.user import User
from loguru import logger


router = APIRouter()


# Query History CRUD Endpoints

@router.post("/", response_model=QueryHistory, summary="Create query history entry")
async def create_query_history(
    query_data: QueryHistoryCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new query history entry.

    This is typically called automatically after query execution,
    but can also be called manually for tracking purposes.
    """
    try:
        query = text("""
            INSERT INTO query_history (
                user_id, customer_id, query_text, intent, answer,
                confidence, source_documents, reasoning_path, execution_time_ms
            )
            VALUES (
                :user_id, :customer_id, :query_text, :intent, :answer,
                :confidence, :source_documents, :reasoning_path, :execution_time_ms
            )
            RETURNING *
        """)

        result = await db.execute(
            query,
            {
                "user_id": str(user.id),
                "customer_id": str(query_data.customer_id) if query_data.customer_id else None,
                "query_text": query_data.query_text,
                "intent": query_data.intent,
                "answer": query_data.answer,
                "confidence": query_data.confidence,
                "source_documents": query_data.source_documents,
                "reasoning_path": query_data.reasoning_path,
                "execution_time_ms": query_data.execution_time_ms,
            },
        )
        await db.commit()

        row = result.first()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create query history")

        logger.info(f"Created query history entry for user {user.id}")
        return QueryHistory(**dict(row._mapping))

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create query history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create query history: {str(e)}")


@router.get("/", response_model=QueryHistoryListResponse, summary="List query history")
async def list_query_history(
    customer_id: Optional[UUID] = QueryParam(None, description="Filter by customer"),
    intent: Optional[str] = QueryParam(None, description="Filter by intent"),
    date_from: Optional[datetime] = QueryParam(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = QueryParam(None, description="End date (ISO format)"),
    search: Optional[str] = QueryParam(None, description="Search in query text"),
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of query history for the current user.

    Supports:
    - Filter by customer, intent, date range
    - Search in query text
    - Pagination
    """
    try:
        # Build WHERE conditions
        conditions = [f"qh.user_id = '{user.id}'"]

        if customer_id:
            conditions.append(f"qh.customer_id = '{customer_id}'")

        if intent:
            intent_safe = intent.replace("'", "''")
            conditions.append(f"qh.intent = '{intent_safe}'")

        if date_from:
            conditions.append(f"qh.created_at >= '{date_from.isoformat()}'")

        if date_to:
            conditions.append(f"qh.created_at <= '{date_to.isoformat()}'")

        if search:
            search_term = search.replace("'", "''")
            conditions.append(f"qh.query_text ILIKE '%{search_term}%'")

        where_clause = " AND ".join(conditions)

        # Count total
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM query_history qh
            WHERE {where_clause}
        """)
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results with customer name
        offset = (page - 1) * page_size
        list_query = text(f"""
            SELECT
                qh.id,
                qh.query_text,
                qh.intent,
                LEFT(qh.answer, 200) as answer_preview,
                qh.confidence,
                qh.customer_id,
                c.name as customer_name,
                qh.execution_time_ms,
                qh.created_at
            FROM query_history qh
            LEFT JOIN customers c ON qh.customer_id = c.id
            WHERE {where_clause}
            ORDER BY qh.created_at DESC
            LIMIT {page_size} OFFSET {offset}
        """)

        result = await db.execute(list_query)
        rows = result.fetchall()

        items = [QueryHistoryResponse(**dict(row._mapping)) for row in rows]

        return QueryHistoryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total,
        )

    except Exception as e:
        logger.error(f"Failed to list query history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list query history: {str(e)}")


@router.get("/stats", response_model=QueryHistoryStats, summary="Get query statistics")
async def get_query_stats(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get query statistics for the current user.

    Includes:
    - Total queries
    - Queries by time period (today, week, month)
    - Average confidence and execution time
    - Top intents
    - Queries by customer
    """
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Main stats query
        stats_query = text(f"""
            SELECT
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE created_at >= '{today.isoformat()}') as queries_today,
                COUNT(*) FILTER (WHERE created_at >= '{week_ago.isoformat()}') as queries_this_week,
                COUNT(*) FILTER (WHERE created_at >= '{month_ago.isoformat()}') as queries_this_month,
                AVG(confidence) as avg_confidence,
                AVG(execution_time_ms) as avg_execution_time_ms
            FROM query_history
            WHERE user_id = '{user.id}'
        """)

        result = await db.execute(stats_query)
        row = result.first()

        stats_data = dict(row._mapping)

        # Top intents
        intents_query = text(f"""
            SELECT intent, COUNT(*) as count
            FROM query_history
            WHERE user_id = '{user.id}' AND intent IS NOT NULL
            GROUP BY intent
            ORDER BY count DESC
            LIMIT 5
        """)

        intents_result = await db.execute(intents_query)
        top_intents = [
            {"intent": row.intent, "count": row.count}
            for row in intents_result.fetchall()
        ]

        # Queries by customer (top 5)
        customers_query = text(f"""
            SELECT
                c.id,
                c.name,
                COUNT(qh.id) as query_count
            FROM query_history qh
            JOIN customers c ON qh.customer_id = c.id
            WHERE qh.user_id = '{user.id}' AND qh.customer_id IS NOT NULL
            GROUP BY c.id, c.name
            ORDER BY query_count DESC
            LIMIT 5
        """)

        customers_result = await db.execute(customers_query)
        queries_by_customer = [
            {
                "customer_id": str(row.id),
                "customer_name": row.name,
                "query_count": row.query_count,
            }
            for row in customers_result.fetchall()
        ]

        return QueryHistoryStats(
            total_queries=stats_data["total_queries"] or 0,
            queries_today=stats_data["queries_today"] or 0,
            queries_this_week=stats_data["queries_this_week"] or 0,
            queries_this_month=stats_data["queries_this_month"] or 0,
            avg_confidence=stats_data["avg_confidence"],
            avg_execution_time_ms=int(stats_data["avg_execution_time_ms"])
            if stats_data["avg_execution_time_ms"]
            else None,
            top_intents=top_intents,
            queries_by_customer=queries_by_customer,
        )

    except Exception as e:
        logger.error(f"Failed to get query stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {str(e)}")


@router.get("/{query_id}", response_model=QueryHistory, summary="Get query history detail")
async def get_query_history(
    query_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed query history entry by ID.

    Includes full answer, source documents, and reasoning path.
    """
    try:
        query = text("""
            SELECT * FROM query_history
            WHERE id = :query_id AND user_id = :user_id
        """)

        result = await db.execute(
            query, {"query_id": str(query_id), "user_id": str(user.id)}
        )
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Query history not found")

        return QueryHistory(**dict(row._mapping))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")


@router.delete("/{query_id}", summary="Delete query history entry")
async def delete_query_history(
    query_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a query history entry.

    Only the user who created the query can delete it.
    """
    try:
        # Check if exists and belongs to user
        check_query = text("""
            SELECT id FROM query_history
            WHERE id = :query_id AND user_id = :user_id
        """)

        result = await db.execute(
            check_query, {"query_id": str(query_id), "user_id": str(user.id)}
        )

        if not result.first():
            raise HTTPException(status_code=404, detail="Query history not found")

        # Delete
        delete_query = text("""
            DELETE FROM query_history
            WHERE id = :query_id AND user_id = :user_id
        """)

        await db.execute(
            delete_query, {"query_id": str(query_id), "user_id": str(user.id)}
        )
        await db.commit()

        logger.info(f"Deleted query history {query_id} for user {user.id}")
        return {"message": "Query history deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete query history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete query history: {str(e)}")


@router.get("/customer/{customer_id}/history", response_model=QueryHistoryListResponse)
async def get_customer_query_history(
    customer_id: UUID,
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(10, ge=1, le=50),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get query history for a specific customer.

    This is useful for the customer detail page to show
    all queries related to this customer.
    """
    # Verify customer belongs to user
    customer_check = text("""
        SELECT id FROM customers
        WHERE id = :customer_id AND fp_user_id = :user_id
    """)

    result = await db.execute(
        customer_check, {"customer_id": str(customer_id), "user_id": str(user.id)}
    )

    if not result.first():
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get query history
    return await list_query_history(
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        user=user,
        db=db,
    )
