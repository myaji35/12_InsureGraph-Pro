"""
간단한 Neo4j 그래프 생성 테스트

GraphBuilder의 복잡한 의존성 없이 직접 Neo4j에 
보험 지식 그래프를 생성하는 테스트입니다.
"""
from neo4j import GraphDatabase
from datetime import datetime

def create_sample_insurance_graph():
    """샘플 보험 지식 그래프 생성"""
    
    print("=" * 70)
    print("📊 Neo4j 보험 지식 그래프 생성 테스트")
    print("=" * 70)
    print()
    
    # 연결
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "change-me-in-production")
    )
    
    try:
        with driver.session() as session:
            # 1. Product 노드 생성
            print("1️⃣ Product 노드 생성 중...")
            session.run("""
                CREATE (p:Product {
                    id: 'prod_metlife_cancer_001',
                    product_code: 'ML-CI-001',
                    name: 'MetLife 무배당 프라임 암보험',
                    insurer: 'MetLife 생명보험',
                    product_type: '암보험',
                    version: '1.0',
                    launch_date: date('2024-01-01'),
                    status: 'active',
                    created_at: datetime()
                })
            """)
            print("   ✓ Product 노드 생성 완료\n")
            
            # 2. Coverage 노드 생성
            print("2️⃣ Coverage 노드 생성 중...")
            session.run("""
                CREATE (c1:Coverage {
                    id: 'cov_cancer_diagnosis',
                    code: 'CI-D-001',
                    name: '암진단급여금',
                    type: 'cancer',
                    category: 'diagnosis',
                    payment_type: 'lump_sum',
                    base_amount: 100000000,
                    created_at: datetime()
                }),
                (c2:Coverage {
                    id: 'cov_minor_cancer',
                    code: 'CI-D-002',
                    name: '소액암진단급여금',
                    type: 'cancer',
                    category: 'diagnosis',
                    payment_type: 'lump_sum',
                    base_amount: 10000000,
                    created_at: datetime()
                }),
                (c3:Coverage {
                    id: 'cov_ami',
                    code: 'CVD-D-001',
                    name: '급성심근경색증진단급여금',
                    type: 'cardiovascular',
                    category: 'diagnosis',
                    payment_type: 'lump_sum',
                    base_amount: 50000000,
                    created_at: datetime()
                })
            """)
            print("   ✓ 3개의 Coverage 노드 생성 완료\n")
            
            # 3. Product -> Coverage 관계 생성
            print("3️⃣ Product-Coverage 관계 생성 중...")
            session.run("""
                MATCH (p:Product {id: 'prod_metlife_cancer_001'})
                MATCH (c1:Coverage {id: 'cov_cancer_diagnosis'})
                MATCH (c2:Coverage {id: 'cov_minor_cancer'})
                MATCH (c3:Coverage {id: 'cov_ami'})
                CREATE (p)-[:HAS_COVERAGE {order: 1, is_optional: false}]->(c1)
                CREATE (p)-[:HAS_COVERAGE {order: 2, is_optional: false}]->(c2)
                CREATE (p)-[:HAS_COVERAGE {order: 3, is_optional: false}]->(c3)
            """)
            print("   ✓ 3개의 HAS_COVERAGE 관계 생성 완료\n")
            
            # 4. Coverage -> Disease 관계 생성 (COVERS)
            print("4️⃣ Coverage-Disease COVERS 관계 생성 중...")
            session.run("""
                MATCH (c1:Coverage {id: 'cov_cancer_diagnosis'})
                MATCH (d1:Disease {kcd_code: 'C00-C97'})
                CREATE (c1)-[:COVERS {
                    confidence: 0.95,
                    extraction_method: 'manual',
                    benefit_amount: 100000000,
                    reasoning: '일반암으로 진단 확정 시 가입금액 전액 지급'
                }]->(d1)
            """)
            
            session.run("""
                MATCH (c2:Coverage {id: 'cov_minor_cancer'})
                MATCH (d2:Disease {kcd_code: 'C77'})
                MATCH (d3:Disease {kcd_code: 'C44'})
                CREATE (c2)-[:COVERS {
                    confidence: 0.98,
                    extraction_method: 'manual',
                    benefit_amount: 10000000,
                    reasoning: '갑상선암은 소액암으로 분류하여 가입금액의 10% 지급'
                }]->(d2)
                CREATE (c2)-[:COVERS {
                    confidence: 0.98,
                    extraction_method: 'manual',
                    benefit_amount: 10000000,
                    reasoning: '기타 피부암은 소액암으로 분류하여 가입금액의 10% 지급'
                }]->(d3)
            """)
            
            session.run("""
                MATCH (c3:Coverage {id: 'cov_ami'})
                MATCH (d4:Disease {kcd_code: 'I21'})
                CREATE (c3)-[:COVERS {
                    confidence: 0.92,
                    extraction_method: 'manual',
                    benefit_amount: 50000000,
                    reasoning: '급성심근경색증으로 진단 확정 시 가입금액의 50% 지급'
                }]->(d4)
            """)
            print("   ✓ 4개의 COVERS 관계 생성 완료\n")
            
            # 5. Condition 노드 생성
            print("5️⃣ Condition 노드 생성 중...")
            session.run("""
                CREATE (cond:Condition {
                    id: 'cond_cancer_waiting_period',
                    type: 'waiting_period',
                    days: 90,
                    description: '계약일로부터 90일 면책기간',
                    trigger_event: 'diagnosis'
                })
            """)
            print("   ✓ Condition 노드 생성 완료\n")
            
            # 6. Coverage -> Condition 관계 생성
            print("6️⃣ Coverage-Condition REQUIRES 관계 생성 중...")
            session.run("""
                MATCH (c1:Coverage {id: 'cov_cancer_diagnosis'})
                MATCH (c2:Coverage {id: 'cov_minor_cancer'})
                MATCH (cond:Condition {id: 'cond_cancer_waiting_period'})
                CREATE (c1)-[:REQUIRES {order: 1, is_mandatory: true}]->(cond)
                CREATE (c2)-[:REQUIRES {order: 1, is_mandatory: true}]->(cond)
            """)
            print("   ✓ 2개의 REQUIRES 관계 생성 완료\n")
            
            # 7. 결과 확인
            print("=" * 70)
            print("✅ 그래프 생성 완료!")
            print("=" * 70)
            print()
            
            # 노드 개수 확인
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            print("📊 생성된 노드:")
            for record in result:
                print(f"   • {record['label']}: {record['count']}개")
            print()
            
            # 관계 개수 확인
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            print("🔗 생성된 관계:")
            for record in result:
                print(f"   • {record['rel_type']}: {record['count']}개")
            print()
            
            # 샘플 쿼리
            print("💡 생성된 그래프 확인:")
            result = session.run("""
                MATCH (p:Product)-[:HAS_COVERAGE]->(c:Coverage)-[:COVERS]->(d:Disease)
                RETURN p.name as product, c.name as coverage, 
                       d.name_ko as disease, d.kcd_code as kcd
                LIMIT 10
            """)
            for record in result:
                print(f"   • {record['product']}")
                print(f"     └─ {record['coverage']} → {record['disease']} ({record['kcd']})")
            print()
            
            print("=" * 70)
            print("🎉 테스트 완료! Neo4j Browser에서 확인하세요:")
            print("   http://localhost:7474")
            print()
            print("💡 추천 Cypher 쿼리:")
            print("   MATCH (n) RETURN n LIMIT 50")
            print("   MATCH p=()-[r:COVERS]->() RETURN p")
            print("   MATCH (p:Product)-[*1..3]-(d:Disease) RETURN p, d")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()
        print("\n🔌 Neo4j 연결 종료")


if __name__ == "__main__":
    create_sample_insurance_graph()
