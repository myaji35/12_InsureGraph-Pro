"""
Unit tests for Neo4j Service

Tests Neo4j database operations with mocked driver.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from neo4j import Driver, Session

from app.services.graph.neo4j_service import Neo4jService
from app.models.graph import (
    ProductNode,
    CoverageNode,
    DiseaseNode,
    ConditionNode,
    ClauseNode,
    GraphBatch,
    NodeType,
    RelationType,
    GraphRelationship,
)


class TestNeo4jService:
    """Test suite for Neo4jService"""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver"""
        driver = Mock(spec=Driver)
        driver.verify_connectivity = Mock()
        return driver

    @pytest.fixture
    def neo4j_service(self, mock_driver):
        """Create Neo4j service with mocked driver"""
        service = Neo4jService(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password",
        )
        service.driver = mock_driver
        return service

    def test_service_initialization(self):
        """Test service initialization"""
        service = Neo4jService(
            uri="bolt://test:7687",
            user="test_user",
            password="test_pass",
        )

        assert service.uri == "bolt://test:7687"
        assert service.user == "test_user"
        assert service.password == "test_pass"

    def test_service_initialization_from_env(self):
        """Test service initialization from environment variables"""
        with patch.dict(
            "os.environ",
            {
                "NEO4J_URI": "bolt://env:7687",
                "NEO4J_USER": "env_user",
                "NEO4J_PASSWORD": "env_pass",
            },
        ):
            service = Neo4jService()
            assert service.uri == "bolt://env:7687"
            assert service.user == "env_user"
            assert service.password == "env_pass"

    def test_connect(self, neo4j_service, mock_driver):
        """Test database connection"""
        # Already mocked in fixture
        assert neo4j_service.driver is not None
        assert neo4j_service.driver == mock_driver

    def test_close(self, neo4j_service, mock_driver):
        """Test database connection close"""
        neo4j_service.close()
        mock_driver.close.assert_called_once()

    def test_context_manager(self, mock_driver):
        """Test context manager usage"""
        with patch("app.services.graph.neo4j_service.GraphDatabase.driver") as mock_gd:
            mock_gd.return_value = mock_driver

            with Neo4jService() as service:
                assert service.driver is not None

            mock_driver.close.assert_called_once()

    def test_create_product_node(self, neo4j_service):
        """Test product node creation"""
        product = ProductNode(
            product_id="prod_001",
            product_name="ABC암보험",
            company="ABC생명",
            product_type="암보험",
        )

        # Mock session
        mock_session = Mock(spec=Session)
        mock_result = [{"p": {"product_id": "prod_001"}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_product_node(product, mock_session)

        assert mock_session.run.called
        call_args = mock_session.run.call_args
        assert "MERGE (p:Product" in call_args[0][0]

    def test_create_coverage_node(self, neo4j_service):
        """Test coverage node creation"""
        coverage = CoverageNode(
            coverage_id="cov_001",
            coverage_name="암진단특약",
            coverage_type="특약",
            benefit_amount=10000000,
        )

        mock_session = Mock(spec=Session)
        mock_result = [{"c": {"coverage_id": "cov_001"}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_coverage_node(coverage, mock_session)

        assert mock_session.run.called

    def test_create_disease_node(self, neo4j_service):
        """Test disease node creation"""
        disease = DiseaseNode(
            disease_id="dis_001",
            standard_name="ThyroidCancer",
            korean_names=["갑상선암"],
            english_names=["Thyroid Cancer"],
            kcd_codes=["C73"],
            category="cancer",
            severity="minor",
        )

        mock_session = Mock(spec=Session)
        mock_result = [{"d": {"disease_id": "dis_001"}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_disease_node(disease, mock_session)

        assert mock_session.run.called

    def test_create_condition_node(self, neo4j_service):
        """Test condition node creation"""
        condition = ConditionNode(
            condition_id="cond_001",
            condition_type="waiting_period",
            description="90일 대기기간",
            waiting_period_days=90,
        )

        mock_session = Mock(spec=Session)
        mock_result = [{"c": {"condition_id": "cond_001"}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_condition_node(condition, mock_session)

        assert mock_session.run.called

    def test_create_clause_node(self, neo4j_service):
        """Test clause node creation"""
        clause = ClauseNode(
            clause_id="clause_001",
            article_num="제1조",
            article_title="보험금의 지급사유",
            paragraph_num="①",
            clause_text="회사는 피보험자가 암으로 진단확정된 경우 보험금을 지급합니다.",
            page=1,
        )

        mock_session = Mock(spec=Session)
        mock_result = [{"c": {"clause_id": "clause_001"}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_clause_node(clause, mock_session)

        assert mock_session.run.called

    def test_create_typed_relationship(self, neo4j_service):
        """Test typed relationship creation"""
        mock_session = Mock(spec=Session)
        mock_result = [{"r": {}}]
        mock_session.run = Mock(return_value=mock_result)

        result = neo4j_service.create_typed_relationship(
            source_type=NodeType.COVERAGE,
            source_id="cov_001",
            target_type=NodeType.DISEASE,
            target_id="dis_001",
            relation_type=RelationType.COVERS,
            properties={"confidence": 0.95},
            session=mock_session,
        )

        assert mock_session.run.called
        call_args = mock_session.run.call_args
        assert "COVERS" in call_args[0][0]

    def test_create_batch(self, neo4j_service, mock_driver):
        """Test batch creation"""
        batch = GraphBatch()

        # Add nodes
        batch.products.append(
            ProductNode(
                product_id="prod_001",
                product_name="ABC암보험",
                company="ABC생명",
                product_type="암보험",
            )
        )

        batch.coverages.append(
            CoverageNode(
                coverage_id="cov_001",
                coverage_name="암진단특약",
                coverage_type="특약",
            )
        )

        batch.diseases.append(
            DiseaseNode(
                disease_id="dis_001",
                standard_name="ThyroidCancer",
                korean_names=["갑상선암"],
                english_names=["Thyroid Cancer"],
                kcd_codes=["C73"],
                category="cancer",
            )
        )

        # Mock session and transaction
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value.__enter__ = Mock(return_value=mock_tx)
        mock_session.begin_transaction.return_value.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        # Create batch
        stats = neo4j_service.create_batch(batch)

        assert stats.total_nodes == 3
        assert stats.nodes_by_type["Product"] == 1
        assert stats.nodes_by_type["Coverage"] == 1
        assert stats.nodes_by_type["Disease"] == 1

    def test_create_indexes(self, neo4j_service, mock_driver):
        """Test index creation"""
        mock_session = MagicMock()
        mock_session.run = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        neo4j_service.create_indexes()

        # Should create multiple indexes
        assert mock_session.run.call_count >= 5

    def test_get_id_field(self, neo4j_service):
        """Test ID field name retrieval"""
        assert neo4j_service._get_id_field(NodeType.PRODUCT) == "product_id"
        assert neo4j_service._get_id_field(NodeType.COVERAGE) == "coverage_id"
        assert neo4j_service._get_id_field(NodeType.DISEASE) == "disease_id"
        assert neo4j_service._get_id_field(NodeType.CONDITION) == "condition_id"
        assert neo4j_service._get_id_field(NodeType.CLAUSE) == "clause_id"

    def test_clear_database(self, neo4j_service, mock_driver):
        """Test database clearing"""
        mock_session = MagicMock()
        mock_session.run = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        neo4j_service.clear_database()

        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "DETACH DELETE" in call_args[0][0]

    def test_get_graph_stats(self, neo4j_service, mock_driver):
        """Test graph statistics retrieval"""
        mock_session = MagicMock()
        mock_result = [
            {"label": "Product", "count": 5},
            {"label": "Coverage", "count": 10},
        ]
        mock_session.run = Mock(return_value=mock_result)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        stats = neo4j_service.get_graph_stats()

        assert "nodes" in stats
        assert "relationships" in stats

    def test_batch_with_relationships(self, neo4j_service, mock_driver):
        """Test batch creation with relationships"""
        batch = GraphBatch()

        # Add a relationship
        batch.relationships.append(
            GraphRelationship(
                relation_id="rel_001",
                relation_type=RelationType.COVERS,
                source_node_id="cov_001",
                target_node_id="dis_001",
                confidence=0.95,
            )
        )

        # Mock session and transaction
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value.__enter__ = Mock(return_value=mock_tx)
        mock_session.begin_transaction.return_value.__exit__ = Mock(return_value=False)
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        stats = neo4j_service.create_batch(batch)

        assert stats.total_relationships == 1
        assert stats.relationships_by_type["COVERS"] == 1

    def test_graph_batch_total_counts(self):
        """Test GraphBatch total count methods"""
        batch = GraphBatch()

        batch.products.append(
            ProductNode(
                product_id="prod_001",
                product_name="Test",
                company="Test",
                product_type="Test",
            )
        )
        batch.coverages.append(
            CoverageNode(coverage_id="cov_001", coverage_name="Test", coverage_type="Test")
        )
        batch.diseases.append(
            DiseaseNode(
                disease_id="dis_001",
                standard_name="Test",
                korean_names=[],
                english_names=[],
                kcd_codes=[],
                category="test",
            )
        )

        batch.relationships.append(
            GraphRelationship(
                relation_id="rel_001",
                relation_type=RelationType.COVERS,
                source_node_id="cov_001",
                target_node_id="dis_001",
            )
        )

        assert batch.total_nodes() == 3
        assert batch.total_relationships() == 1
