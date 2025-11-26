"""
Unit tests for Validators

검증 컴포넌트들의 기능을 테스트합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock

from app.services.qa.data_validator import DataValidator
from app.services.qa.graph_validator import GraphValidator
from app.services.qa.quality_calculator import QualityCalculator
from app.services.qa.validator import ComprehensiveValidator
from app.models.validation import (
    DataValidationResult,
    GraphValidationResult,
    QualityMetrics,
    ValidationReport,
    ValidationSeverity,
)


class TestDataValidator:
    """Test suite for DataValidator"""

    @pytest.fixture
    def validator(self):
        """데이터 검증기 인스턴스"""
        return DataValidator()

    def test_validate_structure_success(self, validator):
        """구조 검증 성공 테스트"""
        parsed_doc = {
            "articles": [
                {
                    "article_num": "제1조",
                    "title": "보험금 지급",
                    "paragraphs": [
                        {"text": "보험금을 지급합니다", "paragraph_num": "①"}
                    ],
                }
            ]
        }

        result = validator.validate(parsed_document=parsed_doc)

        assert result.structure_valid is True
        assert result.total_articles == 1
        assert result.total_paragraphs == 1

    def test_validate_structure_no_articles(self, validator):
        """조항이 없는 문서 검증 테스트"""
        parsed_doc = {"articles": []}

        result = validator.validate(parsed_document=parsed_doc)

        assert result.structure_valid is False
        assert len(result.issues) > 0
        assert any(i.severity == ValidationSeverity.CRITICAL for i in result.issues)

    def test_validate_critical_data_success(self, validator):
        """핵심 데이터 검증 성공 테스트"""
        critical_data = {
            "amounts": [
                {"value": 10000000, "original_text": "1천만원", "position": 0}
            ],
            "periods": [{"days": 90, "original_unit": "월"}],
            "kcd_codes": [{"code": "C73", "is_valid": True}],
        }

        result = validator.validate(critical_data=critical_data)

        assert result.critical_data_valid is True
        assert result.total_amounts == 1
        assert result.total_periods == 1
        assert result.total_kcd_codes == 1

    def test_validate_critical_data_invalid_amount(self, validator):
        """유효하지 않은 금액 검증 테스트"""
        critical_data = {
            "amounts": [{"value": -1000, "original_text": "-1000원", "position": 0}],
            "periods": [],
            "kcd_codes": [],
        }

        result = validator.validate(critical_data=critical_data)

        assert result.critical_data_valid is False
        assert any(i.severity == ValidationSeverity.ERROR for i in result.issues)

    def test_validate_relations_success(self, validator):
        """관계 검증 성공 테스트"""
        relations = [
            {
                "relations": [
                    {
                        "subject": "암진단특약",
                        "object": "갑상선암",
                        "action": "COVERS",
                        "confidence": 0.95,
                    }
                ]
            }
        ]

        result = validator.validate(relations=relations)

        assert result.relations_valid is True
        assert result.total_relations == 1

    def test_validate_relations_no_relations(self, validator):
        """관계가 없는 경우 테스트"""
        relations = []

        result = validator.validate(relations=relations)

        assert result.relations_valid is False
        assert len(result.issues) > 0

    def test_validate_entity_links_success(self, validator):
        """엔티티 링크 검증 성공 테스트"""
        entity_links = {
            "갑상선암": {
                "matched_entity": {
                    "standard_name": "ThyroidCancer",
                    "korean_names": ["갑상선암"],
                },
                "match_score": 1.0,
            },
            "간암": {
                "matched_entity": {
                    "standard_name": "LiverCancer",
                    "korean_names": ["간암"],
                },
                "match_score": 1.0,
            },
        }

        result = validator.validate(entity_links=entity_links)

        assert result.entities_valid is True
        assert result.entity_link_rate == 1.0

    def test_validate_entity_links_partial(self, validator):
        """일부 엔티티만 연결된 경우 테스트"""
        entity_links = {
            "갑상선암": {
                "matched_entity": {
                    "standard_name": "ThyroidCancer",
                },
                "match_score": 1.0,
            },
            "알수없는질병": {"matched_entity": None, "match_score": 0.0},
        }

        result = validator.validate(entity_links=entity_links)

        assert result.entity_link_rate == 0.5
        assert len(result.issues) > 0


class TestGraphValidator:
    """Test suite for GraphValidator"""

    @pytest.fixture
    def validator(self):
        """그래프 검증기 인스턴스"""
        return GraphValidator()

    def test_validate_basic_stats_success(self, validator):
        """기본 통계 검증 성공 테스트"""
        graph_stats = {
            "total_nodes": 100,
            "total_relationships": 50,
            "nodes_by_type": {
                "Product": 1,
                "Coverage": 10,
                "Disease": 20,
                "Clause": 69,
            },
            "relationships_by_type": {"COVERS": 20, "HAS_COVERAGE": 10},
        }

        result = validator.validate(graph_stats)

        assert result.nodes_valid is True
        assert result.relationships_valid is True
        assert result.total_nodes == 100
        assert result.total_relationships == 50

    def test_validate_no_nodes(self, validator):
        """노드가 없는 경우 테스트"""
        graph_stats = {
            "total_nodes": 0,
            "total_relationships": 0,
            "nodes_by_type": {},
            "relationships_by_type": {},
        }

        result = validator.validate(graph_stats)

        assert result.nodes_valid is False
        assert result.is_valid is False
        assert any(i.severity == ValidationSeverity.CRITICAL for i in result.issues)

    def test_validate_missing_required_nodes(self, validator):
        """필수 노드가 없는 경우 테스트"""
        graph_stats = {
            "total_nodes": 10,
            "total_relationships": 5,
            "nodes_by_type": {
                "Coverage": 10,  # Product와 Clause가 없음
            },
            "relationships_by_type": {"COVERS": 5},
        }

        result = validator.validate(graph_stats)

        assert result.nodes_valid is False
        assert len(result.issues) >= 2  # Product와 Clause 누락


class TestQualityCalculator:
    """Test suite for QualityCalculator"""

    @pytest.fixture
    def calculator(self):
        """품질 계산기 인스턴스"""
        return QualityCalculator()

    def test_calculate_perfect_quality(self, calculator):
        """완벽한 품질 계산 테스트"""
        data_validation = DataValidationResult(
            is_valid=True,
            structure_valid=True,
            critical_data_valid=True,
            relations_valid=True,
            entities_valid=True,
            total_articles=50,
            total_paragraphs=200,
            total_amounts=10,
            total_relations=20,
            entity_link_rate=1.0,
        )

        graph_validation = GraphValidationResult(
            is_valid=True,
            nodes_valid=True,
            relationships_valid=True,
            consistency_valid=True,
            total_nodes=100,
            total_relationships=50,
        )

        metrics = calculator.calculate(data_validation, graph_validation)

        assert metrics.overall_score >= 0.8
        assert metrics.get_grade() in ["A", "B"]
        assert metrics.is_acceptable()

    def test_calculate_poor_quality(self, calculator):
        """낮은 품질 계산 테스트"""
        data_validation = DataValidationResult(
            is_valid=False,
            structure_valid=False,
            critical_data_valid=False,
            relations_valid=False,
            entities_valid=False,
        )
        data_validation.add_issue(
            ValidationSeverity.CRITICAL, "test", "Critical issue"
        )
        data_validation.add_issue(ValidationSeverity.ERROR, "test", "Error issue")

        graph_validation = GraphValidationResult(
            is_valid=False,
            nodes_valid=False,
            relationships_valid=False,
            consistency_valid=False,
        )

        metrics = calculator.calculate(data_validation, graph_validation)

        assert metrics.overall_score < 0.5
        assert metrics.get_grade() in ["D", "F"]
        assert not metrics.is_acceptable()


class TestComprehensiveValidator:
    """Test suite for ComprehensiveValidator"""

    @pytest.fixture
    def validator(self):
        """종합 검증기 인스턴스"""
        return ComprehensiveValidator()

    @pytest.mark.asyncio
    async def test_validate_all_success(self, validator):
        """전체 검증 성공 테스트"""
        parsed_document = {
            "articles": [
                {
                    "article_num": "제1조",
                    "paragraphs": [{"text": "test", "paragraph_num": "①"}],
                }
            ]
        }

        critical_data = {"amounts": [], "periods": [], "kcd_codes": []}

        relations = [
            {
                "relations": [
                    {
                        "subject": "암진단특약",
                        "object": "갑상선암",
                        "action": "COVERS",
                        "confidence": 0.95,
                    }
                ]
            }
        ]

        entity_links = {
            "갑상선암": {
                "matched_entity": {"standard_name": "ThyroidCancer"},
                "match_score": 1.0,
            }
        }

        graph_stats = {
            "total_nodes": 10,
            "total_relationships": 5,
            "nodes_by_type": {"Product": 1, "Clause": 9},
            "relationships_by_type": {"COVERS": 5},
        }

        report = await validator.validate_all(
            pipeline_id="test_001",
            parsed_document=parsed_document,
            critical_data=critical_data,
            relations=relations,
            entity_links=entity_links,
            graph_stats=graph_stats,
        )

        assert isinstance(report, ValidationReport)
        assert report.pipeline_id == "test_001"
        assert report.data_validation is not None
        assert report.graph_validation is not None
        assert report.quality_metrics is not None

    def test_validate_quality_threshold(self, validator):
        """품질 임계값 검증 테스트"""
        # Mock 리포트
        report = Mock(spec=ValidationReport)
        report.quality_metrics = Mock(spec=QualityMetrics)

        # 임계값 통과
        report.quality_metrics.is_acceptable = Mock(return_value=True)
        assert validator.validate_quality_threshold(report, 0.7) is True

        # 임계값 미달
        report.quality_metrics.is_acceptable = Mock(return_value=False)
        assert validator.validate_quality_threshold(report, 0.7) is False


class TestValidationModels:
    """Test suite for Validation Models"""

    def test_validation_issue_str(self):
        """ValidationIssue 문자열 변환 테스트"""
        from app.models.validation import ValidationIssue

        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="test",
            message="Test error",
            location="제1조",
        )

        issue_str = str(issue)
        assert "ERROR" in issue_str
        assert "Test error" in issue_str
        assert "제1조" in issue_str

    def test_data_validation_result_add_issue(self):
        """데이터 검증 결과 이슈 추가 테스트"""
        result = DataValidationResult(is_valid=True)

        # WARNING은 is_valid를 변경하지 않음
        result.add_issue(ValidationSeverity.WARNING, "test", "Warning message")
        assert result.is_valid is True

        # ERROR는 is_valid를 False로 변경
        result.add_issue(ValidationSeverity.ERROR, "test", "Error message")
        assert result.is_valid is False

    def test_validation_report_get_summary(self):
        """검증 리포트 요약 생성 테스트"""
        data_val = DataValidationResult(is_valid=True)
        graph_val = GraphValidationResult(is_valid=True)
        quality = QualityMetrics(
            overall_score=0.85,
            completeness_score=0.9,
            accuracy_score=0.8,
            consistency_score=0.85,
            coverage_score=0.85,
        )

        report = ValidationReport(
            is_valid=True,
            data_validation=data_val,
            graph_validation=graph_val,
            quality_metrics=quality,
            pipeline_id="test_001",
        )

        summary = report.get_summary()
        assert "✅" in summary
        assert "0.85" in summary

    def test_quality_metrics_get_grade(self):
        """품질 점수 등급 테스트"""
        # A등급
        metrics_a = QualityMetrics(
            overall_score=0.95,
            completeness_score=1.0,
            accuracy_score=0.9,
            consistency_score=0.95,
            coverage_score=0.95,
        )
        assert metrics_a.get_grade() == "A"

        # C등급
        metrics_c = QualityMetrics(
            overall_score=0.75,
            completeness_score=0.7,
            accuracy_score=0.8,
            consistency_score=0.75,
            coverage_score=0.75,
        )
        assert metrics_c.get_grade() == "C"

        # F등급
        metrics_f = QualityMetrics(
            overall_score=0.4,
            completeness_score=0.4,
            accuracy_score=0.4,
            consistency_score=0.4,
            coverage_score=0.4,
        )
        assert metrics_f.get_grade() == "F"
