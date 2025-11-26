"""
Graph Query Models

그래프 쿼리 실행을 위한 데이터 모델들.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class QueryResultType(str, Enum):
    """쿼리 결과 타입"""
    NODE = "node"                    # 단일 노드
    RELATIONSHIP = "relationship"    # 관계
    PATH = "path"                    # 경로
    SCALAR = "scalar"                # 스칼라 값 (숫자, 문자열 등)
    AGGREGATE = "aggregate"          # 집계 결과
    TABLE = "table"                  # 테이블 형식


class CypherQuery(BaseModel):
    """
    Cypher 쿼리 표현
    """
    query: str = Field(..., description="Cypher 쿼리 문자열")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="쿼리 파라미터")
    result_type: QueryResultType = Field(..., description="예상 결과 타입")
    timeout: Optional[int] = Field(None, description="타임아웃 (초)")

    def __str__(self) -> str:
        """쿼리 문자열 표현"""
        if self.parameters:
            return f"{self.query}\nParameters: {self.parameters}"
        return self.query


class GraphNode(BaseModel):
    """
    그래프 노드 결과
    """
    node_id: str = Field(..., description="노드 ID")
    labels: List[str] = Field(..., description="노드 레이블")
    properties: Dict[str, Any] = Field(default_factory=dict, description="노드 속성")

    def get_property(self, key: str, default: Any = None) -> Any:
        """속성 값 가져오기"""
        return self.properties.get(key, default)

    def has_label(self, label: str) -> bool:
        """특정 레이블 보유 여부"""
        return label in self.labels


class GraphRelationship(BaseModel):
    """
    그래프 관계 결과
    """
    relationship_id: str = Field(..., description="관계 ID")
    type: str = Field(..., description="관계 타입")
    start_node: str = Field(..., description="시작 노드 ID")
    end_node: str = Field(..., description="종료 노드 ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="관계 속성")

    def get_property(self, key: str, default: Any = None) -> Any:
        """속성 값 가져오기"""
        return self.properties.get(key, default)


class GraphPath(BaseModel):
    """
    그래프 경로 결과
    """
    nodes: List[GraphNode] = Field(..., description="경로의 노드들")
    relationships: List[GraphRelationship] = Field(..., description="경로의 관계들")
    length: int = Field(..., description="경로 길이")

    def get_start_node(self) -> Optional[GraphNode]:
        """시작 노드"""
        return self.nodes[0] if self.nodes else None

    def get_end_node(self) -> Optional[GraphNode]:
        """종료 노드"""
        return self.nodes[-1] if self.nodes else None


class QueryResult(BaseModel):
    """
    쿼리 실행 결과
    """
    result_type: QueryResultType = Field(..., description="결과 타입")

    # 다양한 결과 형식
    nodes: List[GraphNode] = Field(default_factory=list, description="노드 결과")
    relationships: List[GraphRelationship] = Field(default_factory=list, description="관계 결과")
    paths: List[GraphPath] = Field(default_factory=list, description="경로 결과")
    scalars: List[Any] = Field(default_factory=list, description="스칼라 값")
    table: List[Dict[str, Any]] = Field(default_factory=list, description="테이블 결과")

    # 메타데이터
    total_count: int = Field(default=0, description="총 결과 개수")
    execution_time_ms: Optional[float] = Field(None, description="실행 시간 (밀리초)")

    def is_empty(self) -> bool:
        """결과가 비어있는지 확인"""
        return (
            len(self.nodes) == 0 and
            len(self.relationships) == 0 and
            len(self.paths) == 0 and
            len(self.scalars) == 0 and
            len(self.table) == 0
        )

    def get_first_node(self) -> Optional[GraphNode]:
        """첫 번째 노드 반환"""
        return self.nodes[0] if self.nodes else None

    def get_first_scalar(self) -> Optional[Any]:
        """첫 번째 스칼라 값 반환"""
        return self.scalars[0] if self.scalars else None


class CoverageQueryResult(BaseModel):
    """
    보장 관련 쿼리 결과
    """
    coverage_name: str = Field(..., description="보장명")
    disease_name: Optional[str] = Field(None, description="질병명")
    amount: Optional[int] = Field(None, description="보장 금액")
    kcd_code: Optional[str] = Field(None, description="KCD 코드")
    conditions: List[str] = Field(default_factory=list, description="보장 조건")
    exclusions: List[str] = Field(default_factory=list, description="제외 사항")
    waiting_period_days: Optional[int] = Field(None, description="대기기간 (일)")


class DiseaseQueryResult(BaseModel):
    """
    질병 관련 쿼리 결과
    """
    disease_name: str = Field(..., description="질병명")
    standard_name: Optional[str] = Field(None, description="표준명")
    kcd_code: Optional[str] = Field(None, description="KCD 코드")
    kcd_name: Optional[str] = Field(None, description="KCD 한글명")
    coverages: List[str] = Field(default_factory=list, description="해당 보장 목록")
    amounts: List[int] = Field(default_factory=list, description="보장 금액 목록")


class ComparisonResult(BaseModel):
    """
    비교 쿼리 결과
    """
    item1: Dict[str, Any] = Field(..., description="비교 대상 1")
    item2: Dict[str, Any] = Field(..., description="비교 대상 2")
    differences: List[Dict[str, Any]] = Field(default_factory=list, description="차이점")
    similarities: List[Dict[str, Any]] = Field(default_factory=list, description="공통점")


class QueryExecutionPlan(BaseModel):
    """
    쿼리 실행 계획
    """
    query_type: str = Field(..., description="쿼리 타입")
    steps: List[str] = Field(..., description="실행 단계")
    estimated_time_ms: Optional[float] = Field(None, description="예상 실행 시간")
    uses_index: bool = Field(default=False, description="인덱스 사용 여부")


class QueryError(BaseModel):
    """
    쿼리 실행 오류
    """
    error_type: str = Field(..., description="오류 타입")
    message: str = Field(..., description="오류 메시지")
    query: Optional[str] = Field(None, description="실패한 쿼리")
    suggestion: Optional[str] = Field(None, description="해결 제안")


class GraphQueryRequest(BaseModel):
    """
    그래프 쿼리 요청
    """
    # Story 2.1의 분석 결과
    original_query: str = Field(..., description="원본 질문")
    intent: str = Field(..., description="질문 의도")
    query_type: str = Field(..., description="쿼리 타입")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="추출된 엔티티")

    # 쿼리 옵션
    max_results: int = Field(default=10, description="최대 결과 개수")
    include_explanation: bool = Field(default=True, description="설명 포함 여부")
    timeout: Optional[int] = Field(None, description="타임아웃 (초)")


class GraphQueryResponse(BaseModel):
    """
    그래프 쿼리 응답
    """
    # 요청 정보
    request_id: Optional[str] = Field(None, description="요청 ID")
    original_query: str = Field(..., description="원본 질문")

    # 실행 정보
    cypher_query: str = Field(..., description="실행된 Cypher 쿼리")
    execution_time_ms: float = Field(..., description="실행 시간")

    # 결과
    result: QueryResult = Field(..., description="쿼리 결과")

    # 구조화된 결과 (질문 타입별)
    coverage_results: List[CoverageQueryResult] = Field(
        default_factory=list, description="보장 관련 결과"
    )
    disease_results: List[DiseaseQueryResult] = Field(
        default_factory=list, description="질병 관련 결과"
    )
    comparison_result: Optional[ComparisonResult] = Field(
        None, description="비교 결과"
    )

    # 메타데이터
    success: bool = Field(default=True, description="성공 여부")
    error: Optional[QueryError] = Field(None, description="오류 정보")
    explanation: Optional[str] = Field(None, description="결과 설명")

    def is_successful(self) -> bool:
        """쿼리 성공 여부"""
        return self.success and self.error is None

    def has_results(self) -> bool:
        """결과 존재 여부"""
        return not self.result.is_empty()


class QueryTemplate(BaseModel):
    """
    쿼리 템플릿
    """
    name: str = Field(..., description="템플릿 이름")
    description: str = Field(..., description="템플릿 설명")
    template: str = Field(..., description="Cypher 쿼리 템플릿")
    required_params: List[str] = Field(..., description="필수 파라미터")
    optional_params: List[str] = Field(default_factory=list, description="선택 파라미터")
    result_type: QueryResultType = Field(..., description="결과 타입")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="사용 예시")

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 유효성 검증"""
        return all(param in params for param in self.required_params)

    def render(self, params: Dict[str, Any]) -> str:
        """템플릿 렌더링"""
        if not self.validate_params(params):
            missing = [p for p in self.required_params if p not in params]
            raise ValueError(f"Missing required parameters: {missing}")

        query = self.template
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, str):
                query = query.replace(placeholder, f"'{value}'")
            else:
                query = query.replace(placeholder, str(value))

        return query
