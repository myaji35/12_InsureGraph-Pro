"""
Metadata API Endpoints

RESTful API for Human-in-the-Loop policy metadata curation.
Allows admins to discover, review, and selectively queue policies for learning.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, status
from loguru import logger

from app.api.v1.models.metadata import (
    PolicyMetadataResponse,
    PolicyMetadataListResponse,
    PolicyMetadataQueueRequest,
    PolicyMetadataQueueResponse,
    PolicyMetadataUpdateRequest,
    PolicyMetadataStatsResponse,
    PolicyQueueJobResponse,
    PolicyMetadataErrorResponse,
)
from app.models.policy_metadata import (
    PolicyMetadata,
    PolicyMetadataStatus,
    PolicyCategory,
    PolicyMetadataFilter,
)
from app.models.user import User
from app.core.security import get_current_active_user, require_role

router = APIRouter(prefix="/metadata", tags=["metadata"])

# ============================================
# In-Memory Storage (Development)
# TODO: Replace with PostgreSQL in production
# ============================================

_policy_metadata_store: Dict[UUID, PolicyMetadata] = {}
_ingestion_jobs_store: Dict[UUID, Dict[str, Any]] = {}


# ============================================
# Helper Functions
# ============================================

def _create_policy_response(policy: PolicyMetadata) -> PolicyMetadataResponse:
    """Convert domain model to API response"""
    return PolicyMetadataResponse(
        id=policy.id,
        insurer=policy.insurer,
        category=policy.category.value if policy.category else None,
        policy_name=policy.policy_name,
        file_name=policy.file_name,
        publication_date=policy.publication_date,
        download_url=str(policy.download_url),
        status=policy.status.value,
        queued_by=policy.queued_by,
        queued_at=policy.queued_at,
        discovered_at=policy.discovered_at,
        last_updated=policy.last_updated,
        notes=policy.notes,
        metadata=policy.metadata,
    )


def _filter_policies(
    policies: Dict[UUID, PolicyMetadata],
    filter_params: PolicyMetadataFilter
) -> List[PolicyMetadata]:
    """Apply filters to policy list"""
    result = list(policies.values())

    # Status filter
    if filter_params.status:
        result = [p for p in result if p.status == filter_params.status]

    # Insurer filter
    if filter_params.insurer:
        result = [
            p for p in result
            if filter_params.insurer.lower() in p.insurer.lower()
        ]

    # Category filter
    if filter_params.category:
        result = [p for p in result if p.category == filter_params.category]

    # Date range filter
    if filter_params.date_from:
        result = [
            p for p in result
            if p.publication_date and p.publication_date >= filter_params.date_from
        ]

    if filter_params.date_to:
        result = [
            p for p in result
            if p.publication_date and p.publication_date <= filter_params.date_to
        ]

    # Full-text search (simple contains)
    if filter_params.search:
        search_lower = filter_params.search.lower()
        result = [
            p for p in result
            if (search_lower in p.policy_name.lower() or
                (p.file_name and search_lower in p.file_name.lower()))
        ]

    # Sort by discovery date (newest first)
    result.sort(key=lambda p: p.discovered_at, reverse=True)

    return result


def _paginate(
    items: List[Any],
    page: int,
    page_size: int
) -> tuple[List[Any], Dict[str, Any]]:
    """Paginate items and return pagination info"""
    total = len(items)
    total_pages = (total + page_size - 1) // page_size

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    pagination = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return page_items, pagination


# ============================================
# API Endpoints
# ============================================

@router.get(
    "/policies",
    response_model=PolicyMetadataListResponse,
    summary="List policy metadata",
    description="Retrieve paginated list of discovered policies with filtering",
)
async def list_policies(
    status: Optional[PolicyMetadataStatus] = Query(None, description="Filter by status"),
    insurer: Optional[str] = Query(None, description="Filter by insurer (partial match)"),
    category: Optional[PolicyCategory] = Query(None, description="Filter by category"),
    date_from: Optional[datetime] = Query(None, description="Filter by publication date (from)"),
    date_to: Optional[datetime] = Query(None, description="Filter by publication date (to)"),
    search: Optional[str] = Query(None, description="Full-text search on policy name and file name"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all policy metadata with filtering and pagination.

    **Required Role**: Any authenticated user

    **Query Parameters**:
    - `status`: Filter by lifecycle status
    - `insurer`: Filter by insurer name (case-insensitive partial match)
    - `category`: Filter by policy category
    - `date_from`, `date_to`: Filter by publication date range
    - `search`: Full-text search on policy name and file name
    - `page`, `page_size`: Pagination controls

    **Returns**: Paginated list of policy metadata
    """
    logger.info(
        f"Listing policies - user: {current_user.id}, "
        f"status: {status}, insurer: {insurer}, page: {page}"
    )

    # Build filter
    filter_params = PolicyMetadataFilter(
        status=status,
        insurer=insurer,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        page_size=page_size,
    )

    # Apply filters
    filtered_policies = _filter_policies(_policy_metadata_store, filter_params)

    # Paginate
    page_items, pagination = _paginate(filtered_policies, page, page_size)

    # Convert to response models
    policies_response = [_create_policy_response(p) for p in page_items]

    return PolicyMetadataListResponse(
        policies=policies_response,
        pagination=pagination,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyMetadataResponse,
    summary="Get policy metadata by ID",
    description="Retrieve detailed information about a specific policy",
)
async def get_policy(
    policy_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed information about a specific policy.

    **Required Role**: Any authenticated user

    **Returns**: Policy metadata details
    """
    policy = _policy_metadata_store.get(policy_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy metadata not found: {policy_id}"
        )

    return _create_policy_response(policy)


@router.post(
    "/queue",
    response_model=PolicyMetadataQueueResponse,
    summary="Queue policies for learning",
    description="Admin action to queue selected policies for on-demand download and ingestion",
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_policies(
    request: PolicyMetadataQueueRequest,
    current_user: User = Depends(require_role(["ADMIN", "FP_MANAGER"])),
):
    """
    Queue selected policies for learning.

    **Required Role**: ADMIN or FP_MANAGER

    This endpoint:
    1. Validates that policies can be queued (status must be DISCOVERED or FAILED)
    2. Updates policy status to QUEUED
    3. Creates ingestion job records
    4. Triggers the on-demand downloader worker (Celery task)

    **Request Body**:
    - `policy_ids`: List of policy metadata IDs to queue (max 100)
    - `priority`: Optional priority level (low, medium, high, urgent)
    - `notes`: Optional notes for this batch

    **Returns**: List of created ingestion jobs
    """
    logger.info(
        f"Queueing policies - user: {current_user.id}, "
        f"count: {len(request.policy_ids)}, priority: {request.priority}"
    )

    jobs_created = []
    skipped_policies = []

    for policy_id in request.policy_ids:
        policy = _policy_metadata_store.get(policy_id)

        if not policy:
            logger.warning(f"Policy not found: {policy_id}")
            skipped_policies.append(policy_id)
            continue

        # Check if policy can be queued
        if not policy.can_be_queued():
            logger.warning(
                f"Cannot queue policy {policy_id} with status {policy.status}"
            )
            skipped_policies.append(policy_id)
            continue

        # Update policy status
        try:
            policy.mark_as_queued(current_user.id)
        except ValueError as e:
            logger.error(f"Error queuing policy {policy_id}: {e}")
            skipped_policies.append(policy_id)
            continue

        # Create ingestion job
        job_id = uuid4()
        job = {
            "id": job_id,
            "policy_metadata_id": policy.id,
            "user_id": current_user.id,
            "file_name": policy.file_name,
            "download_url": str(policy.download_url),
            "status": "QUEUED",
            "priority": request.priority or "medium",
            "notes": request.notes,
            "metadata": {
                "insurer": policy.insurer,
                "policy_name": policy.policy_name,
                "publication_date": policy.publication_date.isoformat() if policy.publication_date else None,
            },
            "created_at": datetime.utcnow(),
        }

        _ingestion_jobs_store[job_id] = job

        jobs_created.append(
            PolicyQueueJobResponse(
                job_id=job_id,
                policy_id=policy.id,
                status="QUEUED",
            )
        )

        logger.info(
            f"Created ingestion job {job_id} for policy {policy.id}"
        )

        # TODO: Trigger Celery task to download and process
        # download_and_ingest_policy.delay(job_id)

    return PolicyMetadataQueueResponse(
        queued_count=len(jobs_created),
        jobs_created=jobs_created,
        skipped_count=len(skipped_policies),
        skipped_policies=skipped_policies,
    )


@router.patch(
    "/policies/{policy_id}",
    response_model=PolicyMetadataResponse,
    summary="Update policy metadata",
    description="Admin action to update policy status, notes, or category",
)
async def update_policy(
    policy_id: UUID,
    request: PolicyMetadataUpdateRequest,
    current_user: User = Depends(require_role(["ADMIN", "FP_MANAGER"])),
):
    """
    Update policy metadata (status, notes, category).

    **Required Role**: ADMIN or FP_MANAGER

    Common use cases:
    - Mark as IGNORED (with reason in notes)
    - Update category classification
    - Add manual review notes

    **Returns**: Updated policy metadata
    """
    policy = _policy_metadata_store.get(policy_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy metadata not found: {policy_id}"
        )

    # Update status if provided
    if request.status:
        if request.status == PolicyMetadataStatus.IGNORED:
            try:
                policy.mark_as_ignored(request.notes)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        else:
            try:
                policy.update_status(request.status)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition: {e}"
                )

    # Update notes if provided (and not already updated by mark_as_ignored)
    if request.notes and request.status != PolicyMetadataStatus.IGNORED:
        if policy.notes:
            policy.notes = f"{policy.notes}\n\n[{datetime.utcnow().isoformat()}] {request.notes}"
        else:
            policy.notes = f"[{datetime.utcnow().isoformat()}] {request.notes}"

    # Update category if provided
    if request.category:
        policy.category = request.category

    policy.last_updated = datetime.utcnow()

    logger.info(
        f"Updated policy {policy_id} - user: {current_user.id}, "
        f"status: {request.status}, category: {request.category}"
    )

    return _create_policy_response(policy)


@router.get(
    "/stats",
    response_model=PolicyMetadataStatsResponse,
    summary="Get policy metadata statistics",
    description="Retrieve aggregate statistics for policy metadata",
)
async def get_stats(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get aggregate statistics for policy metadata.

    **Required Role**: Any authenticated user

    **Returns**:
    - Total count
    - Counts by status
    - Counts by insurer
    - Counts by category
    - Recent discoveries (last 7 days)
    """
    policies = list(_policy_metadata_store.values())

    # Count by status
    status_counts = {}
    for status_enum in PolicyMetadataStatus:
        status_counts[status_enum.value] = sum(
            1 for p in policies if p.status == status_enum
        )

    # Count by insurer
    insurer_counts = {}
    for policy in policies:
        insurer_counts[policy.insurer] = insurer_counts.get(policy.insurer, 0) + 1

    # Count by category
    category_counts = {}
    for policy in policies:
        if policy.category:
            cat = policy.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # Recent discoveries (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_discoveries = sum(
        1 for p in policies if p.discovered_at >= seven_days_ago
    )

    return PolicyMetadataStatsResponse(
        total_count=len(policies),
        status_counts=status_counts,
        insurer_counts=insurer_counts,
        category_counts=category_counts,
        recent_discoveries=recent_discoveries,
        last_crawl=None,  # TODO: Track last crawler run
    )


# ============================================
# Development Helper Endpoints
# ============================================

@router.post(
    "/dev/seed",
    response_model=Dict[str, Any],
    summary="[DEV] Seed sample data",
    description="Development endpoint to populate sample policy metadata",
    include_in_schema=False,  # Hide from production docs
)
async def seed_sample_data(
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Seed sample policy metadata for development/testing"""

    sample_policies = [
        PolicyMetadata(
            insurer="삼성화재",
            category=PolicyCategory.CANCER,
            policy_name="종합암보험 2.0 약관",
            file_name="cancer_insurance_v2_2025.pdf",
            publication_date=datetime(2025, 11, 1),
            download_url="https://www.samsungfire.com/download/cancer_v2.pdf",
            status=PolicyMetadataStatus.DISCOVERED,
        ),
        PolicyMetadata(
            insurer="한화생명",
            category=PolicyCategory.LIFE,
            policy_name="무배당 NEW 행복한 종신보험 약관",
            file_name="life_insurance_2025.pdf",
            publication_date=datetime(2025, 10, 15),
            download_url="https://www.hanwhalife.com/download/life_2025.pdf",
            status=PolicyMetadataStatus.DISCOVERED,
        ),
        PolicyMetadata(
            insurer="KB손해보험",
            category=PolicyCategory.CARDIOVASCULAR,
            policy_name="심혈관질환보장보험 약관",
            file_name="cardiovascular_insurance.pdf",
            publication_date=datetime(2025, 9, 20),
            download_url="https://www.kbinsurance.com/download/cardio.pdf",
            status=PolicyMetadataStatus.COMPLETED,
        ),
    ]

    for policy in sample_policies:
        _policy_metadata_store[policy.id] = policy

    logger.info(f"Seeded {len(sample_policies)} sample policies")

    return {
        "message": f"Seeded {len(sample_policies)} sample policies",
        "policy_ids": [str(p.id) for p in sample_policies],
    }
