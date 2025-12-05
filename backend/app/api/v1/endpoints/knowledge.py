"""
Knowledge Extraction API Endpoints

문서에서 엔티티를 추출하고 지식 그래프를 구축하는 API
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Optional
from pydantic import BaseModel

from app.services.document_entity_processor import doc_processor

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


class ProcessDocumentRequest(BaseModel):
    """문서 처리 요청"""
    document_id: str  # UUID string


class ProcessAllRequest(BaseModel):
    """전체 문서 처리 요청"""
    limit: Optional[int] = None


@router.post(
    "/extract/document",
    summary="단일 문서 엔티티 추출",
    description="지정된 문서에서 엔티티를 추출합니다."
)
async def extract_entities_from_document(request: ProcessDocumentRequest):
    """
    단일 문서에서 엔티티 추출

    Args:
        request: 문서 처리 요청

    Returns:
        처리 결과
    """
    try:
        result = await doc_processor.process_document(request.document_id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "PROCESSING_FAILED",
                    "error_message": result.get("error", "Unknown error")
                }
            )

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EXTRACTION_ERROR",
                "error_message": f"엔티티 추출 중 오류가 발생했습니다: {str(e)}"
            }
        )


@router.post(
    "/extract/all",
    summary="전체 문서 엔티티 추출",
    description="완료된 모든 문서에서 엔티티를 추출합니다."
)
async def extract_entities_from_all_documents(request: ProcessAllRequest):
    """
    전체 문서에서 엔티티 추출

    Args:
        request: 처리 요청 (limit 포함)

    Returns:
        처리 결과
    """
    try:
        result = await doc_processor.process_all_completed_documents(limit=request.limit)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BATCH_EXTRACTION_ERROR",
                "error_message": f"배치 추출 중 오류가 발생했습니다: {str(e)}"
            }
        )


@router.post(
    "/extract/all/background",
    summary="전체 문서 엔티티 추출 (백그라운드)",
    description="완료된 모든 문서에서 엔티티를 백그라운드로 추출합니다."
)
async def extract_entities_background(
    background_tasks: BackgroundTasks,
    request: ProcessAllRequest
):
    """
    백그라운드에서 전체 문서 엔티티 추출

    Args:
        background_tasks: FastAPI 백그라운드 태스크
        request: 처리 요청 (limit 포함)

    Returns:
        작업 시작 확인
    """
    # 백그라운드 태스크로 추가
    background_tasks.add_task(
        doc_processor.process_all_completed_documents,
        limit=request.limit
    )

    return {
        "success": True,
        "message": "엔티티 추출 작업이 백그라운드에서 시작되었습니다.",
        "limit": request.limit
    }


@router.get(
    "/stats",
    summary="엔티티 통계 조회",
    description="추출된 엔티티 및 관계의 통계를 조회합니다."
)
async def get_knowledge_stats():
    """
    엔티티 통계 조회

    Returns:
        엔티티 통계
    """
    try:
        stats = await doc_processor.get_entity_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STATS_ERROR",
                "error_message": f"통계 조회 중 오류가 발생했습니다: {str(e)}"
            }
        )
