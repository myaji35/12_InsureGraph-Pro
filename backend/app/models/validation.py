"""
Validation Models

데이터 품질 검증 결과를 위한 모델들.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ValidationSeverity(str, Enum):
    """검증 이슈 심각도"""
    INFO = "info"           # 정보성 메시지
    WARNING = "warning"     # 경고 (처리는 가능하지만 주의 필요)
    ERROR = "error"         # 에러 (처리 불가능할 수 있음)
    CRITICAL = "critical"   # 치명적 (반드시 수정 필요)


class ValidationIssue(BaseModel):
    """개별 검증 이슈"""
    severity: ValidationSeverity = Field(..., description="심각도")
    category: str = Field(..., description="카테고리 (예: structure, data, consistency)")
    message: str = Field(..., description="이슈 메시지")
    location: Optional[str] = Field(None, description="이슈 위치 (예: 제1조, Step 4)")
    suggestion: Optional[str] = Field(None, description="해결 방법 제안")

    def __str__(self) -> str:
        location_str = f" [{self.location}]" if self.location else ""
        return f"[{self.severity.value.upper()}]{location_str} {self.message}"


class DataValidationResult(BaseModel):
    """데이터 검증 결과"""
    is_valid: bool = Field(..., description="검증 통과 여부")

    # 검증 항목별 결과
    structure_valid: bool = Field(default=True, description="문서 구조 유효성")
    critical_data_valid: bool = Field(default=True, description="핵심 데이터 유효성")
    relations_valid: bool = Field(default=True, description="관계 데이터 유효성")
    entities_valid: bool = Field(default=True, description="엔티티 링크 유효성")

    # 이슈 목록
    issues: List[ValidationIssue] = Field(default_factory=list, description="검증 이슈 목록")

    # 통계
    total_articles: int = Field(default=0, description="총 조항 수")
    total_paragraphs: int = Field(default=0, description="총 문단 수")
    total_amounts: int = Field(default=0, description="추출된 금액 수")
    total_periods: int = Field(default=0, description="추출된 기간 수")
    total_kcd_codes: int = Field(default=0, description="추출된 KCD 코드 수")
    total_relations: int = Field(default=0, description="추출된 관계 수")
    total_entities_linked: int = Field(default=0, description="연결된 엔티티 수")
    entity_link_rate: float = Field(default=0.0, description="엔티티 연결률 (0-1)")

    def add_issue(
        self,
        severity: ValidationSeverity,
        category: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        """이슈 추가"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            location=location,
            suggestion=suggestion,
        )
        self.issues.append(issue)

        # ERROR 또는 CRITICAL이면 검증 실패
        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """심각도별 이슈 조회"""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_critical_issues(self) -> List[ValidationIssue]:
        """치명적 이슈만 조회"""
        return self.get_issues_by_severity(ValidationSeverity.CRITICAL)

    def get_errors(self) -> List[ValidationIssue]:
        """에러 이슈만 조회"""
        return self.get_issues_by_severity(ValidationSeverity.ERROR)

    def get_warnings(self) -> List[ValidationIssue]:
        """경고 이슈만 조회"""
        return self.get_issues_by_severity(ValidationSeverity.WARNING)


class GraphValidationResult(BaseModel):
    """그래프 검증 결과"""
    is_valid: bool = Field(..., description="검증 통과 여부")

    # 검증 항목별 결과
    nodes_valid: bool = Field(default=True, description="노드 유효성")
    relationships_valid: bool = Field(default=True, description="관계 유효성")
    consistency_valid: bool = Field(default=True, description="일관성 유효성")

    # 이슈 목록
    issues: List[ValidationIssue] = Field(default_factory=list, description="검증 이슈 목록")

    # 그래프 통계
    total_nodes: int = Field(default=0, description="총 노드 수")
    total_relationships: int = Field(default=0, description="총 관계 수")
    nodes_by_type: Dict[str, int] = Field(default_factory=dict, description="노드 타입별 개수")
    relationships_by_type: Dict[str, int] = Field(default_factory=dict, description="관계 타입별 개수")

    # 일관성 검사
    orphaned_nodes: int = Field(default=0, description="고아 노드 수 (연결 없음)")
    duplicate_nodes: int = Field(default=0, description="중복 노드 수")
    invalid_relationships: int = Field(default=0, description="유효하지 않은 관계 수")

    def add_issue(
        self,
        severity: ValidationSeverity,
        category: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        """이슈 추가"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            location=location,
            suggestion=suggestion,
        )
        self.issues.append(issue)

        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False


class QualityMetrics(BaseModel):
    """품질 지표"""

    # 전체 품질 점수 (0-1)
    overall_score: float = Field(..., ge=0.0, le=1.0, description="전체 품질 점수")

    # 세부 점수
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="완성도 점수")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="정확도 점수")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="일관성 점수")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="커버리지 점수")

    # 상세 지표
    metrics: Dict[str, Any] = Field(default_factory=dict, description="상세 지표")

    def get_grade(self) -> str:
        """등급 반환 (A-F)"""
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

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """허용 가능한 품질인지 확인"""
        return self.overall_score >= threshold


class ValidationReport(BaseModel):
    """종합 검증 리포트"""

    # 전체 검증 결과
    is_valid: bool = Field(..., description="전체 검증 통과 여부")

    # 개별 검증 결과
    data_validation: DataValidationResult = Field(..., description="데이터 검증 결과")
    graph_validation: GraphValidationResult = Field(..., description="그래프 검증 결과")
    quality_metrics: QualityMetrics = Field(..., description="품질 지표")

    # 종합 통계
    total_issues: int = Field(default=0, description="총 이슈 수")
    critical_issues: int = Field(default=0, description="치명적 이슈 수")
    errors: int = Field(default=0, description="에러 수")
    warnings: int = Field(default=0, description="경고 수")

    # 메타데이터
    pipeline_id: str = Field(..., description="파이프라인 ID")
    validated_at: Optional[str] = Field(None, description="검증 시각")

    def get_all_issues(self) -> List[ValidationIssue]:
        """모든 이슈 조회"""
        return self.data_validation.issues + self.graph_validation.issues

    def get_summary(self) -> str:
        """요약 문자열 생성"""
        if self.is_valid:
            return f"✅ 검증 통과 (품질: {self.quality_metrics.get_grade()}, 점수: {self.quality_metrics.overall_score:.2f})"
        else:
            return (
                f"❌ 검증 실패 - "
                f"치명적: {self.critical_issues}, "
                f"에러: {self.errors}, "
                f"경고: {self.warnings}"
            )

    def print_report(self) -> str:
        """상세 리포트 출력"""
        lines = []
        lines.append("=" * 60)
        lines.append("검증 리포트")
        lines.append("=" * 60)
        lines.append(f"파이프라인 ID: {self.pipeline_id}")
        lines.append(f"검증 시각: {self.validated_at}")
        lines.append(f"전체 결과: {self.get_summary()}")
        lines.append("")

        # 품질 지표
        lines.append("--- 품질 지표 ---")
        lines.append(f"전체 점수: {self.quality_metrics.overall_score:.2f} (등급: {self.quality_metrics.get_grade()})")
        lines.append(f"  - 완성도: {self.quality_metrics.completeness_score:.2f}")
        lines.append(f"  - 정확도: {self.quality_metrics.accuracy_score:.2f}")
        lines.append(f"  - 일관성: {self.quality_metrics.consistency_score:.2f}")
        lines.append(f"  - 커버리지: {self.quality_metrics.coverage_score:.2f}")
        lines.append("")

        # 데이터 검증
        lines.append("--- 데이터 검증 ---")
        lines.append(f"구조: {'✅' if self.data_validation.structure_valid else '❌'}")
        lines.append(f"핵심 데이터: {'✅' if self.data_validation.critical_data_valid else '❌'}")
        lines.append(f"관계: {'✅' if self.data_validation.relations_valid else '❌'}")
        lines.append(f"엔티티: {'✅' if self.data_validation.entities_valid else '❌'}")
        lines.append("")

        # 그래프 검증
        lines.append("--- 그래프 검증 ---")
        lines.append(f"노드: {'✅' if self.graph_validation.nodes_valid else '❌'} ({self.graph_validation.total_nodes}개)")
        lines.append(f"관계: {'✅' if self.graph_validation.relationships_valid else '❌'} ({self.graph_validation.total_relationships}개)")
        lines.append(f"일관성: {'✅' if self.graph_validation.consistency_valid else '❌'}")
        lines.append("")

        # 이슈 목록
        if self.total_issues > 0:
            lines.append("--- 이슈 목록 ---")
            all_issues = self.get_all_issues()

            # 심각도별로 정렬
            critical = [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
            errors = [i for i in all_issues if i.severity == ValidationSeverity.ERROR]
            warnings = [i for i in all_issues if i.severity == ValidationSeverity.WARNING]

            if critical:
                lines.append("치명적:")
                for issue in critical:
                    lines.append(f"  {issue}")

            if errors:
                lines.append("에러:")
                for issue in errors:
                    lines.append(f"  {issue}")

            if warnings:
                lines.append("경고:")
                for issue in warnings[:5]:  # 경고는 최대 5개만
                    lines.append(f"  {issue}")
                if len(warnings) > 5:
                    lines.append(f"  ... 그 외 {len(warnings) - 5}개 경고")

        lines.append("=" * 60)
        return "\n".join(lines)
