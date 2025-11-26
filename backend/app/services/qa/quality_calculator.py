"""
Quality Calculator

데이터 품질 지표를 계산합니다.
"""
import logging
from typing import Dict, Any

from app.models.validation import (
    DataValidationResult,
    GraphValidationResult,
    QualityMetrics,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)


class QualityCalculator:
    """품질 지표 계산기"""

    def __init__(self):
        """계산기 초기화"""
        pass

    def calculate(
        self,
        data_validation: DataValidationResult,
        graph_validation: GraphValidationResult,
    ) -> QualityMetrics:
        """
        품질 지표 계산

        Args:
            data_validation: 데이터 검증 결과
            graph_validation: 그래프 검증 결과

        Returns:
            QualityMetrics
        """
        logger.info("품질 지표 계산 시작")

        # 1. 완성도 점수 (Completeness)
        completeness = self._calculate_completeness(data_validation, graph_validation)

        # 2. 정확도 점수 (Accuracy)
        accuracy = self._calculate_accuracy(data_validation, graph_validation)

        # 3. 일관성 점수 (Consistency)
        consistency = self._calculate_consistency(data_validation, graph_validation)

        # 4. 커버리지 점수 (Coverage)
        coverage = self._calculate_coverage(data_validation, graph_validation)

        # 5. 전체 점수 (가중 평균)
        overall = self._calculate_overall(
            completeness, accuracy, consistency, coverage
        )

        metrics = QualityMetrics(
            overall_score=overall,
            completeness_score=completeness,
            accuracy_score=accuracy,
            consistency_score=consistency,
            coverage_score=coverage,
            metrics={
                "data_validation": {
                    "total_articles": data_validation.total_articles,
                    "total_paragraphs": data_validation.total_paragraphs,
                    "total_amounts": data_validation.total_amounts,
                    "total_relations": data_validation.total_relations,
                    "entity_link_rate": data_validation.entity_link_rate,
                },
                "graph_validation": {
                    "total_nodes": graph_validation.total_nodes,
                    "total_relationships": graph_validation.total_relationships,
                    "orphaned_nodes": graph_validation.orphaned_nodes,
                    "duplicate_nodes": graph_validation.duplicate_nodes,
                },
            },
        )

        logger.info(f"품질 지표 계산 완료: {overall:.2f} (등급: {metrics.get_grade()})")

        return metrics

    def _calculate_completeness(
        self,
        data_validation: DataValidationResult,
        graph_validation: GraphValidationResult,
    ) -> float:
        """
        완성도 점수 계산

        필요한 데이터가 얼마나 완전하게 추출되었는지 측정
        """
        score = 1.0

        # 문서 구조 검증 실패 시 감점
        if not data_validation.structure_valid:
            score -= 0.3

        # 핵심 데이터 검증 실패 시 감점
        if not data_validation.critical_data_valid:
            score -= 0.2

        # 관계 데이터 검증 실패 시 감점
        if not data_validation.relations_valid:
            score -= 0.2

        # 엔티티 링크 검증 실패 시 감점
        if not data_validation.entities_valid:
            score -= 0.1

        # 그래프 노드 검증 실패 시 감점
        if not graph_validation.nodes_valid:
            score -= 0.1

        # 그래프 관계 검증 실패 시 감점
        if not graph_validation.relationships_valid:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _calculate_accuracy(
        self,
        data_validation: DataValidationResult,
        graph_validation: GraphValidationResult,
    ) -> float:
        """
        정확도 점수 계산

        추출된 데이터가 얼마나 정확한지 측정
        """
        score = 1.0

        # 이슈 개수에 따라 감점
        data_issues = data_validation.issues
        graph_issues = graph_validation.issues

        # 치명적 이슈 = -0.3점
        critical_count = len([i for i in data_issues + graph_issues if i.severity == ValidationSeverity.CRITICAL])
        score -= critical_count * 0.3

        # 에러 이슈 = -0.1점
        error_count = len([i for i in data_issues + graph_issues if i.severity == ValidationSeverity.ERROR])
        score -= error_count * 0.1

        # 경고 이슈 = -0.02점
        warning_count = len([i for i in data_issues + graph_issues if i.severity == ValidationSeverity.WARNING])
        score -= warning_count * 0.02

        return max(0.0, min(1.0, score))

    def _calculate_consistency(
        self,
        data_validation: DataValidationResult,
        graph_validation: GraphValidationResult,
    ) -> float:
        """
        일관성 점수 계산

        데이터 간 일관성이 얼마나 유지되는지 측정
        """
        score = 1.0

        # 그래프 일관성 검증 실패 시 감점
        if not graph_validation.consistency_valid:
            score -= 0.4

        # 고아 노드가 있으면 감점
        if graph_validation.orphaned_nodes > 0:
            # 고아 노드 비율에 따라 감점
            orphan_ratio = graph_validation.orphaned_nodes / max(graph_validation.total_nodes, 1)
            score -= orphan_ratio * 0.3

        # 중복 노드가 있으면 감점
        if graph_validation.duplicate_nodes > 0:
            dup_ratio = graph_validation.duplicate_nodes / max(graph_validation.total_nodes, 1)
            score -= dup_ratio * 0.2

        # 유효하지 않은 관계가 있으면 감점
        if graph_validation.invalid_relationships > 0:
            invalid_ratio = graph_validation.invalid_relationships / max(graph_validation.total_relationships, 1)
            score -= invalid_ratio * 0.2

        return max(0.0, min(1.0, score))

    def _calculate_coverage(
        self,
        data_validation: DataValidationResult,
        graph_validation: GraphValidationResult,
    ) -> float:
        """
        커버리지 점수 계산

        문서의 주요 내용이 얼마나 잘 커버되었는지 측정
        """
        score = 0.0

        # 조항 수에 따른 점수
        if data_validation.total_articles > 0:
            score += 0.2
            if data_validation.total_articles >= 10:
                score += 0.1

        # 문단 수에 따른 점수
        if data_validation.total_paragraphs > 0:
            score += 0.1
            if data_validation.total_paragraphs >= 50:
                score += 0.1

        # 핵심 데이터 추출 점수
        if data_validation.total_amounts > 0:
            score += 0.1
        if data_validation.total_periods > 0:
            score += 0.05
        if data_validation.total_kcd_codes > 0:
            score += 0.05

        # 관계 추출 점수
        if data_validation.total_relations > 0:
            score += 0.1
            if data_validation.total_relations >= 10:
                score += 0.1

        # 엔티티 링크 점수
        if data_validation.entity_link_rate > 0:
            score += data_validation.entity_link_rate * 0.2

        return max(0.0, min(1.0, score))

    def _calculate_overall(
        self, completeness: float, accuracy: float, consistency: float, coverage: float
    ) -> float:
        """
        전체 점수 계산 (가중 평균)

        각 지표의 중요도에 따라 가중치 부여
        """
        weights = {
            "completeness": 0.3,  # 완성도 30%
            "accuracy": 0.3,      # 정확도 30%
            "consistency": 0.25,  # 일관성 25%
            "coverage": 0.15,     # 커버리지 15%
        }

        overall = (
            completeness * weights["completeness"]
            + accuracy * weights["accuracy"]
            + consistency * weights["consistency"]
            + coverage * weights["coverage"]
        )

        return max(0.0, min(1.0, overall))
