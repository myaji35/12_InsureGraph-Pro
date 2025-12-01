"""
Graph Traversal Service

Neo4j 그래프를 탐색하여 다중 홉 추론을 수행합니다.

Traversal Types:
1. Hierarchical - 계층 구조 탐색 (Article → Paragraph → Subclause)
2. Cross-reference - 교차 참조 탐색 (조항 간 연결)
3. Entity-based - 엔티티 기반 탐색 (금액, 질병 등)
4. Multi-hop - 다중 홉 추론 (A → B → C)
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set
from enum import Enum

from neo4j import GraphDatabase
from app.core.config import settings
from loguru import logger


class TraversalType(str, Enum):
    """Type of graph traversal"""
    HIERARCHICAL = "hierarchical"  # 계층 구조
    ENTITY_BASED = "entity_based"  # 엔티티 기반
    MULTI_HOP = "multi_hop"  # 다중 홉
    PATH_FINDING = "path_finding"  # 경로 탐색


@dataclass
class GraphNode:
    """A node in the traversal path"""
    node_id: str
    node_type: str  # "Article", "Paragraph", etc.
    text: str
    properties: Dict[str, Any]


@dataclass
class GraphPath:
    """A path through the graph"""
    nodes: List[GraphNode]
    relationships: List[str]
    path_length: int
    relevance_score: float

    def __str__(self):
        return " → ".join([f"{n.node_type}({n.node_id})" for n in self.nodes])


@dataclass
class TraversalResult:
    """Result of graph traversal"""
    query: str
    paths: List[GraphPath]
    total_paths: int
    traversal_type: TraversalType
    metadata: Dict[str, Any]


class GraphTraversal:
    """
    Graph traversal service for multi-hop reasoning.

    Features:
    - Hierarchical traversal (follow structure)
    - Entity-based traversal (find related entities)
    - Multi-hop reasoning (A → B → C)
    - Path finding (shortest/best path)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        max_depth: int = 5,
    ):
        """
        Initialize graph traversal.

        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
            max_depth: Maximum traversal depth
        """
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.max_depth = max_depth

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

        logger.info(f"GraphTraversal initialized with max_depth={max_depth}")

    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def traverse_hierarchical(
        self,
        start_node_id: str,
        direction: str = "down",
        max_depth: Optional[int] = None,
    ) -> TraversalResult:
        """
        Traverse hierarchical structure.

        Args:
            start_node_id: Starting node ID
            direction: "up" (to parent) or "down" (to children)
            max_depth: Maximum depth (default: self.max_depth)

        Returns:
            TraversalResult with paths
        """
        max_depth = max_depth or self.max_depth

        if direction == "down":
            # Article → Paragraph → Subclause
            query = """
            MATCH path = (start)-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*1..{max_depth}]->(end)
            WHERE start.id = $start_id
            RETURN path
            LIMIT 100
            """.replace("{max_depth}", str(max_depth))
        else:
            # Subclause → Paragraph → Article
            query = """
            MATCH path = (start)<-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*1..{max_depth}]-(end)
            WHERE start.id = $start_id
            RETURN path
            LIMIT 100
            """.replace("{max_depth}", str(max_depth))

        paths = []
        with self.driver.session() as session:
            result = session.run(query, start_id=start_node_id)

            for record in result:
                path_obj = record["path"]
                graph_path = self._convert_path(path_obj)
                paths.append(graph_path)

        return TraversalResult(
            query=f"Hierarchical traversal from {start_node_id} ({direction})",
            paths=paths,
            total_paths=len(paths),
            traversal_type=TraversalType.HIERARCHICAL,
            metadata={"direction": direction, "max_depth": max_depth},
        )

    def traverse_by_entity(
        self,
        entity_type: str,
        entity_value: Any,
        max_hops: int = 2,
    ) -> TraversalResult:
        """
        Traverse by entity (e.g., find all articles mentioning a specific amount).

        Args:
            entity_type: "Amount", "Period", "KCDCode"
            entity_value: Entity value to match
            max_hops: Maximum hops from entity

        Returns:
            TraversalResult with paths
        """
        # Find entity node
        if entity_type == "Amount":
            entity_query = f"MATCH (e:Amount {{value: $value}})"
        elif entity_type == "Period":
            entity_query = f"MATCH (e:Period {{days: $value}})"
        elif entity_type == "KCDCode":
            entity_query = f"MATCH (e:KCDCode {{code: $value}})"
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Traverse from entity to articles
        query = f"""
        {entity_query}
        MATCH path = (e)<-[*1..{max_hops}]-(article:Article)
        RETURN path
        LIMIT 50
        """

        paths = []
        with self.driver.session() as session:
            result = session.run(query, value=entity_value)

            for record in result:
                path_obj = record["path"]
                graph_path = self._convert_path(path_obj)
                paths.append(graph_path)

        return TraversalResult(
            query=f"Entity traversal: {entity_type}={entity_value}",
            paths=paths,
            total_paths=len(paths),
            traversal_type=TraversalType.ENTITY_BASED,
            metadata={"entity_type": entity_type, "entity_value": entity_value},
        )

    def find_related_articles(
        self,
        article_id: str,
        relation_types: Optional[List[str]] = None,
        max_hops: int = 3,
    ) -> TraversalResult:
        """
        Find articles related to a given article.

        Args:
            article_id: Starting article ID
            relation_types: Types of relationships to follow (optional)
            max_hops: Maximum hops

        Returns:
            TraversalResult with related articles
        """
        # Find related articles through shared entities
        query = """
        MATCH (start:Article {id: $article_id})
        MATCH path = (start)-[*1..{max_hops}]-(related:Article)
        WHERE start <> related
        RETURN DISTINCT path
        LIMIT 50
        """.replace("{max_hops}", str(max_hops))

        paths = []
        with self.driver.session() as session:
            result = session.run(query, article_id=article_id)

            for record in result:
                path_obj = record["path"]
                graph_path = self._convert_path(path_obj)
                paths.append(graph_path)

        return TraversalResult(
            query=f"Related articles from {article_id}",
            paths=paths,
            total_paths=len(paths),
            traversal_type=TraversalType.MULTI_HOP,
            metadata={"start_article": article_id, "max_hops": max_hops},
        )

    def find_shortest_path(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: Optional[int] = None,
    ) -> Optional[GraphPath]:
        """
        Find shortest path between two nodes.

        Args:
            start_node_id: Start node ID
            end_node_id: End node ID
            max_depth: Maximum depth

        Returns:
            GraphPath or None if no path found
        """
        max_depth = max_depth or self.max_depth

        query = """
        MATCH path = shortestPath(
            (start {id: $start_id})-[*..{max_depth}]-(end {id: $end_id})
        )
        RETURN path
        """.replace("{max_depth}", str(max_depth))

        with self.driver.session() as session:
            result = session.run(query, start_id=start_node_id, end_id=end_node_id)

            record = result.single()
            if record:
                path_obj = record["path"]
                return self._convert_path(path_obj)

        return None

    def _convert_path(self, neo4j_path) -> GraphPath:
        """Convert Neo4j path object to GraphPath"""
        nodes = []
        relationships = []

        # Extract nodes
        for node in neo4j_path.nodes:
            labels = list(node.labels)
            node_type = labels[0] if labels else "Unknown"

            graph_node = GraphNode(
                node_id=node.get("id", ""),
                node_type=node_type,
                text=node.get("text", node.get("name", "")),
                properties=dict(node),
            )
            nodes.append(graph_node)

        # Extract relationships
        for rel in neo4j_path.relationships:
            relationships.append(rel.type)

        # Calculate relevance (simple: shorter is better)
        relevance_score = 1.0 / (len(nodes) + 1)

        return GraphPath(
            nodes=nodes,
            relationships=relationships,
            path_length=len(nodes),
            relevance_score=relevance_score,
        )

    def get_node_context(self, node_id: str, context_depth: int = 1) -> Dict[str, Any]:
        """
        Get full context for a node (including parent and children).

        Args:
            node_id: Node ID
            context_depth: Depth of context to retrieve

        Returns:
            Dictionary with node context
        """
        query = """
        MATCH (node {id: $node_id})
        OPTIONAL MATCH (node)<-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*1..{depth}]-(parent)
        OPTIONAL MATCH (node)-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*1..{depth}]->(child)
        RETURN node, collect(DISTINCT parent) AS parents, collect(DISTINCT child) AS children
        """.replace("{depth}", str(context_depth))

        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()

            if not record:
                return {}

            node = record["node"]
            parents = record["parents"]
            children = record["children"]

            return {
                "node": dict(node),
                "parents": [dict(p) for p in parents if p],
                "children": [dict(c) for c in children if c],
            }


# Singleton instance
_graph_traversal: Optional[GraphTraversal] = None


def get_graph_traversal() -> GraphTraversal:
    """Get or create singleton graph traversal instance"""
    global _graph_traversal
    if _graph_traversal is None:
        _graph_traversal = GraphTraversal()
    return _graph_traversal


if __name__ == "__main__":
    # Test graph traversal
    from uuid import uuid4
    from app.services.legal_structure_parser import get_legal_parser
    from app.services.critical_data_extractor import get_critical_extractor
    from app.services.embedding_generator import get_embedding_generator
    from app.services.neo4j_graph_builder import get_graph_builder

    sample_text = """제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.

제11조 [보험료 납입]
① 보험료는 매월 10만원씩 납입해야 합니다.
"""

    print("=" * 70)
    print("🧪 Graph Traversal Test")
    print("=" * 70)

    # Create test graph
    print("\n📊 Creating test graph...")
    policy_id = uuid4()

    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    emb_gen = get_embedding_generator()
    embeddings = emb_gen.generate_for_articles(parsed.articles)

    builder = get_graph_builder()
    builder.create_constraints()
    stats = builder.build_graph(
        policy_id=policy_id,
        policy_name="테스트 보험",
        insurer="테스트사",
        articles=parsed.articles,
        extracted_data=extracted,
        embeddings=embeddings,
    )

    print(f"  ✓ Created: {stats.total_nodes} nodes")

    # Test traversal
    print("\n🔍 Testing traversal...")
    traversal = get_graph_traversal()

    # Get first article ID
    article_id = f"{policy_id}_article_제10조"

    # 1. Hierarchical traversal
    print(f"\n1. Hierarchical traversal from {article_id}:")
    result = traversal.traverse_hierarchical(article_id, direction="down", max_depth=2)
    print(f"   Found {result.total_paths} paths")
    for i, path in enumerate(result.paths[:3], 1):
        print(f"   Path {i}: {path} (length={path.path_length})")

    # 2. Get node context
    print(f"\n2. Node context for {article_id}:")
    context = traversal.get_node_context(article_id, context_depth=1)
    if context:
        print(f"   Node: {context['node'].get('article_num', 'N/A')}")
        print(f"   Children: {len(context['children'])}")

    traversal.close()

    # Cleanup
    builder.clear_policy(policy_id)
    builder.close()

    print("\n" + "=" * 70)
    print("✅ Graph traversal test complete!")
    print("=" * 70)
