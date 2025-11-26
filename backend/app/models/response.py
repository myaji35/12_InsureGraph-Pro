"""
Response Models

응답 생성을 위한 데이터 모델들.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class AnswerFormat(str, Enum):
    """응답 형식"""
    TEXT = "text"                    # 일반 텍스트
    TABLE = "table"                  # 테이블 형식
    LIST = "list"                    # 리스트 형식
    COMPARISON = "comparison"        # 비교 형식
    SUMMARY = "summary"              # 요약 형식
    DETAILED = "detailed"            # 상세 형식


class CitationType(str, Enum):
    """출처 타입"""
    CLAUSE = "clause"                # 조항
    ARTICLE = "article"              # 조
    COVERAGE = "coverage"            # 보장
    CONDITION = "condition"          # 조건


class Citation(BaseModel):
    """
    출처 정보
    """
    citation_type: CitationType = Field(..., description="출처 타입")
    source_id: str = Field(..., description="출처 ID")
    source_text: str = Field(..., description="출처 텍스트")

    # 위치 정보
    article_num: Optional[str] = Field(None, description="조 번호")
    paragraph_num: Optional[str] = Field(None, description="항 번호")

    # 신뢰도
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="관련성 점수")

    def format_citation(self) -> str:
        """출처 포맷팅"""
        if self.article_num:
            return f"[{self.article_num}]"
        return f"[{self.citation_type.value}:{self.source_id}]"


class AnswerSegment(BaseModel):
    """
    답변 세그먼트 (답변의 일부분)
    """
    content: str = Field(..., description="내용")
    segment_type: str = Field(default="text", description="세그먼트 타입")
    citations: List[Citation] = Field(default_factory=list, description="출처 목록")
    confidence: Optional[float] = Field(None, description="신뢰도")


class TableRow(BaseModel):
    """테이블 행"""
    cells: List[str] = Field(..., description="셀 데이터")
    row_type: str = Field(default="data", description="행 타입 (header/data)")


class Table(BaseModel):
    """테이블 데이터"""
    headers: List[str] = Field(..., description="헤더")
    rows: List[TableRow] = Field(..., description="행 목록")
    caption: Optional[str] = Field(None, description="테이블 캡션")

    def to_markdown(self) -> str:
        """마크다운 테이블로 변환"""
        lines = []

        # 헤더
        lines.append("| " + " | ".join(self.headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")

        # 데이터 행
        for row in self.rows:
            lines.append("| " + " | ".join(row.cells) + " |")

        return "\n".join(lines)


class ComparisonItem(BaseModel):
    """비교 항목"""
    name: str = Field(..., description="항목 이름")
    attributes: Dict[str, Any] = Field(..., description="속성")


class Comparison(BaseModel):
    """비교 데이터"""
    item1: ComparisonItem = Field(..., description="비교 대상 1")
    item2: ComparisonItem = Field(..., description="비교 대상 2")
    differences: List[Dict[str, Any]] = Field(default_factory=list, description="차이점")
    similarities: List[Dict[str, Any]] = Field(default_factory=list, description="공통점")

    def to_text(self) -> str:
        """텍스트로 변환"""
        lines = []

        lines.append(f"# {self.item1.name} vs {self.item2.name}\n")

        if self.similarities:
            lines.append("## 공통점")
            for sim in self.similarities:
                lines.append(f"- {sim}")

        if self.differences:
            lines.append("\n## 차이점")
            for diff in self.differences:
                lines.append(f"- {diff}")

        return "\n".join(lines)


class GeneratedResponse(BaseModel):
    """
    생성된 응답
    """
    # 기본 정보
    answer: str = Field(..., description="주 답변")
    format: AnswerFormat = Field(..., description="응답 형식")

    # 구조화된 데이터
    segments: List[AnswerSegment] = Field(default_factory=list, description="답변 세그먼트")
    table: Optional[Table] = Field(None, description="테이블 데이터")
    comparison: Optional[Comparison] = Field(None, description="비교 데이터")
    list_items: List[str] = Field(default_factory=list, description="리스트 항목")

    # 메타데이터
    citations: List[Citation] = Field(default_factory=list, description="전체 출처")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="응답 신뢰도")
    generation_time_ms: float = Field(default=0.0, description="생성 시간")

    # 추가 정보
    follow_up_suggestions: List[str] = Field(
        default_factory=list, description="후속 질문 제안"
    )
    related_topics: List[str] = Field(default_factory=list, description="관련 주제")

    def get_full_answer(self, include_citations: bool = True) -> str:
        """
        전체 답변 생성

        Args:
            include_citations: 출처 포함 여부

        Returns:
            전체 답변 텍스트
        """
        parts = [self.answer]

        # 테이블 추가
        if self.table:
            parts.append("\n\n" + self.table.to_markdown())

        # 비교 추가
        if self.comparison:
            parts.append("\n\n" + self.comparison.to_text())

        # 리스트 추가
        if self.list_items:
            parts.append("\n\n" + "\n".join(f"- {item}" for item in self.list_items))

        # 출처 추가
        if include_citations and self.citations:
            parts.append("\n\n**출처:**")
            for i, citation in enumerate(self.citations, 1):
                parts.append(f"{i}. {citation.format_citation()}")

        # 후속 질문 제안
        if self.follow_up_suggestions:
            parts.append("\n\n**관련 질문:**")
            for suggestion in self.follow_up_suggestions:
                parts.append(f"- {suggestion}")

        return "\n".join(parts)


class ResponseTemplate(BaseModel):
    """
    응답 템플릿
    """
    template_id: str = Field(..., description="템플릿 ID")
    intent: str = Field(..., description="대상 의도")
    template: str = Field(..., description="템플릿 문자열")
    format: AnswerFormat = Field(..., description="응답 형식")

    # 변수
    required_variables: List[str] = Field(..., description="필수 변수")
    optional_variables: List[str] = Field(default_factory=list, description="선택 변수")

    # 예시
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="사용 예시")

    def render(self, variables: Dict[str, Any]) -> str:
        """
        템플릿 렌더링

        Args:
            variables: 변수 딕셔너리

        Returns:
            렌더링된 텍스트
        """
        # 필수 변수 확인
        for var in self.required_variables:
            if var not in variables:
                raise ValueError(f"Required variable missing: {var}")

        # 템플릿 렌더링
        text = self.template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            text = text.replace(placeholder, str(value))

        return text


class ConversationTurn(BaseModel):
    """대화 턴"""
    turn_id: int = Field(..., description="턴 ID")
    user_query: str = Field(..., description="사용자 질문")
    assistant_response: GeneratedResponse = Field(..., description="AI 응답")
    timestamp: datetime = Field(default_factory=datetime.now, description="시간")


class ConversationContext(BaseModel):
    """
    대화 컨텍스트
    """
    conversation_id: str = Field(..., description="대화 ID")
    turns: List[ConversationTurn] = Field(default_factory=list, description="대화 턴")

    # 컨텍스트 정보
    current_topic: Optional[str] = Field(None, description="현재 주제")
    entities_mentioned: List[str] = Field(default_factory=list, description="언급된 엔티티")
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="사용자 선호도"
    )

    def add_turn(self, user_query: str, response: GeneratedResponse):
        """대화 턴 추가"""
        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            user_query=user_query,
            assistant_response=response,
        )
        self.turns.append(turn)

    def get_last_turn(self) -> Optional[ConversationTurn]:
        """마지막 턴 반환"""
        return self.turns[-1] if self.turns else None

    def get_recent_turns(self, n: int = 3) -> List[ConversationTurn]:
        """최근 N개 턴 반환"""
        return self.turns[-n:] if self.turns else []


class ResponseGenerationRequest(BaseModel):
    """
    응답 생성 요청
    """
    # 질문 정보
    query: str = Field(..., description="사용자 질문")
    intent: str = Field(..., description="질문 의도")

    # 검색 결과
    search_results: List[Dict[str, Any]] = Field(..., description="검색 결과")
    graph_results: Optional[List[Dict[str, Any]]] = Field(None, description="그래프 결과")
    vector_results: Optional[List[Dict[str, Any]]] = Field(None, description="벡터 결과")

    # 옵션
    format: AnswerFormat = Field(default=AnswerFormat.TEXT, description="응답 형식")
    include_citations: bool = Field(default=True, description="출처 포함 여부")
    include_follow_ups: bool = Field(default=True, description="후속 질문 포함 여부")
    max_length: Optional[int] = Field(None, description="최대 길이")

    # 컨텍스트
    conversation_context: Optional[ConversationContext] = Field(
        None, description="대화 컨텍스트"
    )


class ResponseQuality(BaseModel):
    """
    응답 품질 평가
    """
    completeness: float = Field(..., ge=0.0, le=1.0, description="완전성")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="정확성")
    relevance: float = Field(..., ge=0.0, le=1.0, description="관련성")
    clarity: float = Field(..., ge=0.0, le=1.0, description="명확성")

    overall_score: float = Field(..., ge=0.0, le=1.0, description="종합 점수")

    def calculate_overall(self):
        """종합 점수 계산"""
        self.overall_score = (
            self.completeness * 0.3
            + self.accuracy * 0.3
            + self.relevance * 0.25
            + self.clarity * 0.15
        )

    def get_grade(self) -> str:
        """등급 반환"""
        if self.overall_score >= 0.9:
            return "A"
        elif self.overall_score >= 0.8:
            return "B"
        elif self.overall_score >= 0.7:
            return "C"
        elif self.overall_score >= 0.6:
            return "D"
        else:
            return "F"
