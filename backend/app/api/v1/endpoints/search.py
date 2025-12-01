"""
Search API Endpoints

MVP search endpoints for insurance policy documents.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_pg_connection
from app.repositories.document_repository import (
    DocumentRepository,
    DocumentFilter,
    get_document_repository,
)


router = APIRouter(prefix="/search", tags=["Search"])


# ============================================================================
# Response Models
# ============================================================================


class DocumentSearchResult(BaseModel):
    """Single search result (summary)"""
    id: UUID
    policy_name: str
    insurer: str
    policy_id: Optional[UUID] = None

    total_pages: int = 0
    total_articles: int = 0
    total_paragraphs: int = 0
    total_amounts: int = 0
    total_periods: int = 0
    total_kcd_codes: int = 0

    relevance: float = Field(..., description="Search relevance score (0-1)")
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "policy_name": "무배당 KB암보험",
                "insurer": "KB손해보험",
                "policy_id": None,
                "total_pages": 25,
                "total_articles": 30,
                "total_paragraphs": 45,
                "total_amounts": 15,
                "total_periods": 8,
                "total_kcd_codes": 12,
                "relevance": 0.85,
                "created_at": "2025-12-01T10:30:00Z"
            }
        }


class SearchResponse(BaseModel):
    """Search response with pagination"""
    results: List[DocumentSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total": 42,
                "page": 1,
                "page_size": 20,
                "total_pages": 3
            }
        }


class DocumentDetail(BaseModel):
    """Full document with parsed structure"""
    id: UUID
    policy_name: str
    insurer: str
    policy_id: Optional[UUID] = None

    full_text: str
    parsed_structure: dict
    critical_data: dict

    total_pages: int = 0
    total_chars: int = 0
    total_articles: int = 0
    total_paragraphs: int = 0
    total_subclauses: int = 0
    total_amounts: int = 0
    total_periods: int = 0
    total_kcd_codes: int = 0

    created_at: str
    updated_at: str


class InsurerList(BaseModel):
    """List of available insurers"""
    insurers: List[str]


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/documents",
    response_model=SearchResponse,
    summary="Search insurance policy documents",
    description="""
Search for insurance policy documents with various filters.

**Filters:**
- `q`: Full-text search query (policy name, insurer, content)
- `insurer`: Filter by insurance company name
- `amount_min`: Minimum insurance amount (KRW)
- `amount_max`: Maximum insurance amount (KRW)
- `page`: Page number (1-indexed)
- `page_size`: Results per page (max 100)

**Example queries:**
- `?q=암보험` - Search for cancer insurance
- `?q=보험금&amount_min=10000000` - Search for policies with 10M+ coverage
- `?insurer=삼성생명&page=2` - Second page of Samsung Life policies
""",
)
async def search_documents(
    q: Optional[str] = Query(None, description="Search query"),
    insurer: Optional[str] = Query(None, description="Insurance company name"),
    amount_min: Optional[int] = Query(None, ge=0, description="Minimum amount (KRW)"),
    amount_max: Optional[int] = Query(None, ge=0, description="Maximum amount (KRW)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Search for documents with filters.
    """
    # Calculate offset
    offset = (page - 1) * page_size

    # Build filter
    filter_params = DocumentFilter(
        query=q,
        insurer=insurer,
        amount_min=amount_min,
        amount_max=amount_max,
        limit=page_size,
        offset=offset,
    )

    # Get repository
    doc_repo = get_document_repository()

    # Search
    results = doc_repo.search(filter_params)

    # Get total count
    total = doc_repo.count(filter_params)

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    # Convert to response models
    search_results = [
        DocumentSearchResult(
            id=doc["id"] if isinstance(doc["id"], UUID) else UUID(doc["id"]),
            policy_name=doc["policy_name"],
            insurer=doc["insurer"],
            policy_id=(doc["policy_id"] if isinstance(doc.get("policy_id"), UUID) else UUID(doc["policy_id"])) if doc.get("policy_id") else None,
            total_pages=doc.get("total_pages", 0),
            total_articles=doc.get("total_articles", 0),
            total_paragraphs=doc.get("total_paragraphs", 0),
            total_amounts=doc.get("total_amounts", 0),
            total_periods=doc.get("total_periods", 0),
            total_kcd_codes=doc.get("total_kcd_codes", 0),
            relevance=float(doc.get("relevance", 0)),
            created_at=doc["created_at"].isoformat(),
        )
        for doc in results
    ]

    return SearchResponse(
        results=search_results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetail,
    summary="Get document by ID",
    description="Retrieve full document details including parsed structure and critical data.",
)
async def get_document(
    document_id: UUID,
):
    """
    Get full document by ID.
    """
    doc_repo = get_document_repository()

    document = doc_repo.get_full_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDetail(
        id=document["id"] if isinstance(document["id"], UUID) else UUID(document["id"]),
        policy_name=document["policy_name"],
        insurer=document["insurer"],
        policy_id=(document["policy_id"] if isinstance(document.get("policy_id"), UUID) else UUID(document["policy_id"])) if document.get("policy_id") else None,
        full_text=document["full_text"],
        parsed_structure=document["parsed_structure"],
        critical_data=document["critical_data"],
        total_pages=document.get("total_pages", 0),
        total_chars=document.get("total_chars", 0),
        total_articles=document.get("total_articles", 0),
        total_paragraphs=document.get("total_paragraphs", 0),
        total_subclauses=document.get("total_subclauses", 0),
        total_amounts=document.get("total_amounts", 0),
        total_periods=document.get("total_periods", 0),
        total_kcd_codes=document.get("total_kcd_codes", 0),
        created_at=document["created_at"].isoformat(),
        updated_at=document["updated_at"].isoformat(),
    )


@router.get(
    "/insurers",
    response_model=InsurerList,
    summary="Get list of insurers",
    description="Get list of unique insurance companies in the database.",
)
async def get_insurers():
    """
    Get list of available insurers.
    """
    doc_repo = get_document_repository()
    insurers = doc_repo.get_insurers()

    return InsurerList(insurers=insurers)


# ============================================================================
# Dev/Test Helpers
# ============================================================================


class SeedResult(BaseModel):
    """Result of seeding sample data"""
    success: bool
    message: str
    documents_created: int


@router.post(
    "/dev/seed",
    response_model=SeedResult,
    summary="[DEV] Seed sample documents",
    description="Development endpoint to seed sample documents for testing.",
    tags=["Development"],
)
async def seed_sample_data():
    """
    Seed sample documents for testing.

    This is a development endpoint that creates sample documents.
    """
    doc_repo = get_document_repository()

    # Sample data
    samples = [
        {
            "policy_name": "무배당 KB암보험",
            "insurer": "KB손해보험",
            "full_text": "제1조 (보험금의 지급사유) 암진단비로 1억원을 지급합니다.",
            "parsed_structure": {
                "articles": [
                    {
                        "article_num": "제1조",
                        "title": "보험금의 지급사유",
                        "page": 1,
                        "position": 0,
                        "paragraphs": [],
                        "raw_text": "제1조 (보험금의 지급사유) 암진단비로 1억원을 지급합니다."
                    }
                ],
                "total_pages": 25,
                "parsing_confidence": 0.95,
                "parsing_errors": [],
                "parsing_warnings": []
            },
            "critical_data": {
                "amounts": [
                    {
                        "amount_str": "1억원",
                        "normalized_value": 100000000,
                        "context": "암진단비",
                        "position": 15
                    }
                ],
                "periods": [],
                "kcd_codes": []
            },
            "total_pages": 25,
            "total_chars": 5000,
            "total_articles": 30,
            "total_paragraphs": 45,
            "total_subclauses": 20,
            "total_amounts": 1,
            "total_periods": 0,
            "total_kcd_codes": 0,
        },
        {
            "policy_name": "삼성화재 실손의료보험",
            "insurer": "삼성화재",
            "full_text": "제2조 (보험금의 지급사유) 입원 시 하루당 10만원을 90일 한도로 지급합니다.",
            "parsed_structure": {
                "articles": [
                    {
                        "article_num": "제2조",
                        "title": "보험금의 지급사유",
                        "page": 1,
                        "position": 0,
                        "paragraphs": [],
                        "raw_text": "제2조 (보험금의 지급사유) 입원 시 하루당 10만원을 90일 한도로 지급합니다."
                    }
                ],
                "total_pages": 18,
                "parsing_confidence": 0.93,
                "parsing_errors": [],
                "parsing_warnings": []
            },
            "critical_data": {
                "amounts": [
                    {
                        "amount_str": "10만원",
                        "normalized_value": 100000,
                        "context": "입원 시 하루당",
                        "position": 20
                    }
                ],
                "periods": [
                    {
                        "period_str": "90일",
                        "normalized_days": 90,
                        "context": "한도",
                        "position": 30
                    }
                ],
                "kcd_codes": []
            },
            "total_pages": 18,
            "total_chars": 3500,
            "total_articles": 25,
            "total_paragraphs": 35,
            "total_subclauses": 15,
            "total_amounts": 1,
            "total_periods": 1,
            "total_kcd_codes": 0,
        }
    ]

    # Create documents
    created_count = 0
    for sample in samples:
        try:
            doc_repo.create(
                policy_name=sample["policy_name"],
                insurer=sample["insurer"],
                full_text=sample["full_text"],
                parsed_structure=sample["parsed_structure"],
                critical_data=sample["critical_data"],
                policy_id=None,
                total_pages=sample["total_pages"],
                total_chars=sample["total_chars"],
                total_articles=sample["total_articles"],
                total_paragraphs=sample["total_paragraphs"],
                total_subclauses=sample["total_subclauses"],
                total_amounts=sample["total_amounts"],
                total_periods=sample["total_periods"],
                total_kcd_codes=sample["total_kcd_codes"],
            )
            created_count += 1
        except Exception as e:
            # Skip if already exists
            pass

    return SeedResult(
        success=True,
        message=f"Successfully seeded {created_count} sample documents",
        documents_created=created_count,
    )
