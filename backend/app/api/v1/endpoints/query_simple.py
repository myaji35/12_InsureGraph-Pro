"""
Simple Query API Endpoints

GraphRAG 쿼리 엔진 API를 제공합니다 (간단한 버전).
Stories 2.1-2.5를 통합한 API입니다.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query as QueryParam, Depends
from pydantic import BaseModel, Field
from psycopg2.extras import Json
import json

from app.core.database import get_pg_connection
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.query_parser import get_query_parser, QueryIntent
from app.services.local_search import get_local_search
from app.services.graph_traversal import get_graph_traversal
from app.services.llm_reasoning import get_llm_reasoning, LLMProvider
from app.services.answer_validator import get_answer_validator
from loguru import logger


router = APIRouter()


# Request/Response Models

class SimpleQueryRequest(BaseModel):
    """Query request"""
    query: str = Field(..., description="자연어 질문", min_length=1, max_length=500)
    policy_id: Optional[str] = Field(None, description="특정 보험 정책 ID (선택)")
    customer_id: Optional[str] = Field(None, description="고객 ID (선택, 히스토리 추적용)")
    limit: int = Field(10, description="검색 결과 수", ge=1, le=50)
    use_traversal: bool = Field(True, description="그래프 탐색 사용 여부")
    llm_provider: str = Field("openai", description="LLM 제공자 (openai/anthropic/mock)")


class EntityInfo(BaseModel):
    """Extracted entity info"""
    entity_type: str
    value: str


class SearchResultInfo(BaseModel):
    """Search result info"""
    node_id: str
    node_type: str
    text: str
    relevance_score: float
    article_num: Optional[str] = None


class GraphNodeInfo(BaseModel):
    """Graph node info for visualization"""
    node_id: str
    node_type: str
    text: str
    properties: Dict[str, Any] = {}


class GraphPathInfo(BaseModel):
    """Graph path info for visualization"""
    nodes: List[GraphNodeInfo]
    relationships: List[str]
    path_length: int
    relevance_score: float


class ValidationInfo(BaseModel):
    """Validation info"""
    passed: bool
    overall_level: str
    confidence: float
    issues_count: int
    recommendations: List[str]


class SimpleQueryResponse(BaseModel):
    """Query response"""
    query: str
    intent: str
    entities: List[EntityInfo]

    # Search
    search_results_count: int
    search_results: List[SearchResultInfo]

    # Traversal
    graph_paths_count: int
    graph_paths: List[GraphPathInfo] = []

    # Answer
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]

    # Validation
    validation: ValidationInfo


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    neo4j_connected: bool
    llm_available: bool


# Endpoints

@router.post("/execute", response_model=SimpleQueryResponse, summary="자연어 쿼리 실행 (Simple)")
async def execute_simple_query(
    request: SimpleQueryRequest,
    user: User = Depends(get_current_active_user),
    db = Depends(get_pg_connection),
):
    """
    자연어 질문에 대한 답변을 생성합니다.

    ## 프로세스:
    1. 쿼리 파싱 및 의도 감지
    2. Neo4j 검색
    3. 그래프 탐색 (선택)
    4. LLM 추론
    5. 답변 검증

    ## 예시:
    ```json
    {
        "query": "암보험 1억원 이상 보장되는 경우는?",
        "limit": 10,
        "use_traversal": true,
        "llm_provider": "openai"
    }
    ```
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Executing simple query: {request.query}")

        # 1. Parse query
        parser = get_query_parser()
        parsed_query = parser.parse(request.query)

        logger.info(f"Query intent: {parsed_query.intent.value}")

        # 2. Search
        search = get_local_search()
        search_results = search.search(parsed_query, limit=request.limit)

        logger.info(f"Found {search_results.total_results} search results")

        # 3. Graph traversal (optional)
        graph_paths = []
        if request.use_traversal and search_results.results:
            traversal = get_graph_traversal()

            # Traverse from first result
            first_result = search_results.results[0]
            try:
                traversal_result = traversal.traverse_hierarchical(
                    start_node_id=first_result.node_id,
                    direction="down",
                    max_depth=2,
                )
                graph_paths = traversal_result.paths
                logger.info(f"Found {len(graph_paths)} graph paths")
            except Exception as e:
                logger.warning(f"Graph traversal failed: {e}")

        # 4. LLM reasoning
        try:
            provider = LLMProvider(request.llm_provider)
        except ValueError:
            logger.warning(f"Invalid LLM provider: {request.llm_provider}, using OPENAI")
            provider = LLMProvider.OPENAI

        reasoning = get_llm_reasoning(provider=provider)
        context = reasoning.assemble_context(
            parsed_query=parsed_query,
            search_results=search_results.results,
            graph_paths=graph_paths,
        )

        reasoning_result = reasoning.reason(context)

        logger.info(f"Generated answer (confidence: {reasoning_result.confidence:.2f})")

        # 5. Validate answer
        validator = get_answer_validator()
        validation_result = validator.validate(
            reasoning_result=reasoning_result,
            search_results=search_results.results,
        )

        logger.info(
            f"Validation: {validation_result.overall_level.value} "
            f"(adjusted confidence: {validation_result.confidence:.2f})"
        )

        # Build response
        response = SimpleQueryResponse(
            query=request.query,
            intent=parsed_query.intent.value,
            entities=[
                EntityInfo(entity_type=e.entity_type, value=e.value)
                for e in parsed_query.entities
            ],
            search_results_count=search_results.total_results,
            search_results=[
                SearchResultInfo(
                    node_id=r.node_id,
                    node_type=r.node_type,
                    text=r.text[:300],  # Truncate for API response
                    relevance_score=r.relevance_score,
                    article_num=r.article_num,
                )
                for r in search_results.results[:5]  # Top 5 for API
            ],
            graph_paths_count=len(graph_paths),
            graph_paths=[
                GraphPathInfo(
                    nodes=[
                        GraphNodeInfo(
                            node_id=node.node_id,
                            node_type=node.node_type,
                            text=node.text[:200],  # Truncate for visualization
                            properties=node.properties,
                        )
                        for node in path.nodes
                    ],
                    relationships=path.relationships,
                    path_length=path.path_length,
                    relevance_score=path.relevance_score,
                )
                for path in graph_paths[:10]  # Top 10 paths for visualization
            ],
            answer=reasoning_result.answer,
            confidence=validation_result.confidence,  # Use validated confidence
            sources=reasoning_result.sources[:10],  # Top 10 sources
            validation=ValidationInfo(
                passed=validation_result.passed,
                overall_level=validation_result.overall_level.value,
                confidence=validation_result.confidence,
                issues_count=len(validation_result.issues),
                recommendations=validation_result.recommendations,
            ),
        )

        # 6. Save to query history (auto-save feature)
        try:
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Prepare source documents for storage
            source_docs = [
                {
                    "node_id": src.get("node_id"),
                    "text": src.get("text", "")[:500],  # Limit text length
                    "article_num": src.get("article_num"),
                }
                for src in reasoning_result.sources[:5]  # Store top 5 sources
            ]

            # Prepare reasoning path for storage
            reasoning_path_data = {
                "graph_paths_count": len(graph_paths),
                "paths": [
                    {
                        "path_length": path.path_length,
                        "relevance_score": path.relevance_score,
                        "node_types": [node.node_type for node in path.nodes],
                    }
                    for path in graph_paths[:3]  # Store top 3 paths
                ]
            } if graph_paths else None

            # Insert into query_history
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO query_history (
                    user_id, customer_id, query_text, intent, answer,
                    confidence, source_documents, reasoning_path, execution_time_ms
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    str(user.user_id),
                    request.customer_id if request.customer_id else None,
                    request.query,
                    parsed_query.intent.value,
                    reasoning_result.answer[:1000],  # Limit answer length
                    float(validation_result.confidence),
                    Json(source_docs),
                    Json(reasoning_path_data) if reasoning_path_data else None,
                    execution_time_ms,
                ),
            )
            db.commit()
            cursor.close()
            logger.info(f"Saved query history for user {user.user_id}")
        except Exception as save_error:
            logger.warning(f"Failed to save query history: {save_error}")
            # Don't fail the request if history save fails
            db.rollback()

        return response

    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/intents", response_model=List[str], summary="지원되는 쿼리 의도 목록")
async def get_intents():
    """
    지원되는 쿼리 의도(Intent) 목록을 반환합니다.

    ## 쿼리 의도 유형:
    - `search`: 일반 검색
    - `comparison`: 보험 상품 비교
    - `amount_filter`: 금액별 필터링
    - `coverage_check`: 보장 범위 확인
    - `exclusion_check`: 면책 조항 확인
    - `period_check`: 기간 확인
    """
    return [intent.value for intent in QueryIntent if intent != QueryIntent.UNKNOWN]


@router.get("/health", response_model=HealthResponse, summary="쿼리 엔진 상태 확인")
async def health_check():
    """
    쿼리 엔진의 상태를 확인합니다.

    - Neo4j 연결 상태
    - LLM 가용성
    """
    # Check Neo4j
    neo4j_connected = False
    try:
        search = get_local_search()
        # Simple test query
        search.driver.verify_connectivity()
        neo4j_connected = True
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")

    # Check LLM
    llm_available = False
    try:
        reasoning = get_llm_reasoning(provider=LLMProvider.OPENAI)
        llm_available = (reasoning.provider != LLMProvider.MOCK)
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")

    status = "healthy" if (neo4j_connected and llm_available) else "degraded"

    return HealthResponse(
        status=status,
        neo4j_connected=neo4j_connected,
        llm_available=llm_available,
    )


@router.get("/", summary="Simple Query API 정보")
async def root():
    """
    Simple Query API 기본 정보를 반환합니다.
    """
    return {
        "service": "InsureGraph Pro Simple Query API",
        "version": "1.0.0",
        "endpoints": {
            "execute": "POST /api/v1/query-simple/execute",
            "intents": "GET /api/v1/query-simple/intents",
            "health": "GET /api/v1/query-simple/health",
        },
        "description": "GraphRAG 기반 보험 약관 자연어 쿼리 API (Stories 2.1-2.5 통합)",
        "features": [
            "Query Parsing & Intent Detection (Story 2.1)",
            "Local Search (Story 2.2)",
            "Graph Traversal (Story 2.3)",
            "LLM Reasoning (Story 2.4)",
            "Answer Validation (Story 2.5)",
        ],
    }
