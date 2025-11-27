"""
Graph Generation Test Script

이 스크립트는 완료된 문서(MetLife)의 텍스트를 사용하여
Neo4j 지식 그래프를 생성하는 테스트를 수행합니다.
"""
import asyncio
from neo4j import GraphDatabase
from app.services.graph.graph_builder import GraphBuilder
from app.services.graph.neo4j_service import Neo4jService

# 샘플 보험 문서 텍스트 (MetLife 암보험 예시)
SAMPLE_INSURANCE_TEXT = """
제10조 (보험금의 지급)

① 회사는 피보험자가 이 계약의 보험기간 중 암으로 진단 확정되었을 때에는 
가입금액을 암진단급여금으로 지급합니다.

② 다만, 다음 각 호의 악성신생물은 일반암으로 보지 않으며 소액암으로 
분류하여 가입금액의 10%를 지급합니다:
1. 갑상선의 악성신생물(C77)
2. 기타 피부의 악성신생물(C44)
3. 제자리암(D00~D09)
4. 경계성종양(D37~D48)

제11조 (보험금 지급의 제한)

① 회사는 다음 각 호의 경우에는 보험금을 지급하지 않습니다:
1. 피보험자가 고의로 자신을 해친 경우
2. 계약자 또는 수익자의 고의로 피보험자를 해친 경우
3. 전쟁, 외국의 무력행사, 혁명, 내란, 사변, 폭동으로 인한 경우

제12조 (면책기간)

① 회사는 피보험자가 이 계약의 보험계약일(부활(復活)계약의 경우는 
부활(復活)계약일)부터 90일 이내에 암으로 진단 확정되었을 때에는 
보험금을 지급하지 않습니다.

제13조 (급성심근경색증 진단급여금)

① 회사는 피보험자가 이 계약의 보험기간 중 급성심근경색증(I21)으로 
진단 확정되었을 때에는 가입금액의 50%를 지급합니다.

② 급성심근경색증 진단은 병원의 전문의에 의하여 내려져야 하며, 
다음 각 호의 진단 근거가 있어야 합니다:
1. 전형적인 흉통의 병력
2. 심전도의 변화
3. 심장효소의 증가

제14조 (뇌출혈 진단급여금)

① 회사는 피보험자가 이 계약의 보험기간 중 뇌출혈(I61)로 진단 확정되었을 때에는 
가입금액의 50%를 지급합니다.

제15조 (보험료의 납입면제)

① 회사는 피보험자가 이 계약의 보험기간 중 암으로 진단 확정되었을 때에는 
차회 이후의 보험료 납입을 면제합니다.
"""

PRODUCT_INFO = {
    "product_name": "MetLife 무배당 프라임 암보험",
    "company": "MetLife 생명보험",
    "product_type": "암보험",
    "version": "1.0",
    "effective_date": "2024-01-01",
    "document_id": "983882c9-8728-4a23-b04c-e4a7557ec8e4",
}


async def test_graph_generation():
    """그래프 생성 테스트"""
    
    print("=" * 70)
    print("📊 Neo4j 지식 그래프 생성 테스트")
    print("=" * 70)
    print()
    
    # 1. Neo4j 연결
    print("1️⃣ Neo4j 서비스에 연결 중...")
    neo4j_service = Neo4jService(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="change-me-in-production"
    )
    
    try:
        neo4j_service.connect()
        print("   ✓ Neo4j 연결 성공!\n")
        
        # 2. GraphBuilder 초기화
        print("2️⃣ GraphBuilder 초기화 중...")
        graph_builder = GraphBuilder(
            neo4j_service=neo4j_service,
            embedding_service=None  # 임베딩 생성 스킵 (테스트용)
        )
        print("   ✓ GraphBuilder 준비 완료!\n")
        
        # 3. 그래프 생성
        print("3️⃣ 보험 문서 파싱 및 그래프 생성 중...")
        print(f"   - 상품명: {PRODUCT_INFO['product_name']}")
        print(f"   - 회사: {PRODUCT_INFO['company']}")
        print()
        
        stats = await graph_builder.build_graph_from_document(
            ocr_text=SAMPLE_INSURANCE_TEXT,
            product_info=PRODUCT_INFO,
            generate_embeddings=False  # 임베딩 생성 스킵
        )
        
        # 4. 결과 출력
        print("\n" + "=" * 70)
        print("✅ 그래프 생성 완료!")
        print("=" * 70)
        print()
        print(f"📈 생성 통계:")
        print(f"   • 총 노드 수: {stats.total_nodes}개")
        print(f"   • 총 관계 수: {stats.total_relationships}개")
        print(f"   • 소요 시간: {stats.construction_time_seconds:.2f}초")
        print()
        
        if stats.nodes_by_type:
            print(f"📊 노드 유형별 개수:")
            for node_type, count in stats.nodes_by_type.items():
                print(f"   • {node_type}: {count}개")
            print()
        
        if stats.relationships_by_type:
            print(f"🔗 관계 유형별 개수:")
            for rel_type, count in stats.relationships_by_type.items():
                print(f"   • {rel_type}: {count}개")
            print()
        
        if stats.errors:
            print(f"⚠️ 오류:")
            for error in stats.errors:
                print(f"   • {error}")
            print()
        
        # 5. 데이터 확인
        print("5️⃣ 생성된 그래프 데이터 확인 중...")
        
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "change-me-in-production")
        )
        
        with driver.session() as session:
            # Product 노드 확인
            result = session.run("MATCH (p:Product) RETURN p.product_name as name")
            products = [r["name"] for r in result]
            print(f"   • Product 노드: {len(products)}개")
            for p in products:
                print(f"      - {p}")
            
            # Coverage 노드 확인
            result = session.run("MATCH (c:Coverage) RETURN c.coverage_name as name")
            coverages = [r["name"] for r in result]
            print(f"   • Coverage 노드: {len(coverages)}개")
            for c in coverages:
                print(f"      - {c}")
            
            # Disease 노드 확인 (생성된 것만)
            result = session.run("""
                MATCH (d:Disease)<-[:COVERS|EXCLUDES]-(c:Coverage)
                RETURN DISTINCT d.standard_name as name, d.kcd_codes as kcd
            """)
            diseases = [(r["name"], r["kcd"]) for r in result]
            print(f"   • Disease 노드 (연결된 것): {len(diseases)}개")
            for name, kcd in diseases:
                print(f"      - {name} ({kcd})")
            
            # Clause 노드 확인
            result = session.run("MATCH (c:Clause) RETURN count(c) as count")
            clause_count = result.single()["count"]
            print(f"   • Clause 노드: {clause_count}개")
            
            # 관계 확인
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            print(f"\n   • 관계:")
            for record in result:
                print(f"      - {record['rel_type']}: {record['count']}개")
        
        driver.close()
        
        print("\n" + "=" * 70)
        print("🎉 테스트 완료! Neo4j Browser에서 확인하세요:")
        print("   http://localhost:7474")
        print()
        print("💡 추천 Cypher 쿼리:")
        print("   MATCH (n) RETURN n LIMIT 50")
        print("   MATCH p=()-[r:COVERS]->() RETURN p")
        print("   MATCH (c:Coverage)-[r:COVERS]->(d:Disease) RETURN c, r, d")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        neo4j_service.close()
        print("\n🔌 Neo4j 연결 종료")


if __name__ == "__main__":
    asyncio.run(test_graph_generation())
