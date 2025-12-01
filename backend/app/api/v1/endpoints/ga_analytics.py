"""
GA Manager Analytics API Endpoints

Enhancement #4: GA Manager View
Provides team-wide analytics for GA Managers (FP_MANAGER role).
"""
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from loguru import logger


router = APIRouter()


# Response Models

class FPPerformance(BaseModel):
    """Individual FP performance metrics."""
    fp_id: str
    fp_name: str
    total_customers: int
    active_customers: int
    total_policies: int
    total_queries: int
    avg_query_confidence: float | None
    last_activity: str | None


class GATeamMetrics(BaseModel):
    """Team-wide metrics for GA Manager."""
    # Overview
    total_fps: int
    active_fps: int

    # Customer metrics
    total_customers: int
    active_customers: int
    new_customers_this_month: int

    # Policy metrics
    total_policies: int
    total_coverage_amount: float
    total_monthly_premium: float

    # Query metrics
    total_queries: int
    queries_today: int
    queries_this_week: int
    queries_this_month: int
    avg_query_confidence: float | None

    # Coverage breakdown
    coverage_breakdown: List[Dict[str, Any]]

    # Top performing FPs
    top_fps: List[FPPerformance]


# Helper function

def check_fp_manager_role(user: User):
    """Check if user has FP_MANAGER role."""
    if user.role != UserRole.FP_MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Access denied. This endpoint is only available for GA Managers (FP_MANAGER role)."
        )


# Endpoints

@router.get("/overview", response_model=GATeamMetrics, summary="Get GA team overview")
async def get_ga_team_overview(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get team-wide analytics for GA Manager.

    Only accessible by users with FP_MANAGER role.
    Aggregates metrics across all FPs in the same organization.
    """
    check_fp_manager_role(user)

    if not user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="GA Manager must be associated with an organization"
        )

    try:
        org_id = str(user.organization_id)
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Get all FPs in organization
        fps_query = text(f"""
            SELECT
                user_id as id,
                full_name,
                last_login_at
            FROM users
            WHERE organization_id = '{org_id}'
              AND role = 'fp'
              AND is_active = true
        """)

        fps_result = await db.execute(fps_query)
        fps = fps_result.fetchall()

        total_fps = len(fps)
        active_fps = sum(1 for fp in fps if fp.last_login_at and
                         datetime.fromisoformat(str(fp.last_login_at).replace('+00:00', '')) > month_ago)

        # Get customer metrics
        fp_ids = [str(fp.id) for fp in fps]
        fp_ids_str = "', '".join(fp_ids) if fp_ids else ""

        if not fp_ids_str:
            # No FPs in organization
            return GATeamMetrics(
                total_fps=0,
                active_fps=0,
                total_customers=0,
                active_customers=0,
                new_customers_this_month=0,
                total_policies=0,
                total_coverage_amount=0.0,
                total_monthly_premium=0.0,
                total_queries=0,
                queries_today=0,
                queries_this_week=0,
                queries_this_month=0,
                avg_query_confidence=None,
                coverage_breakdown=[],
                top_fps=[],
            )

        customer_metrics_query = text(f"""
            SELECT
                COUNT(*) as total_customers,
                COUNT(*) FILTER (WHERE last_contact_date >= '{month_ago.isoformat()}') as active_customers,
                COUNT(*) FILTER (WHERE created_at >= '{month_ago.isoformat()}') as new_customers
            FROM customers
            WHERE fp_user_id IN ('{fp_ids_str}')
        """)

        customer_result = await db.execute(customer_metrics_query)
        customer_row = customer_result.first()

        # Get policy metrics
        policy_metrics_query = text(f"""
            SELECT
                COUNT(*) as total_policies,
                COALESCE(SUM(coverage_amount), 0) as total_coverage,
                COALESCE(SUM(premium), 0) as total_premium
            FROM customer_policies cp
            JOIN customers c ON cp.customer_id = c.id
            WHERE c.fp_user_id IN ('{fp_ids_str}')
              AND cp.status = 'active'
        """)

        policy_result = await db.execute(policy_metrics_query)
        policy_row = policy_result.first()

        # Get query metrics
        query_metrics_query = text(f"""
            SELECT
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE created_at >= '{today.isoformat()}') as queries_today,
                COUNT(*) FILTER (WHERE created_at >= '{week_ago.isoformat()}') as queries_this_week,
                COUNT(*) FILTER (WHERE created_at >= '{month_ago.isoformat()}') as queries_this_month,
                AVG(confidence) as avg_confidence
            FROM query_history
            WHERE user_id IN ('{fp_ids_str}')
        """)

        query_result = await db.execute(query_metrics_query)
        query_row = query_result.first()

        # Get coverage breakdown
        coverage_query = text(f"""
            SELECT
                cp.policy_type as coverage_type,
                COUNT(*) as count
            FROM customer_policies cp
            JOIN customers c ON cp.customer_id = c.id
            WHERE c.fp_user_id IN ('{fp_ids_str}')
              AND cp.status = 'active'
            GROUP BY cp.policy_type
            ORDER BY count DESC
            LIMIT 10
        """)

        coverage_result = await db.execute(coverage_query)
        coverage_breakdown = [
            {"coverage_type": row.coverage_type, "count": row.count}
            for row in coverage_result.fetchall()
        ]

        # Get top performing FPs
        top_fps_query = text(f"""
            SELECT
                u.user_id as fp_id,
                u.full_name as fp_name,
                COUNT(DISTINCT c.id) as total_customers,
                COUNT(DISTINCT c.id) FILTER (WHERE c.last_contact_date >= '{month_ago.isoformat()}') as active_customers,
                COUNT(DISTINCT cp.id) as total_policies,
                COUNT(DISTINCT qh.id) as total_queries,
                AVG(qh.confidence) as avg_confidence,
                MAX(u.last_login_at) as last_activity
            FROM users u
            LEFT JOIN customers c ON c.fp_user_id = u.user_id
            LEFT JOIN customer_policies cp ON cp.customer_id = c.id AND cp.status = 'active'
            LEFT JOIN query_history qh ON qh.user_id = u.user_id
            WHERE u.user_id IN ('{fp_ids_str}')
            GROUP BY u.user_id, u.full_name
            ORDER BY total_customers DESC, total_policies DESC
            LIMIT 10
        """)

        top_fps_result = await db.execute(top_fps_query)
        top_fps = [
            FPPerformance(
                fp_id=str(row.fp_id),
                fp_name=row.fp_name,
                total_customers=row.total_customers or 0,
                active_customers=row.active_customers or 0,
                total_policies=row.total_policies or 0,
                total_queries=row.total_queries or 0,
                avg_query_confidence=float(row.avg_confidence) if row.avg_confidence else None,
                last_activity=row.last_activity.isoformat() if row.last_activity else None,
            )
            for row in top_fps_result.fetchall()
        ]

        return GATeamMetrics(
            total_fps=total_fps,
            active_fps=active_fps,
            total_customers=customer_row.total_customers or 0,
            active_customers=customer_row.active_customers or 0,
            new_customers_this_month=customer_row.new_customers or 0,
            total_policies=policy_row.total_policies or 0,
            total_coverage_amount=float(policy_row.total_coverage) if policy_row.total_coverage else 0.0,
            total_monthly_premium=float(policy_row.total_premium) if policy_row.total_premium else 0.0,
            total_queries=query_row.total_queries or 0,
            queries_today=query_row.queries_today or 0,
            queries_this_week=query_row.queries_this_week or 0,
            queries_this_month=query_row.queries_this_month or 0,
            avg_query_confidence=float(query_row.avg_confidence) if query_row.avg_confidence else None,
            coverage_breakdown=coverage_breakdown,
            top_fps=top_fps,
        )

    except Exception as e:
        logger.error(f"Failed to get GA team overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team overview: {str(e)}")


@router.get("/fp/{fp_id}/details", response_model=FPPerformance, summary="Get specific FP details")
async def get_fp_details(
    fp_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed performance metrics for a specific FP.

    Only accessible by GA Managers for FPs in their organization.
    """
    check_fp_manager_role(user)

    if not user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="GA Manager must be associated with an organization"
        )

    try:
        # Verify FP belongs to same organization
        fp_check_query = text(f"""
            SELECT user_id, full_name, last_login_at
            FROM users
            WHERE user_id = '{fp_id}'
              AND organization_id = '{user.organization_id}'
              AND role = 'fp'
        """)

        fp_result = await db.execute(fp_check_query)
        fp_row = fp_result.first()

        if not fp_row:
            raise HTTPException(status_code=404, detail="FP not found in your organization")

        month_ago = datetime.utcnow() - timedelta(days=30)

        # Get FP metrics
        metrics_query = text(f"""
            SELECT
                COUNT(DISTINCT c.id) as total_customers,
                COUNT(DISTINCT c.id) FILTER (WHERE c.last_contact_date >= '{month_ago.isoformat()}') as active_customers,
                COUNT(DISTINCT cp.id) as total_policies,
                COUNT(DISTINCT qh.id) as total_queries,
                AVG(qh.confidence) as avg_confidence
            FROM users u
            LEFT JOIN customers c ON c.fp_user_id = u.user_id
            LEFT JOIN customer_policies cp ON cp.customer_id = c.id AND cp.status = 'active'
            LEFT JOIN query_history qh ON qh.user_id = u.user_id
            WHERE u.user_id = '{fp_id}'
            GROUP BY u.user_id
        """)

        result = await db.execute(metrics_query)
        row = result.first()

        return FPPerformance(
            fp_id=str(fp_id),
            fp_name=fp_row.full_name,
            total_customers=row.total_customers or 0,
            active_customers=row.active_customers or 0,
            total_policies=row.total_policies or 0,
            total_queries=row.total_queries or 0,
            avg_query_confidence=float(row.avg_confidence) if row.avg_confidence else None,
            last_activity=fp_row.last_login_at.isoformat() if fp_row.last_login_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FP details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get FP details: {str(e)}")
