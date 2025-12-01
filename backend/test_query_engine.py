"""
Integration Test: Complete Query Engine

Tests the full GraphRAG query pipeline:
1. Query Parsing
2. Local Search (Neo4j)
3. Graph Traversal
4. LLM Reasoning
"""
import asyncio
from uuid import uuid4
from app.services.query_parser import get_query_parser
from app.services.local_search import get_local_search
from app.services.graph_traversal import get_graph_traversal
from app.services.llm_reasoning import get_llm_reasoning, LLMProvider

# Setup test data
from app.services.legal_structure_parser import get_legal_parser
from app.services.critical_data_extractor import get_critical_extractor
from app.services.embedding_generator import get_embedding_generator
from app.services.entity_linker import get_entity_linker
from app.services.neo4j_graph_builder import get_graph_builder


def setup_test_policy():
    """Create a test policy in Neo4j"""
    sample_text = """제10조 [암보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원
3. 유사암(D00-D09): 500만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.

제11조 [보험료 납입]
① 보험료는 매월 10만원씩 납입해야 합니다.

제12조 [심근경색 진단 시]
① 심근경색(I21)으로 진단 확정 시 3천만원을 지급합니다.
"""

    policy_id = uuid4()

    # Parse
    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    # Extract
    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    # Generate embeddings
    emb_gen = get_embedding_generator()
    embeddings = emb_gen.generate_for_articles(parsed.articles)

    # Link entities
    linker = get_entity_linker()
    linked = linker.link_entities(extracted, policy_name="테스트 암보험", full_text=sample_text)

    # Build graph
    builder = get_graph_builder()
    stats = builder.build_graph(
        policy_id=policy_id,
        policy_name="테스트 암보험",
        insurer="테스트 보험사",
        articles=parsed.articles,
        extracted_data=extracted,
        embeddings=embeddings,
    )

    print(f"✓ Test policy created: {stats.total_nodes} nodes, {stats.relationships} relationships")

    # Return policy_id and first article's node_id
    first_article_id = f"{policy_id}_article_{parsed.articles[0].article_num}"
    return policy_id, first_article_id


def test_query_engine(policy_id, sample_article_id):
    """Test the complete query engine"""

    test_queries = [
        "암보험 1억원 이상 보장되는 경우는?",
        "면책 기간은 얼마나 되나요?",
        "심근경색 보험금은 얼마인가요?",
    ]

    # Initialize services
    parser = get_query_parser()
    search = get_local_search()
    traversal = get_graph_traversal()
    reasoning = get_llm_reasoning(provider=LLMProvider.MOCK)

    for i, query_text in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}: {query_text}")
        print(f"{'='*70}")

        # Step 1: Parse query
        print("\n1️⃣ Parsing query...")
        parsed_query = parser.parse(query_text)
        print(f"   Intent: {parsed_query.intent.value}")
        print(f"   Entities: {len(parsed_query.entities)}")
        for entity in parsed_query.entities:
            print(f"     - {entity.entity_type}: {entity.value}")

        # Step 2: Local search
        print("\n2️⃣ Searching in Neo4j...")
        search_results = search.search(parsed_query, limit=10)
        print(f"   Found: {search_results.total_results} results")
        for j, result in enumerate(search_results.results[:3], 1):
            print(f"   {j}. {result.node_id} (score: {result.relevance_score:.2f})")
            print(f"      {result.text[:80]}...")

        # Step 3: Graph traversal (if we have results)
        print("\n3️⃣ Graph traversal...")
        graph_paths = []
        if search_results.results:
            first_result = search_results.results[0]
            traversal_result = traversal.traverse_hierarchical(
                start_node_id=first_result.node_id,
                direction="down",
                max_depth=2,
            )
            graph_paths = traversal_result.paths
            print(f"   Found: {len(graph_paths)} paths")
            for j, path in enumerate(graph_paths[:2], 1):
                print(f"   {j}. {path}")
        else:
            print("   (No search results to traverse)")

        # Step 4: LLM reasoning
        print("\n4️⃣ LLM reasoning...")
        context = reasoning.assemble_context(
            parsed_query=parsed_query,
            search_results=search_results.results,
            graph_paths=graph_paths,
        )

        result = reasoning.reason(context)
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"\n   Answer:\n   {result.answer[:300]}...")
        print(f"\n   Sources: {len(result.sources)}")
        print(f"   Reasoning steps: {len(result.reasoning_steps)}")


def cleanup_test_policy(policy_id):
    """Remove test policy from Neo4j"""
    builder = get_graph_builder()
    builder.clear_policy(policy_id)
    builder.close()
    print("\n✓ Test policy cleaned up")


def main():
    print("="*70)
    print("🧪 GraphRAG Query Engine Integration Test")
    print("="*70)

    # Setup
    print("\n📊 Setting up test policy...")
    policy_id, sample_article_id = setup_test_policy()

    try:
        # Test
        test_query_engine(policy_id, sample_article_id)

        print("\n" + "="*70)
        print("✅ All query engine tests passed!")
        print("="*70)

    finally:
        # Cleanup
        cleanup_test_policy(policy_id)


if __name__ == "__main__":
    main()
