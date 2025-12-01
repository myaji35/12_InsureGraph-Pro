"""
Neo4j Graph Builder Service

Constructs a knowledge graph from parsed insurance policy documents.

Graph Schema:
- Policy (보험 상품)
  - name, insurer, policy_type
- Article (조)
  - article_num, title, text
- Paragraph (항)
  - paragraph_num, text
- Subclause (하위 조항)
  - subclause_num, text
- Amount (금액)
  - value, original_text
- Period (기간)
  - days, original_text
- KCDCode (질병 코드)
  - code, is_range

Relationships:
- (:Policy)-[:HAS_ARTICLE]->(:Article)
- (:Article)-[:HAS_PARAGRAPH]->(:Paragraph)
- (:Paragraph)-[:HAS_SUBCLAUSE]->(:Subclause)
- (:Article|Paragraph|Subclause)-[:MENTIONS_AMOUNT]->(:Amount)
- (:Article|Paragraph|Subclause)-[:MENTIONS_PERIOD]->(:Period)
- (:Article|Paragraph|Subclause)-[:MENTIONS_KCD]->(:KCDCode)
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from neo4j import GraphDatabase
from dataclasses import dataclass

from app.core.config import settings
from app.services.legal_structure_parser import Article, Paragraph, Subclause
from app.services.critical_data_extractor import ExtractionResult
from app.services.embedding_generator import EmbeddingResult
from loguru import logger


@dataclass
class GraphStats:
    """Statistics about the constructed graph"""
    policy_nodes: int = 0
    article_nodes: int = 0
    paragraph_nodes: int = 0
    subclause_nodes: int = 0
    amount_nodes: int = 0
    period_nodes: int = 0
    kcd_nodes: int = 0
    relationships: int = 0

    @property
    def total_nodes(self) -> int:
        return (
            self.policy_nodes
            + self.article_nodes
            + self.paragraph_nodes
            + self.subclause_nodes
            + self.amount_nodes
            + self.period_nodes
            + self.kcd_nodes
        )


class Neo4jGraphBuilder:
    """
    Builds knowledge graph in Neo4j from parsed insurance policies.

    Features:
    - Hierarchical structure (Policy -> Article -> Paragraph -> Subclause)
    - Entity nodes (Amount, Period, KCDCode)
    - Vector embeddings for semantic search
    - Relationship tracking
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j graph builder.

        Args:
            uri: Neo4j connection URI (defaults to settings)
            user: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
        """
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
        )

        # Verify connectivity
        self.driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {self.uri}")

    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_constraints(self):
        """Create uniqueness constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paragraph) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subclause) REQUIRE s.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (a:Article) ON (a.article_num)",
            "CREATE INDEX IF NOT EXISTS FOR (amt:Amount) ON (amt.value)",
            "CREATE INDEX IF NOT EXISTS FOR (kcd:KCDCode) ON (kcd.code)",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                session.run(constraint)
                logger.debug(f"Created constraint/index: {constraint[:50]}...")

    def build_graph(
        self,
        policy_id: UUID,
        policy_name: str,
        insurer: str,
        articles: List[Article],
        extracted_data: ExtractionResult,
        embeddings: Optional[EmbeddingResult] = None,
    ) -> GraphStats:
        """
        Build complete knowledge graph for a policy.

        Args:
            policy_id: Unique policy identifier
            policy_name: Policy name
            insurer: Insurance company name
            articles: List of parsed articles
            extracted_data: Extracted amounts, periods, KCD codes
            embeddings: Optional embeddings for semantic search

        Returns:
            GraphStats with node and relationship counts
        """
        stats = GraphStats()

        with self.driver.session() as session:
            # 1. Create Policy node
            stats.policy_nodes += self._create_policy_node(
                session, policy_id, policy_name, insurer
            )

            # 2. Create Article nodes and hierarchy
            for article in articles:
                article_id = f"{policy_id}_article_{article.article_num}"

                # Get embedding if available
                article_embedding = None
                if embeddings:
                    emb = embeddings.get_by_source_id(f"article_{article.article_num}")
                    if emb:
                        article_embedding = emb.embedding

                stats.article_nodes += self._create_article_node(
                    session, article_id, policy_id, article, article_embedding
                )

                # 3. Create Paragraph nodes
                for para in article.paragraphs:
                    para_id = f"{article_id}_para_{para.paragraph_num}"

                    # Get embedding
                    para_embedding = None
                    if embeddings:
                        emb = embeddings.get_by_source_id(
                            f"paragraph_{article.article_num}_{para.paragraph_num}"
                        )
                        if emb:
                            para_embedding = emb.embedding

                    stats.paragraph_nodes += self._create_paragraph_node(
                        session, para_id, article_id, para, para_embedding
                    )

                    # 4. Create Subclause nodes
                    for sub in para.subclauses:
                        sub_id = f"{para_id}_sub_{sub.subclause_num}"

                        # Get embedding
                        sub_embedding = None
                        if embeddings:
                            emb = embeddings.get_by_source_id(
                                f"subclause_{article.article_num}_{para.paragraph_num}_{sub.subclause_num}"
                            )
                            if emb:
                                sub_embedding = emb.embedding

                        stats.subclause_nodes += self._create_subclause_node(
                            session, sub_id, para_id, sub, sub_embedding
                        )

            # 5. Create entity nodes (Amount, Period, KCDCode)
            stats.amount_nodes, rel_count = self._create_amount_nodes(
                session, str(policy_id), extracted_data.amounts
            )
            stats.relationships += rel_count

            stats.period_nodes, rel_count = self._create_period_nodes(
                session, str(policy_id), extracted_data.periods
            )
            stats.relationships += rel_count

            stats.kcd_nodes, rel_count = self._create_kcd_nodes(
                session, str(policy_id), extracted_data.kcd_codes
            )
            stats.relationships += rel_count

        logger.info(
            f"Graph built: {stats.total_nodes} nodes, {stats.relationships} relationships"
        )
        return stats

    def _create_policy_node(
        self, session, policy_id: UUID, policy_name: str, insurer: str
    ) -> int:
        """Create Policy node"""
        query = """
        MERGE (p:Policy {id: $policy_id})
        SET p.name = $policy_name,
            p.insurer = $insurer,
            p.created_at = datetime()
        RETURN p
        """
        session.run(query, policy_id=str(policy_id), policy_name=policy_name, insurer=insurer)
        return 1

    def _create_article_node(
        self, session, article_id: str, policy_id: UUID, article: Article, embedding: Optional[List[float]]
    ) -> int:
        """Create Article node and link to Policy"""
        query = """
        MATCH (p:Policy {id: $policy_id})
        MERGE (a:Article {id: $article_id})
        SET a.article_num = $article_num,
            a.title = $title,
            a.text = $text,
            a.embedding = $embedding
        MERGE (p)-[:HAS_ARTICLE]->(a)
        RETURN a
        """
        session.run(
            query,
            policy_id=str(policy_id),
            article_id=article_id,
            article_num=article.article_num,
            title=article.title or "",
            text=article.text or "",
            embedding=embedding,
        )
        return 1

    def _create_paragraph_node(
        self, session, para_id: str, article_id: str, paragraph: Paragraph, embedding: Optional[List[float]]
    ) -> int:
        """Create Paragraph node and link to Article"""
        query = """
        MATCH (a:Article {id: $article_id})
        MERGE (p:Paragraph {id: $para_id})
        SET p.paragraph_num = $paragraph_num,
            p.text = $text,
            p.embedding = $embedding
        MERGE (a)-[:HAS_PARAGRAPH]->(p)
        RETURN p
        """
        session.run(
            query,
            article_id=article_id,
            para_id=para_id,
            paragraph_num=paragraph.paragraph_num,
            text=paragraph.text,
            embedding=embedding,
        )
        return 1

    def _create_subclause_node(
        self, session, sub_id: str, para_id: str, subclause: Subclause, embedding: Optional[List[float]]
    ) -> int:
        """Create Subclause node and link to Paragraph"""
        query = """
        MATCH (p:Paragraph {id: $para_id})
        MERGE (s:Subclause {id: $sub_id})
        SET s.subclause_num = $subclause_num,
            s.text = $text,
            s.embedding = $embedding
        MERGE (p)-[:HAS_SUBCLAUSE]->(s)
        RETURN s
        """
        session.run(
            query,
            para_id=para_id,
            sub_id=sub_id,
            subclause_num=subclause.subclause_num,
            text=subclause.text,
            embedding=embedding,
        )
        return 1

    def _create_amount_nodes(self, session, policy_id: str, amounts: List) -> tuple[int, int]:
        """Create Amount nodes and link to context"""
        if not amounts:
            return 0, 0

        node_count = 0
        rel_count = 0

        for amount in amounts:
            query = """
            MERGE (amt:Amount {value: $value, policy_id: $policy_id})
            SET amt.original_text = $original_text,
                amt.start_pos = $start_pos,
                amt.end_pos = $end_pos
            RETURN amt
            """
            session.run(
                query,
                value=amount.normalized_value,
                policy_id=policy_id,
                original_text=amount.original_text,
                start_pos=amount.start_pos,
                end_pos=amount.end_pos,
            )
            node_count += 1

        return node_count, rel_count

    def _create_period_nodes(self, session, policy_id: str, periods: List) -> tuple[int, int]:
        """Create Period nodes"""
        if not periods:
            return 0, 0

        node_count = 0
        rel_count = 0

        for period in periods:
            query = """
            MERGE (per:Period {days: $days, policy_id: $policy_id})
            SET per.original_text = $original_text,
                per.start_pos = $start_pos,
                per.end_pos = $end_pos
            RETURN per
            """
            session.run(
                query,
                days=period.normalized_days,
                policy_id=policy_id,
                original_text=period.original_text,
                start_pos=period.start_pos,
                end_pos=period.end_pos,
            )
            node_count += 1

        return node_count, rel_count

    def _create_kcd_nodes(self, session, policy_id: str, kcd_codes: List) -> tuple[int, int]:
        """Create KCDCode nodes"""
        if not kcd_codes:
            return 0, 0

        node_count = 0
        rel_count = 0

        for kcd in kcd_codes:
            query = """
            MERGE (k:KCDCode {code: $code, policy_id: $policy_id})
            SET k.is_range = $is_range,
                k.start_pos = $start_pos,
                k.end_pos = $end_pos
            RETURN k
            """
            session.run(
                query,
                code=kcd.code,
                policy_id=policy_id,
                is_range=kcd.is_range,
                start_pos=kcd.start_pos,
                end_pos=kcd.end_pos,
            )
            node_count += 1

        return node_count, rel_count

    def clear_policy(self, policy_id: UUID):
        """Delete all nodes related to a policy"""
        query = """
        MATCH (p:Policy {id: $policy_id})
        OPTIONAL MATCH (p)-[*]-(n)
        DETACH DELETE p, n
        """
        with self.driver.session() as session:
            result = session.run(query, policy_id=str(policy_id))
            logger.info(f"Cleared policy {policy_id} from graph")


# Singleton instance
_graph_builder: Optional[Neo4jGraphBuilder] = None


def get_graph_builder() -> Neo4jGraphBuilder:
    """Get or create singleton graph builder instance"""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = Neo4jGraphBuilder()
    return _graph_builder


if __name__ == "__main__":
    # Test graph construction
    from uuid import uuid4
    from app.services.legal_structure_parser import get_legal_parser
    from app.services.critical_data_extractor import get_critical_extractor
    from app.services.embedding_generator import get_embedding_generator

    sample_text = """
제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.
"""

    print("=" * 70)
    print("🧪 Neo4j Graph Builder Test")
    print("=" * 70)

    # Parse
    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    # Extract data
    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    # Generate embeddings
    emb_generator = get_embedding_generator()
    embeddings = emb_generator.generate_for_articles(parsed.articles)

    print(f"\n📄 Parsed: {parsed.total_articles} articles")
    print(f"💰 Extracted: {len(extracted.amounts)} amounts, {len(extracted.periods)} periods, {len(extracted.kcd_codes)} KCD codes")
    print(f"🧮 Embeddings: {embeddings.total_embeddings}")

    # Build graph
    builder = get_graph_builder()
    builder.create_constraints()

    policy_id = uuid4()
    stats = builder.build_graph(
        policy_id=policy_id,
        policy_name="테스트 암보험",
        insurer="테스트 보험사",
        articles=parsed.articles,
        extracted_data=extracted,
        embeddings=embeddings,
    )

    print(f"\n✅ Graph constructed!")
    print(f"   Policy nodes: {stats.policy_nodes}")
    print(f"   Article nodes: {stats.article_nodes}")
    print(f"   Paragraph nodes: {stats.paragraph_nodes}")
    print(f"   Subclause nodes: {stats.subclause_nodes}")
    print(f"   Amount nodes: {stats.amount_nodes}")
    print(f"   Period nodes: {stats.period_nodes}")
    print(f"   KCD nodes: {stats.kcd_nodes}")
    print(f"   Total: {stats.total_nodes} nodes, {stats.relationships} relationships")

    # Cleanup
    builder.clear_policy(policy_id)
    builder.close()

    print("\n" + "=" * 70)
    print("✅ Neo4j graph test complete!")
    print("=" * 70)
