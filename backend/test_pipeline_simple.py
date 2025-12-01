"""
Simple Pipeline Test

텍스트 데이터를 직접 사용하여 파이프라인을 테스트합니다.
(PDF 생성 문제를 우회)
"""
import asyncio
from uuid import uuid4

sample_text = """제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원
3. 유사암(D00-D09): 500만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.

제11조 [보험료 납입]
① 보험료는 매월 10만원씩 납입해야 합니다.
② 보험료 미납 시 3개월 후 계약이 해지될 수 있습니다.

제12조 [계약의 해지]
① 계약자는 언제든지 계약을 해지할 수 있습니다.
② 해지 시 1년 이상 경과한 경우 해약환급금을 지급합니다.
"""


async def test_pipeline():
    """Test pipeline with direct text input"""
    from app.services.legal_structure_parser import get_legal_parser
    from app.services.critical_data_extractor import get_critical_extractor
    from app.services.embedding_generator import get_embedding_generator
    from app.services.neo4j_graph_builder import get_graph_builder

    print("=" * 70)
    print("🚀 Simple Pipeline Test")
    print("=" * 70)

    policy_id = uuid4()

    # Step 1: Parse structure
    print("\n[Step 1/4] Legal Structure Parsing...")
    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)
    print(f"  ✓ Parsed {parsed.total_articles} articles, {parsed.total_paragraphs} paragraphs, {parsed.total_subclauses} subclauses")

    # Step 2: Extract data
    print("\n[Step 2/4] Critical Data Extraction...")
    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)
    print(f"  ✓ Extracted {len(extracted.amounts)} amounts, {len(extracted.periods)} periods, {len(extracted.kcd_codes)} KCD codes")

    # Step 3: Generate embeddings
    print("\n[Step 3/4] Embedding Generation...")
    emb_gen = get_embedding_generator()
    embeddings = emb_gen.generate_for_articles(parsed.articles)
    print(f"  ✓ Generated {embeddings.total_embeddings} embeddings (~{embeddings.total_tokens:,} tokens)")

    # Step 4: Build graph
    print("\n[Step 4/4] Neo4j Graph Construction...")
    builder = get_graph_builder()
    builder.create_constraints()

    stats = builder.build_graph(
        policy_id=policy_id,
        policy_name="샘플 암보험 약관",
        insurer="테스트 보험사",
        articles=parsed.articles,
        extracted_data=extracted,
        embeddings=embeddings,
    )

    print(f"  ✓ Built graph with {stats.total_nodes} nodes, {stats.relationships} relationships")

    # Display summary
    print(f"\n{'='*70}")
    print(f"📊 Pipeline Summary")
    print(f"{'='*70}")
    print(f"Policy ID: {policy_id}")
    print(f"\nData Processing:")
    print(f"  - Articles: {parsed.total_articles}")
    print(f"  - Paragraphs: {parsed.total_paragraphs}")
    print(f"  - Subclauses: {parsed.total_subclauses}")
    print(f"  - Amounts: {len(extracted.amounts)}")
    print(f"  - Periods: {len(extracted.periods)}")
    print(f"  - KCD Codes: {len(extracted.kcd_codes)}")
    print(f"  - Embeddings: {embeddings.total_embeddings}")

    print(f"\nGraph Database:")
    print(f"  - Total Nodes: {stats.total_nodes}")
    print(f"  - Policy: {stats.policy_nodes}")
    print(f"  - Articles: {stats.article_nodes}")
    print(f"  - Paragraphs: {stats.paragraph_nodes}")
    print(f"  - Subclauses: {stats.subclause_nodes}")
    print(f"  - Amounts: {stats.amount_nodes}")
    print(f"  - Periods: {stats.period_nodes}")
    print(f"  - KCD Codes: {stats.kcd_nodes}")
    print(f"  - Relationships: {stats.relationships}")

    # Test search
    print(f"\n{'='*70}")
    print(f"🔍 Testing Search Functionality")
    print(f"{'='*70}")

    from app.services.query_parser import get_query_parser
    from app.services.local_search import get_local_search

    parser_q = get_query_parser()
    search = get_local_search()

    test_queries = [
        "암보험 보장 내용",
        "1억원 이상",
        "90일 대기기간",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        parsed_q = parser_q.parse(query)
        print(f"  Intent: {parsed_q.intent.value}")

        results = search.search(parsed_q, limit=3)
        print(f"  Results: {results.total_results} found")

        for i, result in enumerate(results.results[:2], 1):
            print(f"    {i}. [{result.node_type}] {result.text[:60]}...")

    search.close()

    # Cleanup
    print(f"\n{'='*70}")
    print(f"🧹 Cleanup")
    print(f"{'='*70}")
    builder.clear_policy(policy_id)
    builder.close()
    print(f"  ✓ Cleared test policy from Neo4j")

    print("\n" + "=" * 70)
    print("✅ Pipeline test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_pipeline())
