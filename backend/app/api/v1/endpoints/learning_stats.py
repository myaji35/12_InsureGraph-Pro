"""
Learning Statistics API

SmartInsuranceLearner의 학습 통계 및 캐시 정보 제공
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from loguru import logger

from app.services.learning.smart_learner import SmartInsuranceLearner
from app.services.learning.chunk_learner import SemanticChunkingLearner

router = APIRouter()

# 전역 SmartInsuranceLearner 인스턴스 (통계 유지용)
_smart_learner_instance: SmartInsuranceLearner = None


def get_smart_learner() -> SmartInsuranceLearner:
    """SmartInsuranceLearner 싱글톤 인스턴스 반환"""
    global _smart_learner_instance
    if _smart_learner_instance is None:
        _smart_learner_instance = SmartInsuranceLearner()
    return _smart_learner_instance


@router.get("/stats", response_model=Dict)
async def get_learning_statistics():
    """
    학습 통계 조회

    Returns:
        학습 전략별 통계 및 비용 절감 정보
    """
    try:
        smart_learner = get_smart_learner()
        stats = smart_learner.get_statistics()

        return {
            "status": "success",
            **stats
        }

    except Exception as e:
        logger.error(f"Failed to get learning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", response_model=Dict)
async def get_cache_statistics():
    """
    Redis 캐시 통계 조회

    Returns:
        캐시 상태, 메모리 사용량, 키 개수 등
    """
    try:
        chunk_learner = SemanticChunkingLearner()
        await chunk_learner.connect()

        stats = await chunk_learner.get_cache_stats()

        await chunk_learner.disconnect()

        return {
            "status": "success",
            **stats
        }

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", response_model=Dict)
async def clear_cache(pattern: str = "chunk:learned:*"):
    """
    Redis 캐시 삭제

    Args:
        pattern: 삭제할 키 패턴 (기본값: chunk:learned:*)

    Returns:
        삭제된 키 개수
    """
    try:
        chunk_learner = SemanticChunkingLearner()
        await chunk_learner.connect()

        deleted_count = await chunk_learner.clear_cache(pattern)

        await chunk_learner.disconnect()

        return {
            "status": "success",
            "pattern": pattern,
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=Dict)
async def get_learning_strategies():
    """
    학습 전략 정보 조회

    Returns:
        각 전략의 우선순위, 비용 절감률, 설명
    """
    return {
        "status": "success",
        "strategies": [
            {
                "name": "template",
                "priority": 1,
                "cost_saving_percent": "95%",
                "description": "템플릿 매칭 기반 학습 (변수만 처리)",
                "conditions": "템플릿 캐시 존재 + 유사도 80% 이상"
            },
            {
                "name": "incremental",
                "priority": 2,
                "cost_saving_percent": "80-90%",
                "description": "증분 학습 (이전 버전과의 차이만 학습)",
                "conditions": "이전 버전 존재 + 유사도 85% 이상"
            },
            {
                "name": "chunking",
                "priority": 3,
                "cost_saving_percent": "70-80%",
                "description": "의미 기반 청킹 + Redis 캐싱",
                "conditions": "항상 사용 가능 (fallback)"
            },
            {
                "name": "full",
                "priority": 4,
                "cost_saving_percent": "0%",
                "description": "전체 문서 학습 (캐시 미스 시)",
                "conditions": "다른 전략 모두 실패"
            }
        ]
    }


@router.get("/templates/{insurer}", response_model=Dict)
async def get_insurer_templates(insurer: str):
    """
    특정 보험사의 템플릿 캐시 정보 조회

    Args:
        insurer: 보험사명

    Returns:
        보험사의 캐시된 템플릿 정보
    """
    try:
        smart_learner = get_smart_learner()

        # 템플릿 캐시에서 해당 보험사 템플릿 조회
        templates = {}
        for key, value in smart_learner.template_matcher.template_cache.items():
            if key.startswith(f"{insurer}:"):
                product_type = key.split(":", 1)[1]
                templates[product_type] = {
                    "coverage_ratio": value.get("coverage_ratio", 0),
                    "variable_count": value.get("variable_count", 0),
                    "template_id": value.get("id", "unknown")
                }

        return {
            "status": "success",
            "insurer": insurer,
            "template_count": len(templates),
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Failed to get insurer templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/extract/{insurer}", response_model=Dict)
async def trigger_template_extraction(insurer: str, min_documents: int = 3):
    """
    특정 보험사의 템플릿 추출 트리거

    Args:
        insurer: 보험사명
        min_documents: 최소 문서 수

    Returns:
        추출 결과
    """
    try:
        smart_learner = get_smart_learner()

        result = await smart_learner.optimize_insurer(insurer)

        return {
            "status": "success",
            **result
        }

    except Exception as e:
        logger.error(f"Failed to trigger template extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict)
async def health_check():
    """
    학습 시스템 헬스 체크

    Returns:
        시스템 상태 정보
    """
    try:
        # Redis 연결 확인
        chunk_learner = SemanticChunkingLearner()
        await chunk_learner.connect()
        cache_stats = await chunk_learner.get_cache_stats()
        await chunk_learner.disconnect()

        redis_status = cache_stats.get("status", "unknown")

        # SmartInsuranceLearner 상태 확인
        smart_learner = get_smart_learner()
        learning_stats = smart_learner.get_statistics()

        return {
            "status": "healthy",
            "redis_status": redis_status,
            "learning_system": "operational",
            "total_documents_processed": learning_stats.get("total_documents", 0),
            "cache_enabled": redis_status == "connected"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "redis_status": "unknown",
            "learning_system": "error"
        }
