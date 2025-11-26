"""
Query Models

질의응답을 위한 데이터 모델들.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QueryIntent(str, Enum):
    """질문 의도 타입"""
    # 보장 관련
    COVERAGE_INQUIRY = "coverage_inquiry"              # "이 보험은 무엇을 보장하나요?"
    COVERAGE_AMOUNT = "coverage_amount"                # "갑상선암 보장 금액은?"
    COVERAGE_CHECK = "coverage_check"                  # "간암은 보장되나요?"
    EXCLUSION_CHECK = "exclusion_check"                # "이 보험에서 제외되는 질병은?"

    # 조건 관련
    CONDITION_INQUIRY = "condition_inquiry"            # "보험금 받으려면 어떤 조건이?"
    WAITING_PERIOD = "waiting_period"                  # "대기기간은 얼마나 되나요?"
    AGE_LIMIT = "age_limit"                           # "나이 제한이 있나요?"

    # 비교 관련
    DISEASE_COMPARISON = "disease_comparison"          # "갑상선암과 간암 보장 차이는?"
    COVERAGE_COMPARISON = "coverage_comparison"        # "암진단특약과 수술특약 비교"

    # 일반 정보
    GENERAL_INFO = "general_info"                      # "이 보험 상품은 어떤 보험인가요?"
    PRODUCT_SUMMARY = "product_summary"                # "보험 내용을 요약해주세요"

    # 복합 질문
    COMPLEX_QUERY = "complex_query"                    # 여러 의도가 섞인 질문
    UNKNOWN = "unknown"                                # 의도 파악 불가


class QueryType(str, Enum):
    """쿼리 실행 타입"""
    GRAPH_TRAVERSAL = "graph_traversal"     # 그래프 순회 쿼리 (관계 추적)
    VECTOR_SEARCH = "vector_search"         # 벡터 유사도 검색
    HYBRID = "hybrid"                        # 그래프 + 벡터 결합
    DIRECT_LOOKUP = "direct_lookup"         # 직접 조회 (단순 질문)


class EntityType(str, Enum):
    """추출 가능한 엔티티 타입"""
    DISEASE = "disease"                     # 질병명 (갑상선암, 간암 등)
    COVERAGE = "coverage"                   # 보장명 (암진단특약, 수술특약 등)
    CONDITION = "condition"                 # 조건 (대기기간, 나이제한 등)
    AMOUNT = "amount"                       # 금액 (1천만원, 1억원 등)
    PERIOD = "period"                       # 기간 (90일, 3개월 등)
    KCD_CODE = "kcd_code"                  # KCD 코드 (C73, C22 등)


class ExtractedEntity(BaseModel):
    """추출된 엔티티"""
    text: str = Field(..., description="원본 텍스트")
    entity_type: EntityType = Field(..., description="엔티티 타입")
    normalized_value: Optional[str] = Field(None, description="정규화된 값")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    start_pos: Optional[int] = Field(None, description="시작 위치")
    end_pos: Optional[int] = Field(None, description="종료 위치")


class QueryAnalysisResult(BaseModel):
    """쿼리 분석 결과"""
    # 원본 질문
    original_query: str = Field(..., description="원본 질문")

    # 의도 분석
    intent: QueryIntent = Field(..., description="질문 의도")
    intent_confidence: float = Field(..., ge=0.0, le=1.0, description="의도 신뢰도")

    # 추천 쿼리 타입
    query_type: QueryType = Field(..., description="쿼리 실행 타입")

    # 추출된 엔티티
    entities: List[ExtractedEntity] = Field(default_factory=list, description="추출된 엔티티 목록")

    # 질문 재구성
    reformulated_query: Optional[str] = Field(None, description="재구성된 질문")

    # 키워드
    keywords: List[str] = Field(default_factory=list, description="주요 키워드")

    # 메타데이터
    language: str = Field(default="ko", description="질문 언어")
    is_answerable: bool = Field(default=True, description="답변 가능 여부")
    suggested_clarification: Optional[str] = Field(None, description="명확화 제안")

    def get_diseases(self) -> List[str]:
        """질병 엔티티만 추출"""
        return [e.text for e in self.entities if e.entity_type == EntityType.DISEASE]

    def get_coverages(self) -> List[str]:
        """보장 엔티티만 추출"""
        return [e.text for e in self.entities if e.entity_type == EntityType.COVERAGE]

    def has_entity_type(self, entity_type: EntityType) -> bool:
        """특정 타입의 엔티티 존재 여부"""
        return any(e.entity_type == entity_type for e in self.entities)


class QueryContext(BaseModel):
    """쿼리 컨텍스트 (대화 이력)"""
    conversation_id: str = Field(..., description="대화 ID")
    previous_queries: List[str] = Field(default_factory=list, description="이전 질문들")
    previous_intents: List[QueryIntent] = Field(default_factory=list, description="이전 의도들")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="사용자 프로필")

    def add_query(self, query: str, intent: QueryIntent):
        """이전 질문 추가"""
        self.previous_queries.append(query)
        self.previous_intents.append(intent)


class IntentPattern(BaseModel):
    """의도 감지를 위한 패턴"""
    intent: QueryIntent = Field(..., description="의도")
    patterns: List[str] = Field(..., description="매칭 패턴 (키워드/구문)")
    keywords: List[str] = Field(default_factory=list, description="필수 키워드")
    examples: List[str] = Field(default_factory=list, description="예시 질문")
    priority: int = Field(default=1, description="우선순위 (높을수록 우선)")


# 사전 정의된 의도 패턴
INTENT_PATTERNS = [
    # 보장 금액 질문
    IntentPattern(
        intent=QueryIntent.COVERAGE_AMOUNT,
        patterns=["보장금", "보험금", "지급", "얼마"],
        keywords=["금액", "얼마", "보장금", "보험금"],
        examples=[
            "갑상선암 보장 금액은?",
            "간암 진단 시 얼마를 받나요?",
            "암 보험금은 얼마인가요?"
        ],
        priority=3
    ),

    # 보장 여부 확인
    IntentPattern(
        intent=QueryIntent.COVERAGE_CHECK,
        patterns=["보장", "커버", "포함", "해당"],
        keywords=["보장", "되나요", "해당", "포함"],
        examples=[
            "갑상선암은 보장되나요?",
            "이 보험에 간암이 포함되나요?",
            "뇌출혈도 보장 대상인가요?"
        ],
        priority=3
    ),

    # 제외 확인
    IntentPattern(
        intent=QueryIntent.EXCLUSION_CHECK,
        patterns=["제외", "면책", "보장안", "안되"],
        keywords=["제외", "면책", "제외"],
        examples=[
            "이 보험에서 제외되는 질병은?",
            "보장 안 되는 암은 무엇인가요?",
            "면책 사항이 뭐예요?"
        ],
        priority=3
    ),

    # 대기기간
    IntentPattern(
        intent=QueryIntent.WAITING_PERIOD,
        patterns=["대기기간", "기다려야", "얼마나", "언제부터"],
        keywords=["대기기간", "기간"],
        examples=[
            "대기기간은 얼마나 되나요?",
            "암 진단까지 얼마나 기다려야 하나요?",
            "보험금을 받으려면 언제부터 가능한가요?"
        ],
        priority=2
    ),

    # 보장 조회 (일반)
    IntentPattern(
        intent=QueryIntent.COVERAGE_INQUIRY,
        patterns=["무엇", "어떤", "뭘", "보장"],
        keywords=["보장", "무엇", "어떤"],
        examples=[
            "이 보험은 무엇을 보장하나요?",
            "어떤 질병을 커버하나요?",
            "보장 항목이 뭐예요?"
        ],
        priority=2
    ),

    # 조건 질문
    IntentPattern(
        intent=QueryIntent.CONDITION_INQUIRY,
        patterns=["조건", "요건", "필요", "받으려면"],
        keywords=["조건", "요건"],
        examples=[
            "보험금을 받으려면 어떤 조건이 필요한가요?",
            "가입 조건은 무엇인가요?",
            "보장 요건이 있나요?"
        ],
        priority=2
    ),

    # 상품 요약
    IntentPattern(
        intent=QueryIntent.PRODUCT_SUMMARY,
        patterns=["요약", "설명", "개요", "소개"],
        keywords=["요약", "설명"],
        examples=[
            "이 보험 상품을 요약해주세요",
            "보험 내용을 간단히 설명해주세요",
            "이 보험 상품 개요는?"
        ],
        priority=1
    ),
]
