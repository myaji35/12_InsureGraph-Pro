"""
Vector Search Models

벡터 검색을 위한 데이터 모델들.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SearchStrategy(str, Enum):
    """검색 전략"""
    VECTOR_ONLY = "vector_only"        # 벡터 검색만
    GRAPH_ONLY = "graph_only"          # 그래프 검색만
    HYBRID = "hybrid"                   # 하이브리드 (벡터 + 그래프)
    RERANKED = "reranked"               # 재랭킹 포함


class VectorIndexType(str, Enum):
    """벡터 인덱스 타입"""
    CLAUSE_EMBEDDINGS = "clause_embeddings"     # 조항 임베딩
    COVERAGE_EMBEDDINGS = "coverage_embeddings"  # 보장 임베딩
    DISEASE_EMBEDDINGS = "disease_embeddings"    # 질병 임베딩


class VectorSearchResult(BaseModel):
    """
    벡터 검색 단일 결과
    """
    node_id: str = Field(..., description="노드 ID")
    score: float = Field(..., description="유사도 점수 (0~1)")

    # 노드 정보
    labels: List[str] = Field(default_factory=list, description="노드 레이블")
    properties: Dict[str, Any] = Field(default_factory=dict, description="노드 속성")

    # 조항 정보 (Clause 노드인 경우)
    clause_id: Optional[str] = Field(None, description="조항 ID")
    article_num: Optional[str] = Field(None, description="조 번호")
    clause_text: Optional[str] = Field(None, description="조항 텍스트")

    # 메타데이터
    rank: Optional[int] = Field(None, description="순위")

    def get_text_content(self) -> str:
        """텍스트 내용 추출"""
        if self.clause_text:
            return self.clause_text

        # 속성에서 텍스트 추출
        for key in ["text", "content", "description", "korean_name", "coverage_name"]:
            if key in self.properties:
                return str(self.properties[key])

        return ""


class VectorSearchResults(BaseModel):
    """
    벡터 검색 결과 목록
    """
    results: List[VectorSearchResult] = Field(..., description="검색 결과")
    total_count: int = Field(..., description="총 결과 개수")
    search_time_ms: float = Field(..., description="검색 시간 (밀리초)")

    # 검색 파라미터
    query: str = Field(..., description="원본 질문")
    top_k: int = Field(..., description="요청한 결과 개수")
    index_name: str = Field(..., description="사용한 인덱스")

    def get_top_result(self) -> Optional[VectorSearchResult]:
        """최상위 결과 반환"""
        return self.results[0] if self.results else None

    def filter_by_score(self, min_score: float) -> List[VectorSearchResult]:
        """최소 점수 이상 결과만 필터링"""
        return [r for r in self.results if r.score >= min_score]


class HybridSearchResult(BaseModel):
    """
    하이브리드 검색 결과 (그래프 + 벡터)
    """
    # 원본 결과
    graph_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="그래프 검색 결과"
    )
    vector_results: List[VectorSearchResult] = Field(
        default_factory=list, description="벡터 검색 결과"
    )

    # 통합 결과
    combined_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="통합 결과"
    )

    # 메타데이터
    graph_weight: float = Field(default=0.5, description="그래프 가중치")
    vector_weight: float = Field(default=0.5, description="벡터 가중치")
    fusion_method: str = Field(default="reciprocal_rank", description="융합 방법")

    total_results: int = Field(default=0, description="총 결과 개수")
    search_time_ms: float = Field(default=0.0, description="검색 시간")


class RerankingConfig(BaseModel):
    """
    재랭킹 설정
    """
    enabled: bool = Field(default=True, description="재랭킹 사용 여부")
    method: str = Field(default="cross_encoder", description="재랭킹 방법")

    # Cross-encoder 설정
    model_name: Optional[str] = Field(None, description="모델 이름")
    batch_size: int = Field(default=32, description="배치 크기")

    # 점수 조정
    boost_exact_match: float = Field(default=1.5, description="정확 매칭 부스트")
    boost_entity_match: float = Field(default=1.2, description="엔티티 매칭 부스트")
    penalize_length: bool = Field(default=True, description="길이 페널티")


class SearchRequest(BaseModel):
    """
    검색 요청
    """
    query: str = Field(..., description="검색 질문")

    # 검색 전략
    strategy: SearchStrategy = Field(
        default=SearchStrategy.HYBRID, description="검색 전략"
    )

    # 벡터 검색 설정
    top_k: int = Field(default=10, description="반환할 결과 개수")
    min_score: float = Field(default=0.0, description="최소 유사도 점수")
    index_name: VectorIndexType = Field(
        default=VectorIndexType.CLAUSE_EMBEDDINGS, description="벡터 인덱스"
    )

    # 하이브리드 설정
    graph_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="그래프 가중치")
    vector_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="벡터 가중치")

    # 재랭킹 설정
    reranking: Optional[RerankingConfig] = Field(None, description="재랭킹 설정")

    # 필터링
    filters: Dict[str, Any] = Field(default_factory=dict, description="추가 필터")


class SearchResponse(BaseModel):
    """
    검색 응답
    """
    # 요청 정보
    original_query: str = Field(..., description="원본 질문")
    strategy: SearchStrategy = Field(..., description="사용한 검색 전략")

    # 결과
    results: List[VectorSearchResult] = Field(..., description="최종 검색 결과")

    # 중간 결과 (디버깅용)
    graph_results: Optional[List[Dict[str, Any]]] = Field(
        None, description="그래프 검색 결과"
    )
    vector_results: Optional[List[VectorSearchResult]] = Field(
        None, description="벡터 검색 결과"
    )

    # 메타데이터
    total_count: int = Field(..., description="총 결과 개수")
    search_time_ms: float = Field(..., description="검색 시간")
    reranked: bool = Field(default=False, description="재랭킹 수행 여부")

    # 추가 정보
    explanation: Optional[str] = Field(None, description="검색 설명")

    def get_top_result(self) -> Optional[VectorSearchResult]:
        """최상위 결과"""
        return self.results[0] if self.results else None

    def get_text_snippets(self, max_length: int = 200) -> List[str]:
        """결과 텍스트 스니펫 추출"""
        snippets = []
        for result in self.results:
            text = result.get_text_content()
            if text:
                if len(text) > max_length:
                    text = text[:max_length] + "..."
                snippets.append(text)
        return snippets


class EmbeddingRequest(BaseModel):
    """
    임베딩 생성 요청
    """
    text: str = Field(..., description="임베딩할 텍스트")
    model: str = Field(default="openai", description="임베딩 모델")

    # 옵션
    normalize: bool = Field(default=True, description="정규화 여부")
    cache_key: Optional[str] = Field(None, description="캐시 키")


class EmbeddingResponse(BaseModel):
    """
    임베딩 생성 응답
    """
    embedding: List[float] = Field(..., description="임베딩 벡터")
    dimension: int = Field(..., description="벡터 차원")
    model: str = Field(..., description="사용한 모델")

    # 메타데이터
    generation_time_ms: float = Field(..., description="생성 시간")
    cached: bool = Field(default=False, description="캐시 사용 여부")


class SimilarityScore(BaseModel):
    """
    유사도 점수
    """
    score: float = Field(..., ge=0.0, le=1.0, description="유사도 (0~1)")
    method: str = Field(..., description="계산 방법 (cosine, euclidean 등)")

    # 비교 대상
    query_text: str = Field(..., description="질문 텍스트")
    document_text: str = Field(..., description="문서 텍스트")


class FusionMethod(str, Enum):
    """결과 융합 방법"""
    RECIPROCAL_RANK = "reciprocal_rank"    # Reciprocal Rank Fusion
    WEIGHTED_SUM = "weighted_sum"           # 가중 합
    MAX_SCORE = "max_score"                 # 최대 점수
    MIN_SCORE = "min_score"                 # 최소 점수
    AVERAGE = "average"                     # 평균


class ReciprocalRankFusion(BaseModel):
    """
    Reciprocal Rank Fusion (RRF) 설정
    """
    k: int = Field(default=60, description="RRF 상수")

    def calculate_score(self, rank: int) -> float:
        """
        RRF 점수 계산

        score = 1 / (k + rank)

        Args:
            rank: 순위 (0부터 시작)

        Returns:
            RRF 점수
        """
        return 1.0 / (self.k + rank + 1)


class SearchMetrics(BaseModel):
    """
    검색 성능 지표
    """
    # 시간 지표
    query_embedding_time_ms: float = Field(default=0.0, description="쿼리 임베딩 시간")
    vector_search_time_ms: float = Field(default=0.0, description="벡터 검색 시간")
    graph_search_time_ms: float = Field(default=0.0, description="그래프 검색 시간")
    fusion_time_ms: float = Field(default=0.0, description="융합 시간")
    reranking_time_ms: float = Field(default=0.0, description="재랭킹 시간")
    total_time_ms: float = Field(default=0.0, description="총 시간")

    # 결과 지표
    vector_results_count: int = Field(default=0, description="벡터 검색 결과 수")
    graph_results_count: int = Field(default=0, description="그래프 검색 결과 수")
    final_results_count: int = Field(default=0, description="최종 결과 수")

    # 품질 지표
    avg_score: Optional[float] = Field(None, description="평균 점수")
    max_score: Optional[float] = Field(None, description="최대 점수")
    min_score: Optional[float] = Field(None, description="최소 점수")
