"""
Neo4j Service

Handles Neo4j database connections and operations.
Provides methods for creating nodes, relationships, and indexes.
"""
import os
from typing import List, Dict, Any, Optional, Union
from neo4j import GraphDatabase, Driver, Session
import logging

from app.models.graph import (
    ProductNode,
    CoverageNode,
    DiseaseNode,
    ConditionNode,
    ClauseNode,
    GraphRelationship,
    NodeType,
    RelationType,
    GraphBatch,
    GraphStats,
)

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j database service"""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j service

        Args:
            uri: Neo4j connection URI (defaults to env NEO4J_URI)
            user: Neo4j username (defaults to env NEO4J_USER)
            password: Neo4j password (defaults to env NEO4J_PASSWORD)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")

        self.driver: Optional[Driver] = None

    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # ========================================================================
    # Node Creation
    # ========================================================================

    def create_product_node(
        self, product: ProductNode, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a Product node"""
        cypher = """
        MERGE (p:Product {product_id: $product_id})
        SET p += $properties
        RETURN p
        """
        properties = product.model_dump(exclude_none=True)
        params = {"product_id": product.product_id, "properties": properties}

        return self._execute_write(cypher, params, session)

    def create_coverage_node(
        self, coverage: CoverageNode, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a Coverage node"""
        cypher = """
        MERGE (c:Coverage {coverage_id: $coverage_id})
        SET c += $properties
        RETURN c
        """
        properties = coverage.model_dump(exclude_none=True)
        params = {"coverage_id": coverage.coverage_id, "properties": properties}

        return self._execute_write(cypher, params, session)

    def create_disease_node(
        self, disease: DiseaseNode, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a Disease node"""
        cypher = """
        MERGE (d:Disease {disease_id: $disease_id})
        SET d += $properties
        RETURN d
        """
        properties = disease.model_dump(exclude_none=True)
        params = {"disease_id": disease.disease_id, "properties": properties}

        return self._execute_write(cypher, params, session)

    def create_condition_node(
        self, condition: ConditionNode, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a Condition node"""
        cypher = """
        MERGE (c:Condition {condition_id: $condition_id})
        SET c += $properties
        RETURN c
        """
        properties = condition.model_dump(exclude_none=True)
        params = {"condition_id": condition.condition_id, "properties": properties}

        return self._execute_write(cypher, params, session)

    def create_clause_node(
        self, clause: ClauseNode, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a Clause node"""
        cypher = """
        MERGE (c:Clause {clause_id: $clause_id})
        SET c += $properties
        RETURN c
        """
        properties = clause.model_dump(exclude_none=True)
        params = {"clause_id": clause.clause_id, "properties": properties}

        return self._execute_write(cypher, params, session)

    # ========================================================================
    # Relationship Creation
    # ========================================================================

    def create_relationship(
        self, relationship: GraphRelationship, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes"""
        cypher = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:{relationship.relation_type}]->(target)
        SET r += $properties
        RETURN r
        """
        # Note: This is a simplified version that assumes nodes have an 'id' property
        # In practice, we need to match by the appropriate ID field for each node type

        params = {
            "source_id": relationship.source_node_id,
            "target_id": relationship.target_node_id,
            "properties": relationship.properties,
        }

        return self._execute_write(cypher, params, session)

    def create_typed_relationship(
        self,
        source_type: NodeType,
        source_id: str,
        target_type: NodeType,
        target_id: str,
        relation_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Create a typed relationship with proper node matching

        Args:
            source_type: Source node type
            source_id: Source node ID
            target_type: Target node type
            target_id: Target node ID
            relation_type: Relationship type
            properties: Relationship properties
            session: Neo4j session (optional)
        """
        # Build ID field names based on node types
        source_id_field = self._get_id_field(source_type)
        target_id_field = self._get_id_field(target_type)

        cypher = f"""
        MATCH (source:{source_type.value} {{{source_id_field}: $source_id}})
        MATCH (target:{target_type.value} {{{target_id_field}: $target_id}})
        MERGE (source)-[r:{relation_type.value}]->(target)
        SET r += $properties
        RETURN r
        """

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties or {},
        }

        return self._execute_write(cypher, params, session)

    # ========================================================================
    # Batch Operations
    # ========================================================================

    def create_batch(self, batch: GraphBatch) -> GraphStats:
        """
        Create a batch of nodes and relationships

        Uses a single transaction for performance.

        Args:
            batch: GraphBatch with nodes and relationships

        Returns:
            GraphStats with creation statistics
        """
        stats = GraphStats()
        start_time = None

        try:
            import time

            start_time = time.time()

            with self.driver.session() as session:
                with session.begin_transaction() as tx:
                    # Create nodes by type
                    for product in batch.products:
                        self.create_product_node(product, tx)
                        stats.nodes_by_type["Product"] = (
                            stats.nodes_by_type.get("Product", 0) + 1
                        )

                    for coverage in batch.coverages:
                        self.create_coverage_node(coverage, tx)
                        stats.nodes_by_type["Coverage"] = (
                            stats.nodes_by_type.get("Coverage", 0) + 1
                        )

                    for disease in batch.diseases:
                        self.create_disease_node(disease, tx)
                        stats.nodes_by_type["Disease"] = (
                            stats.nodes_by_type.get("Disease", 0) + 1
                        )

                    for condition in batch.conditions:
                        self.create_condition_node(condition, tx)
                        stats.nodes_by_type["Condition"] = (
                            stats.nodes_by_type.get("Condition", 0) + 1
                        )

                    for clause in batch.clauses:
                        self.create_clause_node(clause, tx)
                        stats.nodes_by_type["Clause"] = (
                            stats.nodes_by_type.get("Clause", 0) + 1
                        )

                    # Create relationships
                    for relationship in batch.relationships:
                        self.create_relationship(relationship, tx)
                        rel_type = relationship.relation_type.value
                        stats.relationships_by_type[rel_type] = (
                            stats.relationships_by_type.get(rel_type, 0) + 1
                        )

                    tx.commit()

            # Calculate totals
            stats.total_nodes = sum(stats.nodes_by_type.values())
            stats.total_relationships = sum(stats.relationships_by_type.values())

            if start_time:
                stats.construction_time_seconds = time.time() - start_time

            logger.info(
                f"Created {stats.total_nodes} nodes and {stats.total_relationships} relationships"
            )

        except Exception as e:
            error_msg = f"Batch creation failed: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)

        return stats

    # ========================================================================
    # Index Creation
    # ========================================================================

    def create_indexes(self):
        """Create Neo4j indexes for fast queries"""
        indexes = [
            # Primary ID indexes
            "CREATE INDEX product_id_index IF NOT EXISTS FOR (p:Product) ON (p.product_id)",
            "CREATE INDEX coverage_id_index IF NOT EXISTS FOR (c:Coverage) ON (c.coverage_id)",
            "CREATE INDEX disease_id_index IF NOT EXISTS FOR (d:Disease) ON (d.disease_id)",
            "CREATE INDEX condition_id_index IF NOT EXISTS FOR (c:Condition) ON (c.condition_id)",
            "CREATE INDEX clause_id_index IF NOT EXISTS FOR (c:Clause) ON (c.clause_id)",
            # KCD code index for diseases
            "CREATE INDEX disease_kcd_index IF NOT EXISTS FOR (d:Disease) ON (d.kcd_codes)",
            # Standard name index
            "CREATE INDEX disease_standard_name_index IF NOT EXISTS FOR (d:Disease) ON (d.standard_name)",
            # Article number index for clauses
            "CREATE INDEX clause_article_index IF NOT EXISTS FOR (c:Clause) ON (c.article_num)",
            # Vector index for semantic search (if supported)
            # Note: Vector indexes require Neo4j 5.11+
            "CREATE VECTOR INDEX clause_embedding_index IF NOT EXISTS FOR (c:Clause) ON (c.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
        ]

        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"Created index: {index_query[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

    # ========================================================================
    # Query Methods
    # ========================================================================

    def get_node_by_id(
        self, node_type: NodeType, node_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a node by its ID"""
        id_field = self._get_id_field(node_type)
        cypher = f"""
        MATCH (n:{node_type.value} {{{id_field}: $node_id}})
        RETURN n
        """
        result = self._execute_read(cypher, {"node_id": node_id})
        return result[0] if result else None

    def get_relationships(
        self, node_id: str, direction: str = "outgoing"
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a node

        Args:
            node_id: Node ID
            direction: 'outgoing', 'incoming', or 'both'
        """
        if direction == "outgoing":
            cypher = "MATCH (n {id: $node_id})-[r]->(m) RETURN r, m"
        elif direction == "incoming":
            cypher = "MATCH (n {id: $node_id})<-[r]-(m) RETURN r, m"
        else:
            cypher = "MATCH (n {id: $node_id})-[r]-(m) RETURN r, m"

        return self._execute_read(cypher, {"node_id": node_id})

    def vector_search(
        self, embedding: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector embeddings

        Args:
            embedding: Query embedding vector
            limit: Maximum results to return

        Returns:
            List of similar clause nodes with similarity scores
        """
        cypher = """
        CALL db.index.vector.queryNodes('clause_embedding_index', $limit, $embedding)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """
        return self._execute_read(cypher, {"embedding": embedding, "limit": limit})

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def clear_database(self):
        """Clear all nodes and relationships (USE WITH CAUTION!)"""
        cypher = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(cypher)
        logger.warning("Database cleared!")

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        cypher = """
        MATCH (n)
        WITH labels(n) as labels
        UNWIND labels as label
        RETURN label, count(*) as count
        """
        node_counts = self._execute_read(cypher, {})

        cypher = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        """
        rel_counts = self._execute_read(cypher, {})

        return {"nodes": node_counts, "relationships": rel_counts}

    def _execute_write(
        self, cypher: str, params: Dict[str, Any], session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Execute a write query"""
        if session:
            # Use provided session/transaction
            result = session.run(cypher, params)
            return [record.data() for record in result]
        else:
            # Create new session
            with self.driver.session() as new_session:
                result = new_session.run(cypher, params)
                return [record.data() for record in result]

    def _execute_read(
        self, cypher: str, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a read query"""
        with self.driver.session() as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def _get_id_field(self, node_type: NodeType) -> str:
        """Get the ID field name for a node type"""
        mapping = {
            NodeType.PRODUCT: "product_id",
            NodeType.COVERAGE: "coverage_id",
            NodeType.DISEASE: "disease_id",
            NodeType.CONDITION: "condition_id",
            NodeType.CLAUSE: "clause_id",
        }
        return mapping.get(node_type, "id")
