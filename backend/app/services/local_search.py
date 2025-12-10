"""
Local Search Service

Performs searches within insurance policy documents using Neo4j graph database.

Search Types:
1. Keyword Search - Find articles/paragraphs containing keywords
2. Amount Search - Find clauses with specific amounts
3. Period Search - Find clauses with specific periods
4. Disease Search - Find coverage for specific diseases (KCD codes)
5. Semantic Search - Vector similarity search using embeddings
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from neo4j import GraphDatabase
from app.core.config import settings
from app.services.query_parser import ParsedQuery, QueryIntent
from loguru import logger


class SearchType(str, Enum):
    """Type of search"""
    KEYWORD = "keyword"
    AMOUNT = "amount"
    PERIOD = "period"
    DISEASE = "disease"
    SEMANTIC = "semantic"


@dataclass
class SearchResult:
    """A single search result"""
    node_type: str  # "Article", "Paragraph", "Subclause"
    node_id: str
    text: str
    relevance_score: float
    metadata: Dict[str, Any]

    # Context
    article_num: Optional[str] = None
    article_title: Optional[str] = None
    paragraph_num: Optional[str] = None


@dataclass
class SearchResults:
    """Collection of search results"""
    results: List[SearchResult]
    total_results: int
    search_type: SearchType
    query: str

    def top_k(self, k: int) -> List[SearchResult]:
        """Get top K results"""
        return sorted(self.results, key=lambda x: x.relevance_score, reverse=True)[:k]


class LocalSearch:
    """
    Local search engine for insurance policy documents.

    Uses Neo4j graph database to search within a single policy or across multiple policies.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize local search.

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
        )

        logger.info(f"LocalSearch initialized with Neo4j at {self.uri}")

    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def search(self, parsed_query: ParsedQuery, limit: int = 20) -> SearchResults:
        """
        Execute search based on parsed query.

        Args:
            parsed_query: Parsed query with intent and entities
            limit: Maximum number of results

        Returns:
            SearchResults
        """
        if parsed_query.intent == QueryIntent.AMOUNT_FILTER:
            return self.search_by_amount(
                min_amount=parsed_query.min_amount,
                max_amount=parsed_query.max_amount,
                limit=limit,
            )
        elif parsed_query.intent == QueryIntent.PERIOD_CHECK:
            periods = [e for e in parsed_query.entities if e.entity_type == "period"]
            if periods:
                return self.search_by_period(
                    period_days=periods[0].normalized_value,
                    limit=limit,
                )
        elif parsed_query.intent == QueryIntent.COVERAGE_CHECK:
            diseases = [e for e in parsed_query.entities if e.entity_type == "disease"]
            if diseases:
                return self.search_by_disease(
                    disease_name=diseases[0].value,
                    limit=limit,
                )

        # Default: keyword search
        return self.search_by_keywords(
            keywords=parsed_query.keywords,
            limit=limit,
        )

    def search_by_keywords(self, keywords: List[str], limit: int = 20) -> SearchResults:
        """
        Search by keywords in article/paragraph/subclause text.

        Args:
            keywords: List of keywords to search
            limit: Maximum results

        Returns:
            SearchResults
        """
        if not keywords:
            return SearchResults([], 0, SearchType.KEYWORD, "")

        # Build regex pattern (OR of all keywords)
        pattern = "|".join(keywords)

        # Search in actual node types: CoverageItem, Exclusion, Article, BenefitAmount, etc.
        # Search in both 'text' and 'source_text' and 'description' properties
        query = """
        MATCH (n)
        WHERE (n:Article OR n:Paragraph OR n:Subclause OR n:CoverageItem OR n:Exclusion
               OR n:BenefitAmount OR n:PaymentCondition OR n:Period OR n:Term OR n:Rider)
          AND (n.text =~ $pattern OR n.source_text =~ $pattern OR n.description =~ $pattern)
        RETURN DISTINCT
            labels(n)[0] AS node_type,
            COALESCE(n.id, n.entity_id) AS node_id,
            COALESCE(n.text, n.source_text, n.description, '') AS text,
            COALESCE(n.article_num, '') AS article_num,
            COALESCE(n.title, n.label, '') AS article_title,
            COALESCE(n.paragraph_num, '') AS paragraph_num,
            COALESCE(n.insurer, '') AS insurer,
            COALESCE(n.product_type, '') AS product_type
        LIMIT $limit
        """

        results = []
        with self.driver.session() as session:
            records = session.run(
                query,
                pattern=f"(?i).*({pattern}).*",
                limit=limit,
            )

            for record in records:
                # Build metadata
                metadata = {}
                if record["insurer"]:
                    metadata["insurer"] = record["insurer"]
                if record["product_type"]:
                    metadata["product_type"] = record["product_type"]

                result = SearchResult(
                    node_type=record["node_type"],
                    node_id=record["node_id"],
                    text=record["text"],
                    relevance_score=1.0,  # Simple: all matches are equal
                    metadata=metadata,
                    article_num=record["article_num"] if record["article_num"] else None,
                    article_title=record["article_title"] if record["article_title"] else None,
                    paragraph_num=record["paragraph_num"] if record["paragraph_num"] else None,
                )
                results.append(result)

        return SearchResults(
            results=results,
            total_results=len(results),
            search_type=SearchType.KEYWORD,
            query=" ".join(keywords),
        )

    def search_by_amount(
        self,
        min_amount: Optional[int] = None,
        max_amount: Optional[int] = None,
        limit: int = 20,
    ) -> SearchResults:
        """
        Search by amount range.

        Args:
            min_amount: Minimum amount (inclusive)
            max_amount: Maximum amount (inclusive)
            limit: Maximum results

        Returns:
            SearchResults
        """
        query = """
        MATCH (amt:Amount)
        WHERE ($min_amount IS NULL OR amt.value >= $min_amount)
          AND ($max_amount IS NULL OR amt.value <= $max_amount)
        MATCH (n)-[:MENTIONS_AMOUNT]->(amt)
        OPTIONAL MATCH (n)<-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*0..2]-(a:Article)
        RETURN DISTINCT
            labels(n)[0] AS node_type,
            n.id AS node_id,
            n.text AS text,
            amt.value AS amount,
            COALESCE(n.article_num, a.article_num) AS article_num,
            COALESCE(n.title, a.title, '') AS article_title
        LIMIT $limit
        """

        results = []
        with self.driver.session() as session:
            records = session.run(
                query,
                min_amount=min_amount,
                max_amount=max_amount,
                limit=limit,
            )

            for record in records:
                result = SearchResult(
                    node_type=record["node_type"],
                    node_id=record["node_id"],
                    text=record["text"],
                    relevance_score=1.0,
                    metadata={"amount": record["amount"]},
                    article_num=record["article_num"],
                    article_title=record["article_title"],
                )
                results.append(result)

        query_str = f"{min_amount or 0:,}원 ~ {max_amount or '무제한'}"
        return SearchResults(
            results=results,
            total_results=len(results),
            search_type=SearchType.AMOUNT,
            query=query_str,
        )

    def search_by_period(self, period_days: int, limit: int = 20) -> SearchResults:
        """
        Search by period (in days).

        Args:
            period_days: Period in days
            limit: Maximum results

        Returns:
            SearchResults
        """
        query = """
        MATCH (per:Period {days: $period_days})
        MATCH (n)-[:MENTIONS_PERIOD]->(per)
        OPTIONAL MATCH (n)<-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*0..2]-(a:Article)
        RETURN DISTINCT
            labels(n)[0] AS node_type,
            n.id AS node_id,
            n.text AS text,
            per.days AS days,
            COALESCE(n.article_num, a.article_num) AS article_num,
            COALESCE(n.title, a.title, '') AS article_title
        LIMIT $limit
        """

        results = []
        with self.driver.session() as session:
            records = session.run(query, period_days=period_days, limit=limit)

            for record in records:
                result = SearchResult(
                    node_type=record["node_type"],
                    node_id=record["node_id"],
                    text=record["text"],
                    relevance_score=1.0,
                    metadata={"days": record["days"]},
                    article_num=record["article_num"],
                    article_title=record["article_title"],
                )
                results.append(result)

        return SearchResults(
            results=results,
            total_results=len(results),
            search_type=SearchType.PERIOD,
            query=f"{period_days}일",
        )

    def search_by_disease(self, disease_name: str, limit: int = 20) -> SearchResults:
        """
        Search by disease name (fuzzy match in text).

        Args:
            disease_name: Disease name (e.g., "암", "심근경색")
            limit: Maximum results

        Returns:
            SearchResults
        """
        # Search in text content
        query = """
        MATCH (n)
        WHERE (n:Article OR n:Paragraph OR n:Subclause)
          AND n.text CONTAINS $disease_name
        OPTIONAL MATCH (n)<-[:HAS_PARAGRAPH|HAS_SUBCLAUSE*0..2]-(a:Article)
        RETURN DISTINCT
            labels(n)[0] AS node_type,
            n.id AS node_id,
            n.text AS text,
            COALESCE(n.article_num, a.article_num) AS article_num,
            COALESCE(n.title, a.title, '') AS article_title
        LIMIT $limit
        """

        results = []
        with self.driver.session() as session:
            records = session.run(query, disease_name=disease_name, limit=limit)

            for record in records:
                result = SearchResult(
                    node_type=record["node_type"],
                    node_id=record["node_id"],
                    text=record["text"],
                    relevance_score=1.0,
                    metadata={"disease": disease_name},
                    article_num=record["article_num"],
                    article_title=record["article_title"],
                )
                results.append(result)

        return SearchResults(
            results=results,
            total_results=len(results),
            search_type=SearchType.DISEASE,
            query=disease_name,
        )


# Singleton instance
_local_search: Optional[LocalSearch] = None


def get_local_search() -> LocalSearch:
    """Get or create singleton local search instance"""
    global _local_search
    if _local_search is None:
        _local_search = LocalSearch()
    return _local_search


if __name__ == "__main__":
    # Test local search
    from app.services.query_parser import get_query_parser

    print("=" * 70)
    print("🧪 Local Search Test")
    print("=" * 70)

    # First, create test data in Neo4j
    from uuid import uuid4
    from app.services.legal_structure_parser import get_legal_parser
    from app.services.critical_data_extractor import get_critical_extractor
    from app.services.embedding_generator import get_embedding_generator
    from app.services.neo4j_graph_builder import get_graph_builder

    sample_text = """
제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.
"""

    print("\n📄 Creating test policy in Neo4j...")

    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    emb_generator = get_embedding_generator()
    embeddings = emb_generator.generate_for_articles(parsed.articles)

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

    print(f"✅ Created test policy with {stats.total_nodes} nodes")

    # Test searches
    query_parser = get_query_parser()
    search_engine = get_local_search()

    test_queries = [
        "암보험 보장",
        "1억원 이상",
        "90일",
    ]

    for q in test_queries:
        print(f"\n🔍 Query: {q}")
        parsed_q = query_parser.parse(q)
        results = search_engine.search(parsed_q, limit=5)

        print(f"   Found {results.total_results} results (type: {results.search_type.value})")
        for i, result in enumerate(results.results[:3], 1):
            print(f"   {i}. [{result.node_type}] {result.text[:80]}...")
            if result.article_title:
                print(f"      제{result.article_num}조 [{result.article_title}]")

    # Cleanup
    builder.clear_policy(policy_id)
    builder.close()
    search_engine.close()

    print("\n" + "=" * 70)
    print("✅ Local search test complete!")
    print("=" * 70)
