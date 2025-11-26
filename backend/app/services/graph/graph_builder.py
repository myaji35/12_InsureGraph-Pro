"""
Graph Builder

Integrates all ingestion components to build Neo4j knowledge graph.
Combines:
- Legal Structure Parser (Story 1.3)
- Critical Data Extractor (Story 1.4)
- Relation Extractor (Story 1.5)
- Entity Linker (Story 1.6)
- Neo4j Service (Story 1.7)
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib

from app.models.document import ParsedDocument
from app.models.critical_data import CriticalData
from app.models.relation import RelationExtractionResult, ExtractedRelation
from app.models.ontology import EntityLinkResult
from app.models.graph import (
    ProductNode,
    CoverageNode,
    DiseaseNode,
    ConditionNode,
    ClauseNode,
    GraphBatch,
    GraphStats,
    RelationType,
    NodeType,
    CoversRelationship,
    ExcludesRelationship,
    RequiresRelationship,
    DefinedInRelationship,
    GraphRelationship,
)

from app.services.ingestion.legal_parser import LegalStructureParser
from app.services.ingestion.critical_data_extractor import CriticalDataExtractor
from app.services.ingestion.relation_extractor import RelationExtractor
from app.services.ingestion.entity_linker import EntityLinker
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.embedding_service import EmbeddingService, create_embedding_service

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds Neo4j knowledge graph from insurance documents"""

    def __init__(
        self,
        neo4j_service: Neo4jService,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize graph builder

        Args:
            neo4j_service: Neo4j service for graph operations
            embedding_service: Embedding service for semantic search (optional)
        """
        self.neo4j = neo4j_service
        self.embedding_service = embedding_service

        # Initialize ingestion components
        self.legal_parser = LegalStructureParser()
        self.critical_extractor = CriticalDataExtractor()
        self.relation_extractor = RelationExtractor()
        self.entity_linker = EntityLinker()

    async def build_graph_from_document(
        self,
        ocr_text: str,
        product_info: Dict[str, Any],
        generate_embeddings: bool = True,
    ) -> GraphStats:
        """
        Build knowledge graph from OCR text

        Args:
            ocr_text: OCR extracted text from PDF
            product_info: Product metadata (name, company, type, etc.)
            generate_embeddings: Whether to generate embeddings for clauses

        Returns:
            GraphStats with construction statistics
        """
        logger.info(f"Building graph for product: {product_info.get('product_name')}")

        # Step 1: Parse legal structure (Story 1.3)
        logger.info("Step 1: Parsing legal structure...")
        parsed_doc = self.legal_parser.parse(ocr_text)

        # Step 2: Extract critical data (Story 1.4)
        logger.info("Step 2: Extracting critical data...")
        critical_data = self.critical_extractor.extract(ocr_text)

        # Step 3: Extract relations (Story 1.5)
        logger.info("Step 3: Extracting relations...")
        relation_results = []
        for article in parsed_doc.articles:
            for paragraph in article.paragraphs:
                # Extract relations from each paragraph
                result = await self.relation_extractor.extract(
                    clause_text=paragraph.text,
                    critical_data=critical_data,
                    use_cascade=True,
                )
                relation_results.append(result)

        # Step 4: Build graph batch
        logger.info("Step 4: Building graph batch...")
        batch = await self._create_graph_batch(
            product_info=product_info,
            parsed_doc=parsed_doc,
            critical_data=critical_data,
            relation_results=relation_results,
            generate_embeddings=generate_embeddings,
        )

        # Step 5: Insert into Neo4j
        logger.info("Step 5: Inserting into Neo4j...")
        stats = self.neo4j.create_batch(batch)

        logger.info(f"Graph construction complete: {stats.total_nodes} nodes, {stats.total_relationships} relationships")

        return stats

    async def _create_graph_batch(
        self,
        product_info: Dict[str, Any],
        parsed_doc: ParsedDocument,
        critical_data: CriticalData,
        relation_results: List[RelationExtractionResult],
        generate_embeddings: bool,
    ) -> GraphBatch:
        """Create graph batch from parsed data"""
        batch = GraphBatch()

        # 1. Create Product node
        product_node = self._create_product_node(product_info, parsed_doc)
        batch.products.append(product_node)

        # 2. Create Clause nodes
        clause_nodes = await self._create_clause_nodes(
            parsed_doc, critical_data, generate_embeddings
        )
        batch.clauses.extend(clause_nodes)

        # Track unique entities
        coverage_map = {}  # coverage_name -> CoverageNode
        disease_map = {}  # standard_name -> DiseaseNode
        condition_map = {}  # condition_id -> ConditionNode

        # 3. Process relations and create Coverage/Disease/Condition nodes
        for result in relation_results:
            for relation in result.relations:
                # Create Coverage node (subject)
                if relation.subject not in coverage_map:
                    coverage_node = self._create_coverage_node(relation)
                    coverage_map[relation.subject] = coverage_node
                    batch.coverages.append(coverage_node)

                # Link disease entity (object)
                entity_result = self.entity_linker.link(relation.object)

                if entity_result.is_successful():
                    # Create Disease node
                    standard_name = entity_result.matched_entity.standard_name
                    if standard_name not in disease_map:
                        disease_node = self._create_disease_node(entity_result)
                        disease_map[standard_name] = disease_node
                        batch.diseases.append(disease_node)

                    # Create relationship
                    if relation.action in ["COVERS", "EXCLUDES"]:
                        rel = self._create_coverage_disease_relationship(
                            coverage=coverage_map[relation.subject],
                            disease=disease_map[standard_name],
                            relation=relation,
                        )
                        batch.relationships.append(rel)

                # Create Condition nodes from relation conditions
                for condition in relation.conditions:
                    condition_id = self._generate_condition_id(condition.condition_type, condition.description)
                    if condition_id not in condition_map:
                        condition_node = self._create_condition_node(condition, condition_id)
                        condition_map[condition_id] = condition_node
                        batch.conditions.append(condition_node)

                        # Create REQUIRES relationship
                        rel = RequiresRelationship(
                            relation_id=f"req_{coverage_map[relation.subject].coverage_id}_{condition_id}",
                            source_node_id=coverage_map[relation.subject].coverage_id,
                            target_node_id=condition_id,
                            confidence=relation.confidence,
                        )
                        batch.relationships.append(rel)

        # 4. Create Product -> Coverage relationships
        for coverage in batch.coverages:
            rel = self._create_product_coverage_relationship(product_node, coverage)
            batch.relationships.append(rel)

        return batch

    def _create_product_node(
        self, product_info: Dict[str, Any], parsed_doc: ParsedDocument
    ) -> ProductNode:
        """Create Product node"""
        product_id = self._generate_id(f"product_{product_info.get('product_name')}")

        return ProductNode(
            product_id=product_id,
            product_name=product_info.get("product_name", "Unknown"),
            company=product_info.get("company", "Unknown"),
            product_type=product_info.get("product_type", "보험"),
            version=product_info.get("version"),
            effective_date=product_info.get("effective_date"),
            document_id=product_info.get("document_id"),
            total_pages=len(set(a.page for a in parsed_doc.articles)),
            created_at=datetime.utcnow().isoformat(),
        )

    async def _create_clause_nodes(
        self,
        parsed_doc: ParsedDocument,
        critical_data: CriticalData,
        generate_embeddings: bool,
    ) -> List[ClauseNode]:
        """Create Clause nodes from parsed document"""
        clause_nodes = []
        clause_texts = []

        # Collect all clauses
        for article in parsed_doc.articles:
            for paragraph in article.paragraphs:
                clause_id = self._generate_id(
                    f"clause_{article.article_num}_{paragraph.paragraph_num}"
                )

                clause_node = ClauseNode(
                    clause_id=clause_id,
                    article_num=article.article_num,
                    article_title=article.title,
                    paragraph_num=paragraph.paragraph_num,
                    clause_text=paragraph.text,
                    page=article.page,
                    has_amounts=len(critical_data.amounts) > 0,
                    has_periods=len(critical_data.periods) > 0,
                    has_kcd_codes=len(critical_data.kcd_codes) > 0,
                )

                clause_nodes.append(clause_node)
                clause_texts.append(paragraph.text)

        # Generate embeddings in batch
        if generate_embeddings and self.embedding_service:
            logger.info(f"Generating embeddings for {len(clause_texts)} clauses...")
            embeddings = await self.embedding_service.embed_batch(clause_texts)

            for i, embedding in enumerate(embeddings):
                clause_nodes[i].embedding = embedding
                clause_nodes[i].embedding_model = (
                    self.embedding_service.__class__.__name__
                )

        return clause_nodes

    def _create_coverage_node(self, relation: ExtractedRelation) -> CoverageNode:
        """Create Coverage node from relation"""
        coverage_id = self._generate_id(f"coverage_{relation.subject}")

        # Extract benefit amount from conditions
        benefit_amount = None
        for condition in relation.conditions:
            if condition.amount:
                benefit_amount = condition.amount
                break

        return CoverageNode(
            coverage_id=coverage_id,
            coverage_name=relation.subject,
            coverage_type="특약",  # Default type
            benefit_amount=benefit_amount,
            description=relation.reasoning,
        )

    def _create_disease_node(self, entity_result: EntityLinkResult) -> DiseaseNode:
        """Create Disease node from entity link result"""
        entity = entity_result.matched_entity
        disease_id = self._generate_id(f"disease_{entity.standard_name}")

        return DiseaseNode(
            disease_id=disease_id,
            standard_name=entity.standard_name,
            korean_names=entity.korean_names,
            english_names=entity.english_names,
            kcd_codes=entity.kcd_codes,
            category=entity.category,
            severity=entity.severity,
            description=entity.description,
        )

    def _create_condition_node(
        self, condition: Any, condition_id: str
    ) -> ConditionNode:
        """Create Condition node from relation condition"""
        return ConditionNode(
            condition_id=condition_id,
            condition_type=condition.condition_type,
            description=condition.description,
            waiting_period_days=condition.period,
            amount_limit=condition.amount,
        )

    def _create_coverage_disease_relationship(
        self, coverage: CoverageNode, disease: DiseaseNode, relation: ExtractedRelation
    ) -> GraphRelationship:
        """Create COVERS or EXCLUDES relationship"""
        rel_id = f"{relation.action.lower()}_{coverage.coverage_id}_{disease.disease_id}"

        if relation.action == "COVERS":
            return CoversRelationship(
                relation_id=rel_id,
                source_node_id=coverage.coverage_id,
                target_node_id=disease.disease_id,
                confidence=relation.confidence,
                extracted_by="llm",
                reasoning=relation.reasoning,
                benefit_amount=coverage.benefit_amount,
            )
        elif relation.action == "EXCLUDES":
            return ExcludesRelationship(
                relation_id=rel_id,
                source_node_id=coverage.coverage_id,
                target_node_id=disease.disease_id,
                confidence=relation.confidence,
                extracted_by="llm",
                reasoning=relation.reasoning,
                exclusion_reason=relation.reasoning,
            )

    def _create_product_coverage_relationship(
        self, product: ProductNode, coverage: CoverageNode
    ) -> GraphRelationship:
        """Create Product -> Coverage relationship"""
        rel_id = f"has_{product.product_id}_{coverage.coverage_id}"

        return GraphRelationship(
            relation_id=rel_id,
            relation_type=RelationType.HAS_COVERAGE,
            source_node_id=product.product_id,
            target_node_id=coverage.coverage_id,
        )

    def _generate_id(self, text: str) -> str:
        """Generate deterministic ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def _generate_condition_id(self, condition_type: str, description: str) -> str:
        """Generate condition ID"""
        return self._generate_id(f"{condition_type}_{description}")
