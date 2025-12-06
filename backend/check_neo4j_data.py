#!/usr/bin/env python3
"""
Neo4j 데이터 상태 확인
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "simple123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("=" * 60)
print("📊 Neo4j 데이터 상태 확인")
print("=" * 60)

with driver.session() as session:
    # 1. 전체 노드 수
    result = session.run("MATCH (n) RETURN count(n) as count")
    total_nodes = result.single()["count"]
    print(f"\n✅ 전체 노드 수: {total_nodes:,}")
    
    # 2. 노드 타입별 개수
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    print("\n📌 노드 타입별 개수 (상위 10개):")
    for record in result:
        print(f"  - {record['type']}: {record['count']:,}")
    
    # 3. 전체 관계 수
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    total_rels = result.single()["count"]
    print(f"\n✅ 전체 관계 수: {total_rels:,}")
    
    # 4. 관계 타입별 개수
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    print("\n📌 관계 타입별 개수 (상위 10개):")
    for record in result:
        print(f"  - {record['type']}: {record['count']:,}")
    
    # 5. 샘플 노드 확인
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, n.label as label, n.description as desc
        LIMIT 5
    """)
    print("\n📝 샘플 노드 (5개):")
    for record in result:
        label = record['label'] if record['label'] else 'N/A'
        desc = record['desc'][:50] + '...' if record['desc'] and len(record['desc']) > 50 else record['desc']
        print(f"  - [{record['type']}] {label}")
        if desc:
            print(f"    설명: {desc}")

driver.close()

print("\n" + "=" * 60)
print("✅ 확인 완료")
print("=" * 60)
