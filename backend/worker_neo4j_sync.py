"""
Neo4j Data Synchronization Worker

PostgreSQL의 knowledge_entities와 knowledge_relationships 데이터를
Neo4j 그래프 데이터베이스로 동기화합니다.
"""
import sys
import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import text as sql_text
from neo4j import GraphDatabase

from app.core.database import AsyncSessionLocal
from app.core.config import settings


class Neo4jSyncWorker:
    """PostgreSQL → Neo4j 동기화 워커"""

    def __init__(self):
        """Neo4j 드라이버 초기화"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("✅ Neo4j driver initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Neo4j driver: {e}")
            raise

    def close(self):
        """Neo4j 연결 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")

    async def run(self, limit: Optional[int] = None, clear_existing: bool = False):
        """메인 실행 함수"""
        logger.info("=" * 80)
        logger.info("🔄 Neo4j Data Synchronization Worker Started")
        logger.info("=" * 80)

        try:
            # 1. Neo4j 연결 테스트
            await self.test_neo4j_connection()

            # 2. 기존 데이터 삭제 (옵션)
            if clear_existing:
                await self.clear_neo4j_data()

            # 3. PostgreSQL에서 엔티티 조회
            entities = await self.fetch_entities_from_postgres(limit)
            logger.info(f"📄 Fetched {len(entities)} entities from PostgreSQL")

            # 4. PostgreSQL에서 관계 조회
            relationships = await self.fetch_relationships_from_postgres()
            logger.info(f"🔗 Fetched {len(relationships)} relationships from PostgreSQL")

            # 5. Neo4j에 엔티티 생성
            entity_count = await self.create_entities_in_neo4j(entities)
            logger.info(f"✅ Created {entity_count} entity nodes in Neo4j")

            # 6. Neo4j에 관계 생성
            relationship_count = await self.create_relationships_in_neo4j(relationships)
            logger.info(f"✅ Created {relationship_count} relationships in Neo4j")

            # 7. 최종 통계
            logger.info(f"\n{'=' * 80}")
            logger.info(f"📊 Synchronization Complete:")
            logger.info(f"   Entities synced: {entity_count}")
            logger.info(f"   Relationships synced: {relationship_count}")
            logger.info(f"{'=' * 80}")

        except Exception as e:
            logger.error(f"❌ Synchronization failed: {e}", exc_info=True)
            raise
        finally:
            self.close()

    async def test_neo4j_connection(self):
        """Neo4j 연결 테스트"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                logger.info(f"✅ Neo4j connection test successful: {record['test']}")
        except Exception as e:
            logger.error(f"❌ Neo4j connection test failed: {e}")
            raise

    async def clear_neo4j_data(self):
        """Neo4j 기존 데이터 삭제"""
        logger.warning("⚠️  Clearing existing Neo4j data...")
        try:
            with self.driver.session() as session:
                # 모든 노드와 관계 삭제
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("✅ Neo4j data cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear Neo4j data: {e}")
            raise

    async def fetch_entities_from_postgres(self, limit: Optional[int] = None) -> List[Dict]:
        """PostgreSQL에서 엔티티 조회"""
        async with AsyncSessionLocal() as db:
            query_str = """
                SELECT
                    entity_id, label, type, description, source_text,
                    document_id, insurer, product_type, created_at
                FROM knowledge_entities
                ORDER BY created_at DESC
            """
            if limit:
                query_str += f" LIMIT {limit}"

            result = await db.execute(sql_text(query_str))
            rows = result.fetchall()

            entities = []
            for row in rows:
                entities.append({
                    "entity_id": str(row.entity_id),
                    "label": row.label,
                    "type": row.type,
                    "description": row.description or "",
                    "source_text": row.source_text or "",
                    "document_id": str(row.document_id),
                    "insurer": row.insurer or "",
                    "product_type": row.product_type or "",
                    "created_at": row.created_at.isoformat() if row.created_at else ""
                })

            return entities

    async def fetch_relationships_from_postgres(self) -> List[Dict]:
        """PostgreSQL에서 관계 조회"""
        async with AsyncSessionLocal() as db:
            query_str = """
                SELECT
                    source_entity_id, target_entity_id, type, description, created_at
                FROM knowledge_relationships
                ORDER BY created_at DESC
            """

            result = await db.execute(sql_text(query_str))
            rows = result.fetchall()

            relationships = []
            for row in rows:
                relationships.append({
                    "source_entity_id": str(row.source_entity_id),
                    "target_entity_id": str(row.target_entity_id),
                    "type": row.type,
                    "description": row.description or "",
                    "created_at": row.created_at.isoformat() if row.created_at else ""
                })

            return relationships

    async def create_entities_in_neo4j(self, entities: List[Dict]) -> int:
        """Neo4j에 엔티티 노드 생성"""
        count = 0
        batch_size = 100

        with self.driver.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]

                # 배치 단위로 노드 생성
                for entity in batch:
                    try:
                        # 엔티티 타입별로 레이블 지정
                        label = self._get_neo4j_label(entity["type"])

                        cypher = f"""
                        MERGE (e:{label} {{entity_id: $entity_id}})
                        SET e.label = $label,
                            e.type = $type,
                            e.description = $description,
                            e.source_text = $source_text,
                            e.document_id = $document_id,
                            e.insurer = $insurer,
                            e.product_type = $product_type,
                            e.created_at = $created_at
                        """

                        session.run(cypher, **entity)
                        count += 1

                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create entity {entity['entity_id']}: {e}")

                if (i + batch_size) % 1000 == 0:
                    logger.info(f"   Progress: {count}/{len(entities)} entities created")

        return count

    async def create_relationships_in_neo4j(self, relationships: List[Dict]) -> int:
        """Neo4j에 관계 생성"""
        count = 0
        batch_size = 100

        with self.driver.session() as session:
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i + batch_size]

                for rel in batch:
                    try:
                        # 관계 타입을 Neo4j 형식으로 변환 (대문자, 언더스코어)
                        rel_type = rel["type"].upper().replace("-", "_")

                        cypher = f"""
                        MATCH (source {{entity_id: $source_entity_id}})
                        MATCH (target {{entity_id: $target_entity_id}})
                        MERGE (source)-[r:{rel_type}]->(target)
                        SET r.description = $description,
                            r.created_at = $created_at
                        """

                        session.run(cypher, **rel)
                        count += 1

                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create relationship: {e}")

                if (i + batch_size) % 1000 == 0:
                    logger.info(f"   Progress: {count}/{len(relationships)} relationships created")

        return count

    def _get_neo4j_label(self, entity_type: str) -> str:
        """엔티티 타입을 Neo4j 레이블로 변환"""
        label_mapping = {
            "coverage_item": "CoverageItem",
            "benefit_amount": "BenefitAmount",
            "payment_condition": "PaymentCondition",
            "exclusion": "Exclusion",
            "deductible": "Deductible",
            "rider": "Rider",
            "eligibility": "Eligibility",
            "article": "Article",
            "term": "Term",
            "period": "Period"
        }
        return label_mapping.get(entity_type, "Entity")


async def main():
    """메인 함수"""
    import sys

    # 명령줄 인자 파싱
    limit = None
    clear_existing = False

    if len(sys.argv) > 1:
        if sys.argv[1] == "--clear":
            clear_existing = True
        elif sys.argv[1].isdigit():
            limit = int(sys.argv[1])

    if len(sys.argv) > 2 and sys.argv[2] == "--clear":
        clear_existing = True

    logger.info(f"Options: limit={limit}, clear_existing={clear_existing}")

    worker = Neo4jSyncWorker()
    await worker.run(limit=limit, clear_existing=clear_existing)


if __name__ == "__main__":
    asyncio.run(main())
