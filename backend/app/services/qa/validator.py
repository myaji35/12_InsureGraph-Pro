"""
Comprehensive Validator

모든 검증 컴포넌트를 통합한 종합 검증기.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.validation import ValidationReport
from app.services.qa.data_validator import DataValidator
from app.services.qa.graph_validator import GraphValidator
from app.services.qa.quality_calculator import QualityCalculator
from app.services.graph.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class ComprehensiveValidator:
    """종합 검증기"""

    def __init__(self, neo4j_service: Optional[Neo4jService] = None):
        """
        검증기 초기화

        Args:
            neo4j_service: Neo4j 서비스 (선택사항)
        """
        self.data_validator = DataValidator()
        self.graph_validator = GraphValidator(neo4j_service)
        self.quality_calculator = QualityCalculator()

    async def validate_all(
        self,
        pipeline_id: str,
        parsed_document: Optional[Dict[str, Any]] = None,
        critical_data: Optional[Dict[str, Any]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        entity_links: Optional[Dict[str, Any]] = None,
        graph_stats: Optional[Dict[str, Any]] = None,
        neo4j_service: Optional[Neo4jService] = None,
    ) -> ValidationReport:
        """
        전체 검증 수행

        Args:
            pipeline_id: 파이프라인 ID
            parsed_document: 파싱된 문서
            critical_data: 핵심 데이터
            relations: 관계 목록
            entity_links: 엔티티 링크
            graph_stats: 그래프 통계
            neo4j_service: Neo4j 서비스 (선택사항)

        Returns:
            ValidationReport: 종합 검증 리포트

        Example:
            ```python
            validator = ComprehensiveValidator(neo4j_service)

            report = await validator.validate_all(
                pipeline_id="pipeline_001",
                parsed_document=state.parsed_document,
                critical_data=state.critical_data,
                relations=state.relations,
                entity_links=state.entity_links,
                graph_stats=state.graph_stats,
            )

            if report.is_valid:
                print(f"✅ 검증 통과: {report.quality_metrics.overall_score:.2f}")
            else:
                print(f"❌ 검증 실패")
                for issue in report.get_all_issues():
                    print(f"  - {issue}")
            ```
        """
        logger.info(f"종합 검증 시작: {pipeline_id}")

        # 1. 데이터 검증
        logger.info("1/3: 데이터 검증 수행 중...")
        data_result = self.data_validator.validate(
            parsed_document=parsed_document,
            critical_data=critical_data,
            relations=relations,
            entity_links=entity_links,
        )

        # 2. 그래프 검증
        logger.info("2/3: 그래프 검증 수행 중...")
        graph_result = self.graph_validator.validate(
            graph_stats=graph_stats or {},
            neo4j_service=neo4j_service,
        )

        # 3. 품질 지표 계산
        logger.info("3/3: 품질 지표 계산 중...")
        quality_metrics = self.quality_calculator.calculate(
            data_validation=data_result,
            graph_validation=graph_result,
        )

        # 종합 리포트 생성
        all_issues = data_result.issues + graph_result.issues
        report = ValidationReport(
            is_valid=data_result.is_valid and graph_result.is_valid,
            data_validation=data_result,
            graph_validation=graph_result,
            quality_metrics=quality_metrics,
            total_issues=len(all_issues),
            critical_issues=len([i for i in all_issues if i.severity.value == "critical"]),
            errors=len([i for i in all_issues if i.severity.value == "error"]),
            warnings=len([i for i in all_issues if i.severity.value == "warning"]),
            pipeline_id=pipeline_id,
            validated_at=datetime.utcnow().isoformat(),
        )

        logger.info(f"종합 검증 완료: {report.get_summary()}")

        return report

    def validate_quality_threshold(
        self, report: ValidationReport, threshold: float = 0.7
    ) -> bool:
        """
        품질 임계값 검증

        Args:
            report: 검증 리포트
            threshold: 최소 품질 점수 (0-1)

        Returns:
            품질 임계값 통과 여부
        """
        return report.quality_metrics.is_acceptable(threshold)
