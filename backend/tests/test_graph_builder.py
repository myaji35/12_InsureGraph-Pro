"""
Unit tests for Graph Builder

Tests the full graph construction pipeline integrating all components.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.graph.graph_builder import GraphBuilder
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.embedding_service import MockEmbeddingService
from app.models.document import ParsedDocument, Article, Paragraph
from app.models.critical_data import CriticalData, AmountData
from app.models.relation import (
    RelationExtractionResult,
    ExtractedRelation,
    RelationCondition,
)
from app.models.ontology import DiseaseEntity, EntityLinkResult
from app.models.graph import GraphBatch, GraphStats, ProductNode, CoverageNode


class TestGraphBuilder:
    """Test suite for GraphBuilder"""

    @pytest.fixture
    def mock_neo4j_service(self):
        """Create mock Neo4j service"""
        service = Mock(spec=Neo4jService)
        service.create_batch = Mock(return_value=GraphStats(
            total_nodes=10,
            total_relationships=5,
            nodes_by_type={"Product": 1, "Coverage": 2, "Disease": 3, "Clause": 4},
            relationships_by_type={"COVERS": 3, "REQUIRES": 2},
            construction_time_seconds=1.5,
        ))
        return service

    @pytest.fixture
    def embedding_service(self):
        """Create mock embedding service"""
        return MockEmbeddingService(dimension=1536)

    @pytest.fixture
    def graph_builder(self, mock_neo4j_service, embedding_service):
        """Create graph builder instance"""
        return GraphBuilder(
            neo4j_service=mock_neo4j_service,
            embedding_service=embedding_service,
        )

    @pytest.fixture
    def sample_parsed_doc(self):
        """Create sample parsed document"""
        article = Article(
            article_num="제1조",
            title="보험금의 지급사유",
            page=1,
            paragraphs=[
                Paragraph(
                    paragraph_num="①",
                    text="회사는 피보험자가 갑상선암으로 진단확정된 경우 1천만원을 지급합니다.",
                    subclauses=[],
                )
            ],
            raw_text="제1조 [보험금의 지급사유] ① 회사는 피보험자가 갑상선암으로 진단확정된 경우 1천만원을 지급합니다.",
        )

        return ParsedDocument(articles=[article])

    @pytest.fixture
    def sample_critical_data(self):
        """Create sample critical data"""
        return CriticalData(
            amounts=[
                AmountData(
                    value=10000000,
                    original_text="1천만원",
                    position=30,
                    confidence=1.0,
                )
            ],
            periods=[],
            kcd_codes=[],
        )

    @pytest.fixture
    def sample_relation_results(self):
        """Create sample relation results"""
        return [
            RelationExtractionResult(
                clause_text="회사는 피보험자가 갑상선암으로 진단확정된 경우 1천만원을 지급합니다.",
                relations=[
                    ExtractedRelation(
                        subject="암진단특약",
                        action="COVERS",
                        object="갑상선암",
                        conditions=[
                            RelationCondition(
                                condition_type="benefit_amount",
                                description="진단 시 1천만원 지급",
                                amount=10000000,
                            )
                        ],
                        confidence=0.95,
                        reasoning="갑상선암 진단 확정 시 보험금 지급",
                    )
                ],
                extraction_method="llm",
            )
        ]

    @pytest.fixture
    def sample_product_info(self):
        """Create sample product info"""
        return {
            "product_name": "무배당 ABC암보험",
            "company": "ABC생명",
            "product_type": "암보험",
            "version": "2023.1",
            "effective_date": "2023-01-01",
            "document_id": "doc_001",
        }

    def test_builder_initialization(self, graph_builder):
        """Test graph builder initialization"""
        assert graph_builder.neo4j is not None
        assert graph_builder.embedding_service is not None
        assert graph_builder.legal_parser is not None
        assert graph_builder.critical_extractor is not None
        assert graph_builder.relation_extractor is not None
        assert graph_builder.entity_linker is not None

    @pytest.mark.asyncio
    async def test_build_graph_from_document(
        self, graph_builder, sample_product_info, mock_neo4j_service
    ):
        """Test full graph construction from document"""
        ocr_text = """
        제1조 [보험금의 지급사유]
        ① 회사는 피보험자가 갑상선암(C73)으로 진단확정된 경우 1천만원을 지급합니다.
        """

        # Mock the relation extractor to return sample relations
        mock_result = RelationExtractionResult(
            clause_text="회사는 피보험자가 갑상선암(C73)으로 진단확정된 경우 1천만원을 지급합니다.",
            relations=[
                ExtractedRelation(
                    subject="암진단특약",
                    action="COVERS",
                    object="갑상선암",
                    conditions=[],
                    confidence=0.95,
                    reasoning="갑상선암 진단 시 보험금 지급",
                )
            ],
            extraction_method="llm",
        )
        graph_builder.relation_extractor.extract = AsyncMock(return_value=mock_result)

        # Build graph
        stats = await graph_builder.build_graph_from_document(
            ocr_text=ocr_text,
            product_info=sample_product_info,
            generate_embeddings=True,
        )

        # Verify stats
        assert stats.total_nodes == 10
        assert stats.total_relationships == 5
        assert mock_neo4j_service.create_batch.called

    def test_create_product_node(self, graph_builder, sample_product_info, sample_parsed_doc):
        """Test product node creation"""
        product_node = graph_builder._create_product_node(
            sample_product_info, sample_parsed_doc
        )

        assert isinstance(product_node, ProductNode)
        assert product_node.product_name == "무배당 ABC암보험"
        assert product_node.company == "ABC생명"
        assert product_node.product_type == "암보험"
        assert product_node.total_pages == 1

    @pytest.mark.asyncio
    async def test_create_clause_nodes(
        self, graph_builder, sample_parsed_doc, sample_critical_data
    ):
        """Test clause node creation"""
        clause_nodes = await graph_builder._create_clause_nodes(
            sample_parsed_doc, sample_critical_data, generate_embeddings=True
        )

        assert len(clause_nodes) == 1
        clause = clause_nodes[0]
        assert clause.article_num == "제1조"
        assert clause.paragraph_num == "①"
        assert "갑상선암" in clause.clause_text
        assert clause.has_amounts is True
        assert clause.embedding is not None
        assert len(clause.embedding) == 1536  # MockEmbeddingService dimension

    def test_create_coverage_node(self, graph_builder, sample_relation_results):
        """Test coverage node creation"""
        relation = sample_relation_results[0].relations[0]
        coverage_node = graph_builder._create_coverage_node(relation)

        assert coverage_node.coverage_name == "암진단특약"
        assert coverage_node.coverage_type == "특약"
        assert coverage_node.benefit_amount == 10000000

    def test_create_disease_node(self, graph_builder):
        """Test disease node creation"""
        entity = DiseaseEntity(
            standard_name="ThyroidCancer",
            korean_names=["갑상선암"],
            english_names=["Thyroid Cancer"],
            kcd_codes=["C73"],
            category="cancer",
            severity="minor",
        )

        entity_result = EntityLinkResult(
            query="갑상선암",
            matched_entity=entity,
            match_score=1.0,
            match_method="exact",
        )

        disease_node = graph_builder._create_disease_node(entity_result)

        assert disease_node.standard_name == "ThyroidCancer"
        assert "갑상선암" in disease_node.korean_names
        assert "C73" in disease_node.kcd_codes
        assert disease_node.category == "cancer"
        assert disease_node.severity == "minor"

    def test_create_condition_node(self, graph_builder):
        """Test condition node creation"""
        condition = RelationCondition(
            condition_type="waiting_period",
            description="90일 대기기간",
            period=90,
        )

        condition_id = graph_builder._generate_condition_id(
            condition.condition_type, condition.description
        )
        condition_node = graph_builder._create_condition_node(condition, condition_id)

        assert condition_node.condition_type == "waiting_period"
        assert condition_node.description == "90일 대기기간"
        assert condition_node.waiting_period_days == 90

    @pytest.mark.asyncio
    async def test_create_graph_batch(
        self,
        graph_builder,
        sample_product_info,
        sample_parsed_doc,
        sample_critical_data,
        sample_relation_results,
    ):
        """Test graph batch creation"""
        batch = await graph_builder._create_graph_batch(
            product_info=sample_product_info,
            parsed_doc=sample_parsed_doc,
            critical_data=sample_critical_data,
            relation_results=sample_relation_results,
            generate_embeddings=True,
        )

        assert isinstance(batch, GraphBatch)
        assert len(batch.products) == 1
        assert len(batch.clauses) == 1
        assert len(batch.coverages) >= 1
        assert len(batch.diseases) >= 1

        # Check that embeddings were generated
        if len(batch.clauses) > 0:
            assert batch.clauses[0].embedding is not None

    def test_generate_id_deterministic(self, graph_builder):
        """Test that ID generation is deterministic"""
        id1 = graph_builder._generate_id("test_text")
        id2 = graph_builder._generate_id("test_text")
        id3 = graph_builder._generate_id("different_text")

        assert id1 == id2
        assert id1 != id3
        assert len(id1) == 16  # MD5 hash truncated to 16 chars

    @pytest.mark.asyncio
    async def test_batch_without_embeddings(
        self,
        mock_neo4j_service,
        sample_product_info,
    ):
        """Test graph construction without embeddings"""
        # Create builder without embedding service
        builder = GraphBuilder(neo4j_service=mock_neo4j_service, embedding_service=None)

        # Mock relation extractor
        builder.relation_extractor.extract = AsyncMock(
            return_value=RelationExtractionResult(
                clause_text="test",
                relations=[],
                extraction_method="llm",
            )
        )

        ocr_text = "제1조 [테스트] ① 테스트 조항입니다."

        stats = await builder.build_graph_from_document(
            ocr_text=ocr_text,
            product_info=sample_product_info,
            generate_embeddings=False,
        )

        assert stats.total_nodes > 0

    def test_coverage_disease_relationship_covers(self, graph_builder):
        """Test COVERS relationship creation"""
        coverage = CoverageNode(
            coverage_id="cov_001",
            coverage_name="암진단특약",
            coverage_type="특약",
            benefit_amount=10000000,
        )

        entity = DiseaseEntity(
            standard_name="ThyroidCancer",
            korean_names=["갑상선암"],
            english_names=["Thyroid Cancer"],
            kcd_codes=["C73"],
            category="cancer",
        )
        entity_result = EntityLinkResult(
            query="갑상선암", matched_entity=entity, match_score=1.0, match_method="exact"
        )
        disease = graph_builder._create_disease_node(entity_result)

        relation = ExtractedRelation(
            subject="암진단특약",
            action="COVERS",
            object="갑상선암",
            conditions=[],
            confidence=0.95,
            reasoning="보험금 지급",
        )

        rel = graph_builder._create_coverage_disease_relationship(
            coverage, disease, relation
        )

        assert rel.relation_type.value == "COVERS"
        assert rel.confidence == 0.95

    def test_coverage_disease_relationship_excludes(self, graph_builder):
        """Test EXCLUDES relationship creation"""
        coverage = CoverageNode(
            coverage_id="cov_001",
            coverage_name="암진단특약",
            coverage_type="특약",
        )

        entity = DiseaseEntity(
            standard_name="ThyroidCancer",
            korean_names=["갑상선암"],
            english_names=["Thyroid Cancer"],
            kcd_codes=["C73"],
            category="cancer",
        )
        entity_result = EntityLinkResult(
            query="갑상선암", matched_entity=entity, match_score=1.0, match_method="exact"
        )
        disease = graph_builder._create_disease_node(entity_result)

        relation = ExtractedRelation(
            subject="암진단특약",
            action="EXCLUDES",
            object="갑상선암",
            conditions=[],
            confidence=0.95,
            reasoning="소액암 제외",
        )

        rel = graph_builder._create_coverage_disease_relationship(
            coverage, disease, relation
        )

        assert rel.relation_type.value == "EXCLUDES"
        assert "소액암 제외" in rel.properties.get("exclusion_reason", "")
