"""
Unit tests for Graph Query

그래프 쿼리 컴포넌트들의 기능을 테스트합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

from app.models.query import (
    QueryAnalysisResult,
    QueryIntent,
    QueryType,
    ExtractedEntity,
    EntityType,
)
from app.models.graph_query import (
    CypherQuery,
    QueryResultType,
    QueryResult,
    GraphNode,
    GraphRelationship,
    GraphPath,
    CoverageQueryResult,
    DiseaseQueryResult,
    ComparisonResult,
    QueryTemplate,
)
from app.services.graph_query.query_builder import CypherQueryBuilder, QueryTemplates
from app.services.graph_query.query_executor import GraphQueryExecutor, ResultParser


class TestQueryTemplates:
    """Test suite for QueryTemplates"""

    def test_coverage_amount_template(self):
        """보장 금액 템플릿 테스트"""
        template = QueryTemplates.COVERAGE_AMOUNT

        assert template.name == "coverage_amount"
        assert "disease_name" in template.required_params
        assert "MATCH" in template.template
        assert "Disease" in template.template
        assert "Coverage" in template.template

    def test_coverage_check_template(self):
        """보장 여부 확인 템플릿 테스트"""
        template = QueryTemplates.COVERAGE_CHECK

        assert template.name == "coverage_check"
        assert "disease_name" in template.required_params
        assert "OPTIONAL MATCH" in template.template

    def test_disease_comparison_template(self):
        """질병 비교 템플릿 테스트"""
        template = QueryTemplates.DISEASE_COMPARISON

        assert template.name == "disease_comparison"
        assert "disease1" in template.required_params
        assert "disease2" in template.required_params

    def test_template_validate_params(self):
        """템플릿 파라미터 검증 테스트"""
        template = QueryTemplates.COVERAGE_AMOUNT

        # 유효한 파라미터
        assert template.validate_params({"disease_name": "갑상선암"}) is True

        # 누락된 파라미터
        assert template.validate_params({}) is False


class TestCypherQueryBuilder:
    """Test suite for CypherQueryBuilder"""

    @pytest.fixture
    def builder(self):
        """쿼리 빌더 인스턴스"""
        return CypherQueryBuilder()

    def test_build_coverage_amount_query(self, builder):
        """보장 금액 쿼리 생성 테스트"""
        analysis = QueryAnalysisResult(
            original_query="갑상선암 보장 금액은?",
            intent=QueryIntent.COVERAGE_AMOUNT,
            intent_confidence=0.95,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                )
            ],
            keywords=["갑상선암", "보장", "금액"],
        )

        cypher = builder.build(analysis)

        assert isinstance(cypher, CypherQuery)
        assert "Disease" in cypher.query
        assert "Coverage" in cypher.query
        assert cypher.parameters["disease_name"] == "갑상선암"

    def test_build_coverage_check_query(self, builder):
        """보장 여부 확인 쿼리 생성 테스트"""
        analysis = QueryAnalysisResult(
            original_query="간암은 보장되나요?",
            intent=QueryIntent.COVERAGE_CHECK,
            intent_confidence=0.9,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="간암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.95,
                )
            ],
            keywords=["간암", "보장"],
        )

        cypher = builder.build(analysis)

        assert isinstance(cypher, CypherQuery)
        assert cypher.parameters["disease_name"] == "간암"

    def test_build_disease_comparison_query(self, builder):
        """질병 비교 쿼리 생성 테스트"""
        analysis = QueryAnalysisResult(
            original_query="갑상선암과 간암의 보장 차이는?",
            intent=QueryIntent.DISEASE_COMPARISON,
            intent_confidence=0.85,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                ),
                ExtractedEntity(
                    text="간암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                ),
            ],
            keywords=["갑상선암", "간암", "차이"],
        )

        cypher = builder.build(analysis)

        assert cypher.parameters["disease1"] == "갑상선암"
        assert cypher.parameters["disease2"] == "간암"

    def test_build_comparison_missing_entities(self, builder):
        """비교 쿼리에 엔티티 부족 시 오류 테스트"""
        analysis = QueryAnalysisResult(
            original_query="갑상선암 비교해주세요",
            intent=QueryIntent.DISEASE_COMPARISON,
            intent_confidence=0.7,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                )
            ],
            keywords=["갑상선암", "비교"],
        )

        with pytest.raises(ValueError, match="at least 2 diseases"):
            builder.build(analysis)

    def test_build_exclusions_query(self, builder):
        """제외 항목 쿼리 생성 테스트"""
        analysis = QueryAnalysisResult(
            original_query="제외되는 질병은?",
            intent=QueryIntent.EXCLUSION_CHECK,
            intent_confidence=0.9,
            query_type=QueryType.DIRECT_LOOKUP,
            entities=[],
            keywords=["제외", "질병"],
        )

        cypher = builder.build(analysis)

        assert "EXCLUDES" in cypher.query
        assert len(cypher.parameters) == 0  # 파라미터 불필요

    def test_build_waiting_period_query(self, builder):
        """대기기간 쿼리 생성 테스트"""
        analysis = QueryAnalysisResult(
            original_query="대기기간은 얼마나 되나요?",
            intent=QueryIntent.WAITING_PERIOD,
            intent_confidence=0.9,
            query_type=QueryType.DIRECT_LOOKUP,
            entities=[],
            keywords=["대기기간"],
        )

        cypher = builder.build(analysis)

        assert "waiting_period" in cypher.query
        assert "disease_name" in cypher.parameters

    def test_build_custom_query(self, builder):
        """커스텀 쿼리 생성 테스트"""
        custom_cypher = "MATCH (n) RETURN n LIMIT 10"
        params = {"limit": 10}

        cypher = builder.build_custom_query(custom_cypher, params)

        assert cypher.query == custom_cypher
        assert cypher.parameters == params

    def test_validate_query(self, builder):
        """쿼리 유효성 검증 테스트"""
        # 유효한 쿼리
        valid_query = CypherQuery(
            query="MATCH (n) RETURN n",
            parameters={},
            result_type=QueryResultType.TABLE,
        )
        assert builder.validate_query(valid_query) is True

        # 빈 쿼리
        invalid_query = CypherQuery(
            query="",
            parameters={},
            result_type=QueryResultType.TABLE,
        )
        assert builder.validate_query(invalid_query) is False

    def test_list_templates(self, builder):
        """템플릿 목록 조회 테스트"""
        templates = builder.list_templates()

        assert len(templates) > 0
        assert all(isinstance(t, QueryTemplate) for t in templates)

        # 주요 템플릿 확인
        template_names = [t.name for t in templates]
        assert "coverage_amount" in template_names
        assert "coverage_check" in template_names
        assert "disease_comparison" in template_names

    def test_get_template_by_name(self, builder):
        """이름으로 템플릿 조회 테스트"""
        template = builder.get_template_by_name("coverage_amount")

        assert template is not None
        assert template.name == "coverage_amount"

        # 존재하지 않는 템플릿
        assert builder.get_template_by_name("nonexistent") is None


class TestResultParser:
    """Test suite for ResultParser"""

    def test_parse_table_results(self):
        """테이블 결과 파싱 테스트"""
        # Mock Neo4j Record
        mock_record = Mock()
        mock_record.keys.return_value = ["coverage_name", "amount", "disease_name"]
        mock_record.__getitem__ = lambda self, key: {
            "coverage_name": "암진단특약",
            "amount": 10000000,
            "disease_name": "갑상선암",
        }[key]

        records = [mock_record]

        result = ResultParser.parse_records(records, QueryResultType.TABLE)

        assert result.result_type == QueryResultType.TABLE
        assert len(result.table) == 1
        assert result.table[0]["coverage_name"] == "암진단특약"
        assert result.table[0]["amount"] == 10000000

    def test_parse_empty_results(self):
        """빈 결과 파싱 테스트"""
        result = ResultParser.parse_records([], QueryResultType.TABLE)

        assert result.total_count == 0
        assert result.is_empty() is True

    def test_parse_coverage_results(self):
        """보장 결과 파싱 테스트"""
        query_result = QueryResult(
            result_type=QueryResultType.TABLE,
            table=[
                {
                    "coverage_name": "암진단특약",
                    "disease_name": "갑상선암",
                    "amount": 10000000,
                    "kcd_code": "C73",
                    "conditions": ["90일 대기기간"],
                }
            ],
            total_count=1,
        )

        coverage_results = ResultParser.parse_coverage_results(query_result)

        assert len(coverage_results) == 1
        assert coverage_results[0].coverage_name == "암진단특약"
        assert coverage_results[0].disease_name == "갑상선암"
        assert coverage_results[0].amount == 10000000

    def test_parse_disease_results(self):
        """질병 결과 파싱 테스트"""
        query_result = QueryResult(
            result_type=QueryResultType.TABLE,
            table=[
                {
                    "disease_name": "갑상선암",
                    "standard_name": "ThyroidCancer",
                    "kcd_code": "C73",
                    "coverages": [
                        {"coverage_name": "암진단특약", "amount": 10000000},
                        {"coverage_name": "수술특약", "amount": 5000000},
                    ],
                }
            ],
            total_count=1,
        )

        disease_results = ResultParser.parse_disease_results(query_result)

        assert len(disease_results) == 1
        assert disease_results[0].disease_name == "갑상선암"
        assert len(disease_results[0].coverages) == 2
        assert len(disease_results[0].amounts) == 2

    def test_parse_comparison_result(self):
        """비교 결과 파싱 테스트"""
        query_result = QueryResult(
            result_type=QueryResultType.TABLE,
            table=[
                {
                    "disease1_name": "갑상선암",
                    "disease1_kcd": "C73",
                    "cov1": [{"name": "암진단특약", "amount": 10000000}],
                    "disease2_name": "간암",
                    "disease2_kcd": "C22",
                    "cov2": [{"name": "암진단특약", "amount": 10000000}],
                }
            ],
            total_count=1,
        )

        comparison = ResultParser.parse_comparison_result(query_result)

        assert comparison is not None
        assert comparison.item1["name"] == "갑상선암"
        assert comparison.item2["name"] == "간암"

    def test_analyze_differences(self):
        """차이점 분석 테스트"""
        item1 = {
            "name": "갑상선암",
            "coverages": [
                {"name": "암진단특약"},
                {"name": "수술특약"},
            ],
        }
        item2 = {
            "name": "간암",
            "coverages": [
                {"name": "암진단특약"},
                {"name": "입원특약"},
            ],
        }

        differences, similarities = ResultParser._analyze_differences(item1, item2)

        # 공통점: 암진단특약
        assert len(similarities) > 0

        # 차이점: 수술특약 vs 입원특약
        assert len(differences) > 0


class TestGraphQueryModels:
    """Test suite for Graph Query Models"""

    def test_cypher_query_creation(self):
        """Cypher 쿼리 생성 테스트"""
        query = CypherQuery(
            query="MATCH (n) RETURN n",
            parameters={"limit": 10},
            result_type=QueryResultType.TABLE,
        )

        assert query.query == "MATCH (n) RETURN n"
        assert query.parameters["limit"] == 10

    def test_query_result_is_empty(self):
        """QueryResult 비어있음 확인 테스트"""
        empty_result = QueryResult(
            result_type=QueryResultType.TABLE,
            total_count=0,
        )

        assert empty_result.is_empty() is True

        non_empty_result = QueryResult(
            result_type=QueryResultType.TABLE,
            table=[{"key": "value"}],
            total_count=1,
        )

        assert non_empty_result.is_empty() is False

    def test_graph_node_creation(self):
        """GraphNode 생성 테스트"""
        node = GraphNode(
            node_id="123",
            labels=["Disease"],
            properties={"korean_name": "갑상선암", "kcd_code": "C73"},
        )

        assert node.get_property("korean_name") == "갑상선암"
        assert node.has_label("Disease") is True
        assert node.has_label("Coverage") is False

    def test_graph_relationship_creation(self):
        """GraphRelationship 생성 테스트"""
        rel = GraphRelationship(
            relationship_id="456",
            type="COVERS",
            start_node="123",
            end_node="789",
            properties={"conditions": ["90일 대기기간"]},
        )

        assert rel.type == "COVERS"
        assert rel.get_property("conditions") == ["90일 대기기간"]

    def test_graph_path_creation(self):
        """GraphPath 생성 테스트"""
        node1 = GraphNode(node_id="1", labels=["Disease"], properties={})
        node2 = GraphNode(node_id="2", labels=["Coverage"], properties={})
        rel = GraphRelationship(
            relationship_id="r1",
            type="COVERS",
            start_node="1",
            end_node="2",
            properties={},
        )

        path = GraphPath(
            nodes=[node1, node2],
            relationships=[rel],
            length=1,
        )

        assert path.get_start_node() == node1
        assert path.get_end_node() == node2
        assert len(path.relationships) == 1

    def test_coverage_query_result(self):
        """CoverageQueryResult 생성 테스트"""
        coverage = CoverageQueryResult(
            coverage_name="암진단특약",
            disease_name="갑상선암",
            amount=10000000,
            kcd_code="C73",
            conditions=["90일 대기기간"],
            waiting_period_days=90,
        )

        assert coverage.coverage_name == "암진단특약"
        assert coverage.amount == 10000000

    def test_disease_query_result(self):
        """DiseaseQueryResult 생성 테스트"""
        disease = DiseaseQueryResult(
            disease_name="갑상선암",
            standard_name="ThyroidCancer",
            kcd_code="C73",
            coverages=["암진단특약", "수술특약"],
            amounts=[10000000, 5000000],
        )

        assert disease.disease_name == "갑상선암"
        assert len(disease.coverages) == 2

    def test_comparison_result(self):
        """ComparisonResult 생성 테스트"""
        comparison = ComparisonResult(
            item1={"name": "갑상선암", "kcd_code": "C73"},
            item2={"name": "간암", "kcd_code": "C22"},
            differences=[{"field": "amount", "diff": 1000000}],
            similarities=[{"field": "coverage", "common": ["암진단특약"]}],
        )

        assert comparison.item1["name"] == "갑상선암"
        assert comparison.item2["name"] == "간암"
        assert len(comparison.differences) == 1
        assert len(comparison.similarities) == 1


class TestGraphQueryExecutor:
    """Test suite for GraphQueryExecutor"""

    @pytest.fixture
    def mock_neo4j(self):
        """Mock Neo4j 서비스"""
        mock = Mock()
        mock.driver = Mock()
        return mock

    @pytest.fixture
    def executor(self, mock_neo4j):
        """쿼리 실행기 인스턴스"""
        return GraphQueryExecutor(mock_neo4j)

    @pytest.mark.asyncio
    async def test_execute_coverage_amount_query(self, executor, mock_neo4j):
        """보장 금액 쿼리 실행 테스트"""
        # Mock 결과
        mock_record = Mock()
        mock_record.keys.return_value = ["coverage_name", "amount", "disease_name"]
        mock_record.__getitem__ = lambda self, key: {
            "coverage_name": "암진단특약",
            "amount": 10000000,
            "disease_name": "갑상선암",
        }[key]

        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value = [mock_record]
        mock_neo4j.driver.session.return_value = mock_session

        # 분석 결과
        analysis = QueryAnalysisResult(
            original_query="갑상선암 보장 금액은?",
            intent=QueryIntent.COVERAGE_AMOUNT,
            intent_confidence=0.95,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                )
            ],
            keywords=["갑상선암", "보장", "금액"],
        )

        response = await executor.execute(analysis)

        assert response.success is True
        assert response.result.total_count >= 0
        assert "갑상선암" in response.cypher_query

    @pytest.mark.asyncio
    async def test_execute_query_with_error(self, executor, mock_neo4j):
        """쿼리 실행 오류 테스트"""
        # Mock 오류
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.side_effect = Exception("Connection error")
        mock_neo4j.driver.session.return_value = mock_session

        analysis = QueryAnalysisResult(
            original_query="테스트 질문",
            intent=QueryIntent.COVERAGE_AMOUNT,
            intent_confidence=0.9,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                )
            ],
            keywords=["갑상선암"],
        )

        response = await executor.execute(analysis)

        assert response.success is False
        assert response.error is not None
        assert "Connection error" in response.error.message
