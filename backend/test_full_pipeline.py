"""
Full Pipeline Test

전체 파이프라인을 통합 테스트합니다.
샘플 텍스트 데이터를 사용하여 PDF → 그래프까지 전체 흐름을 검증합니다.
"""
import asyncio
from pathlib import Path
from uuid import uuid4

# Create a temporary PDF with sample text
def create_sample_pdf():
    """Create a sample PDF for testing"""
    import fitz  # PyMuPDF

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

    # Create PDF
    pdf_path = Path("test_sample_policy.pdf")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    # Insert text with better formatting
    y_position = 72  # Start from top
    for line in sample_text.strip().split('\n'):
        if line.strip():
            page.insert_text(
                (72, y_position),  # (x, y)
                line,
                fontsize=11,
                fontname="helv",
            )
            y_position += 15  # Line spacing

    doc.save(str(pdf_path))
    doc.close()

    return pdf_path


async def progress_callback(step: str, progress: int):
    """Progress callback"""
    bar_length = 30
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"  [{step:20s}] [{bar}] {progress:3d}%")


async def test_full_pipeline():
    from app.workflows.simple_ingestion_workflow import get_ingestion_workflow

    print("=" * 70)
    print("🚀 Full Pipeline Integration Test")
    print("=" * 70)

    # Create sample PDF
    print("\n📄 Creating sample PDF...")
    pdf_path = create_sample_pdf()
    print(f"  ✓ Created: {pdf_path}")

    # Run pipeline
    print("\n🔄 Running ingestion pipeline...")
    workflow = get_ingestion_workflow()

    result = await workflow.run(
        pdf_path=str(pdf_path),
        policy_name="샘플 암보험 약관",
        insurer="테스트 보험사",
        policy_id=uuid4(),
        progress_callback=progress_callback,
    )

    # Display results
    print(f"\n{'='*70}")
    print(f"📊 Pipeline Result")
    print(f"{'='*70}")
    print(f"Pipeline ID: {result.pipeline_id}")
    print(f"Policy ID: {result.policy_id}")
    print(f"Status: {result.status.value}")
    print(f"Duration: {result.duration_seconds:.2f}s")

    print(f"\n📈 Metrics:")
    print(f"  PDF Processing:")
    print(f"    - Pages: {result.metrics.total_pages}")
    print(f"    - Characters: {result.metrics.total_chars:,}")

    print(f"\n  Legal Structure:")
    print(f"    - Articles: {result.metrics.total_articles}")
    print(f"    - Paragraphs: {result.metrics.total_paragraphs}")
    print(f"    - Subclauses: {result.metrics.total_subclauses}")

    print(f"\n  Extracted Data:")
    print(f"    - Amounts: {result.metrics.total_amounts}")
    print(f"    - Periods: {result.metrics.total_periods}")
    print(f"    - KCD Codes: {result.metrics.total_kcd_codes}")

    print(f"\n  Embeddings:")
    print(f"    - Total: {result.metrics.total_embeddings}")

    print(f"\n  Graph Database:")
    print(f"    - Nodes: {result.metrics.graph_nodes}")
    print(f"    - Relationships: {result.metrics.graph_relationships}")

    if result.status.value == "completed":
        print(f"\n✅ Pipeline completed successfully!")

        # Show breakdown
        if result.graph_stats:
            print(f"\n📊 Graph Node Breakdown:")
            print(f"    - Policy: {result.graph_stats.policy_nodes}")
            print(f"    - Articles: {result.graph_stats.article_nodes}")
            print(f"    - Paragraphs: {result.graph_stats.paragraph_nodes}")
            print(f"    - Subclauses: {result.graph_stats.subclause_nodes}")
            print(f"    - Amounts: {result.graph_stats.amount_nodes}")
            print(f"    - Periods: {result.graph_stats.period_nodes}")
            print(f"    - KCD Codes: {result.graph_stats.kcd_nodes}")

        # Test search
        print(f"\n🔍 Testing Search...")
        from app.services.query_parser import get_query_parser
        from app.services.local_search import get_local_search

        parser = get_query_parser()
        search = get_local_search()

        test_queries = [
            "암보험 보장",
            "1억원",
            "90일",
        ]

        for query in test_queries:
            parsed = parser.parse(query)
            results = search.search(parsed, limit=3)
            print(f"  Query: '{query}' → {results.total_results} results")

        search.close()

    else:
        print(f"\n❌ Pipeline failed!")
        print(f"   Error: {result.error}")
        if result.error_step:
            print(f"   Failed at: {result.error_step}")

    # Cleanup
    print(f"\n🧹 Cleaning up...")
    if result.status.value == "completed":
        from app.services.neo4j_graph_builder import get_graph_builder
        builder = get_graph_builder()
        builder.clear_policy(result.policy_id)
        builder.close()
        print(f"  ✓ Cleared test policy from Neo4j")

    pdf_path.unlink()
    print(f"  ✓ Deleted test PDF")

    print("\n" + "=" * 70)
    print("✅ Full pipeline test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
