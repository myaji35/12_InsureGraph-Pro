"""
Deep Knowledge Service 테스트

간단한 보험 텍스트로 엔티티 추출을 테스트합니다.
"""
import asyncio
from app.services.learning.deep_knowledge_service import DeepKnowledgeService


async def test_entity_extraction():
    """엔티티 추출 테스트"""

    # 테스트 텍스트 (자동차 보험 약관 샘플)
    test_text = """
    제1관 제3조 (보험금의 지급사유)

    1. 사망보험금
    피보험자가 보험기간 중 교통사고로 사망한 경우 보험가입금액의 100%인 1억원을 지급합니다.

    2. 후유장해보험금
    피보험자가 보험기간 중 교통사고로 장해지급률 3% 이상의 후유장해를 입은 경우
    보험가입금액에 해당 장해지급률을 곱한 금액을 지급합니다.

    3. 자기부담금
    상해 치료비의 경우 20%의 자기부담금이 적용됩니다.

    제2관 제5조 (면책사항)
    다음의 사유로 인한 손해는 보상하지 않습니다.
    1. 피보험자의 고의적 사고
    2. 전쟁, 혁명, 내란, 폭동
    3. 핵연료 물질에 의한 사고
    """

    document_info = {
        "insurer": "테스트보험",
        "product_type": "자동차보험",
        "title": "개인용 자동차보험 약관 (테스트)"
    }

    print("=" * 80)
    print("Deep Knowledge Service 테스트 시작")
    print("=" * 80)

    service = DeepKnowledgeService()

    print(f"\n📝 테스트 텍스트 길이: {len(test_text)} 자")
    print(f"📄 문서 정보: {document_info}")

    print("\n🔍 엔티티 추출 중...")

    result = await service.process_and_extract(
        chunk_text=test_text,
        document_id="test_doc_001",
        chunk_id="chunk_001",
        document_info=document_info
    )

    print("\n✅ 추출 완료!")
    print(f"   - 엔티티: {result.get('entities', 0)}개")
    print(f"   - 관계: {result.get('relationships', 0)}개")

    if result.get("nodes_by_type"):
        print("\n📊 엔티티 타입별 분포:")
        for entity_type, count in result["nodes_by_type"].items():
            print(f"   - {entity_type}: {count}개")

    if result.get("relationships_by_type"):
        print("\n🔗 관계 타입별 분포:")
        for rel_type, count in result["relationships_by_type"].items():
            print(f"   - {rel_type}: {count}개")

    stats = service.get_stats()
    print("\n📈 전체 통계:")
    print(f"   - 총 엔티티: {stats['total_entities']}개")
    print(f"   - 총 관계: {stats['total_relationships']}개")
    print(f"   - 처리된 청크: {stats['chunks_processed']}개")
    print(f"   - 에러: {stats['errors']}개")

    print("\n=" * 80)
    print("테스트 완료!")
    print("=" * 80)

    # PostgreSQL에서 저장된 데이터 확인
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # 엔티티 확인
        query = text("SELECT COUNT(*) as count FROM knowledge_entities WHERE document_id = 'test_doc_001'")
        result = await db.execute(query)
        row = result.fetchone()
        print(f"\n✅ PostgreSQL에 저장된 엔티티: {row[0]}개")

        # 엔티티 샘플 출력
        query = text("""
            SELECT entity_id, label, type, description
            FROM knowledge_entities
            WHERE document_id = 'test_doc_001'
            LIMIT 5
        """)
        result = await db.execute(query)
        rows = result.fetchall()

        if rows:
            print("\n📋 엔티티 샘플 (최대 5개):")
            for row in rows:
                print(f"   - [{row[2]}] {row[1]}")
                if row[3]:
                    print(f"     설명: {row[3][:100]}")

        # 관계 확인
        query = text("SELECT COUNT(*) as count FROM knowledge_relationships WHERE document_id = 'test_doc_001'")
        result = await db.execute(query)
        row = result.fetchone()
        print(f"\n✅ PostgreSQL에 저장된 관계: {row[0]}개")


if __name__ == "__main__":
    asyncio.run(test_entity_extraction())
