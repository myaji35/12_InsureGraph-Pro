"""
Analytics API Endpoints

Story 3.5: Dashboard & Analytics
Provides metrics and analytics for FP users.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.customer import Customer, CustomerPolicy
from loguru import logger


router = APIRouter()


# Response Models

class MetricCard(BaseModel):
    """Single metric card data"""
    label: str
    value: int
    change: Optional[str] = None
    trend: Optional[str] = None  # "up" | "down" | "neutral"


class RecentCustomer(BaseModel):
    """Recent customer info"""
    id: str
    name: str
    age: int
    policy_count: int
    last_contact_date: Optional[datetime] = None
    created_at: datetime


class CoverageBreakdown(BaseModel):
    """Coverage type breakdown"""
    coverage_type: str
    count: int
    total_amount: float


class DashboardOverview(BaseModel):
    """Dashboard overview response"""
    metrics: List[MetricCard]
    recent_customers: List[RecentCustomer]
    coverage_breakdown: List[CoverageBreakdown]
    period_start: datetime
    period_end: datetime


# Endpoints

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard overview metrics

    Returns:
    - Total customers
    - Active customers (contacted in last 30 days)
    - Total policies
    - Recent customers
    - Coverage breakdown
    """
    try:
        logger.info(f"Fetching dashboard overview for user {user.id}")

        # Date ranges
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Total customers
        total_customers_query = select(func.count(Customer.id)).where(
            Customer.fp_user_id == user.id
        )
        total_customers_result = await db.execute(total_customers_query)
        total_customers = total_customers_result.scalar() or 0

        # Active customers (contacted in last 30 days)
        active_customers_query = select(func.count(Customer.id)).where(
            and_(
                Customer.fp_user_id == user.id,
                Customer.last_contact_date >= thirty_days_ago
            )
        )
        active_customers_result = await db.execute(active_customers_query)
        active_customers = active_customers_result.scalar() or 0

        # Active customers (previous period for comparison)
        prev_active_customers_query = select(func.count(Customer.id)).where(
            and_(
                Customer.fp_user_id == user.id,
                Customer.last_contact_date >= sixty_days_ago,
                Customer.last_contact_date < thirty_days_ago
            )
        )
        prev_active_result = await db.execute(prev_active_customers_query)
        prev_active_customers = prev_active_result.scalar() or 0

        # Total policies
        total_policies_query = select(func.count(CustomerPolicy.id)).join(
            Customer, CustomerPolicy.customer_id == Customer.id
        ).where(
            Customer.fp_user_id == user.id
        )
        total_policies_result = await db.execute(total_policies_query)
        total_policies = total_policies_result.scalar() or 0

        # New customers (last 30 days)
        new_customers_query = select(func.count(Customer.id)).where(
            and_(
                Customer.fp_user_id == user.id,
                Customer.created_at >= thirty_days_ago
            )
        )
        new_customers_result = await db.execute(new_customers_query)
        new_customers = new_customers_result.scalar() or 0

        # Build metrics
        metrics = [
            MetricCard(
                label="총 고객",
                value=total_customers,
                change=f"+{new_customers}" if new_customers > 0 else None,
                trend="up" if new_customers > 0 else "neutral"
            ),
            MetricCard(
                label="활성 고객 (30일)",
                value=active_customers,
                change=f"+{active_customers - prev_active_customers}" if active_customers > prev_active_customers else f"{active_customers - prev_active_customers}" if active_customers < prev_active_customers else "0",
                trend="up" if active_customers > prev_active_customers else "down" if active_customers < prev_active_customers else "neutral"
            ),
            MetricCard(
                label="총 보험 계약",
                value=total_policies,
                trend="neutral"
            ),
            MetricCard(
                label="신규 고객 (30일)",
                value=new_customers,
                trend="up" if new_customers > 0 else "neutral"
            ),
        ]

        # Recent customers (last 10)
        recent_customers_query = select(Customer).where(
            Customer.fp_user_id == user.id
        ).order_by(Customer.created_at.desc()).limit(10)

        recent_customers_result = await db.execute(recent_customers_query)
        recent_customers_db = recent_customers_result.scalars().all()

        # Get policy counts for recent customers
        recent_customers = []
        for customer in recent_customers_db:
            policy_count_query = select(func.count(CustomerPolicy.id)).where(
                CustomerPolicy.customer_id == customer.id
            )
            policy_count_result = await db.execute(policy_count_query)
            policy_count = policy_count_result.scalar() or 0

            # Calculate age
            current_year = datetime.utcnow().year
            age = current_year - customer.birth_year

            recent_customers.append(RecentCustomer(
                id=str(customer.id),
                name=customer.name,
                age=age,
                policy_count=policy_count,
                last_contact_date=customer.last_contact_date,
                created_at=customer.created_at
            ))

        # Coverage breakdown
        coverage_breakdown_query = select(
            CustomerPolicy.policy_type,
            func.count(CustomerPolicy.id).label('count'),
            func.sum(CustomerPolicy.coverage_amount).label('total_amount')
        ).join(
            Customer, CustomerPolicy.customer_id == Customer.id
        ).where(
            Customer.fp_user_id == user.id
        ).group_by(CustomerPolicy.policy_type)

        coverage_result = await db.execute(coverage_breakdown_query)
        coverage_rows = coverage_result.all()

        coverage_breakdown = [
            CoverageBreakdown(
                coverage_type=row.policy_type or "기타",
                count=row.count,
                total_amount=float(row.total_amount or 0)
            )
            for row in coverage_rows
        ]

        return DashboardOverview(
            metrics=metrics,
            recent_customers=recent_customers,
            coverage_breakdown=coverage_breakdown,
            period_start=thirty_days_ago,
            period_end=now
        )

    except Exception as e:
        logger.error(f"Failed to fetch dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard overview: {str(e)}"
        )
