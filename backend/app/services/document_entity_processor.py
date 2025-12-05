"""
Document Entity Processing Service

documents 테이블에서 full_text를 읽어 엔티티를 추출하고 데이터베이스에 저장합니다.
"""
import sys
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import text

sys.path.append("/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend")
from app.core.database import AsyncSessionLocal
from app.services.rule_based_entity_extractor import rule_extractor


class DocumentEntityProcessor:
    """문서 엔티티 처리 서비스"""

    def __init__(self):
        """초기화"""
        self.extractor = rule_extractor

    async def process_document(self, document_id: str) -> Dict:
        """
        단일 문서 처리 (documents 테이블)

        Args:
            document_id: 문서 UUID

        Returns:
            처리 결과
        """
        async with AsyncSessionLocal() as db:
            # 문서 조회 (documents 테이블)
            query = text("""
                SELECT id, policy_name, insurer, full_text
                FROM documents
                WHERE id = :document_id
            """)
            result = await db.execute(query, {"document_id": document_id})
            doc = result.fetchone()

            if not doc:
                logger.error(f"Document {document_id} not found in documents table")
                return {"success": False, "error": "Document not found"}

            doc_id = str(doc[0])
            policy_name = doc[1]
            insurer = doc[2]
            full_text = doc[3]

            # 텍스트가 없으면 스킵
            if not full_text or len(full_text) < 100:
                logger.warning(f"Document {doc_id} has no sufficient text (length: {len(full_text) if full_text else 0})")
                return {"success": False, "error": "No sufficient text"}

            logger.info(f"🔍 Processing document {doc_id}: {policy_name[:50]}...")
            logger.info(f"   Text length: {len(full_text):,} characters")

            # 엔티티 추출
            entities = self.extractor.extract_entities(
                text=full_text,
                document_id=doc_id,
                insurer=insurer,
                product_type="보험약관"  # documents 테이블에는 product_type이 없으므로 기본값 사용
            )

            # 관계 추출
            relationships = self.extractor.extract_relationships(entities, full_text)

            # 이미 존재하는 엔티티 삭제 (재처리 시)
            delete_entities_query = text("""
                DELETE FROM knowledge_entities WHERE document_id = :document_id
            """)
            await db.execute(delete_entities_query, {"document_id": doc_id})

            delete_rels_query = text("""
                DELETE FROM knowledge_relationships
                WHERE source_entity_id IN (
                    SELECT entity_id FROM knowledge_entities WHERE document_id = :document_id
                )
            """)
            await db.execute(delete_rels_query, {"document_id": doc_id})

            # 엔티티 저장
            entity_count = 0
            if entities:
                for entity in entities:
                    insert_query = text("""
                        INSERT INTO knowledge_entities (
                            entity_id, label, type, description, source_text,
                            document_id, insurer, product_type, created_at
                        ) VALUES (
                            :entity_id, :label, :type, :description, :source_text,
                            :document_id, :insurer, :product_type, :created_at
                        )
                    """)
                    await db.execute(insert_query, entity)
                    entity_count += 1

            # 관계 저장
            relationship_count = 0
            if relationships:
                for rel in relationships:
                    insert_query = text("""
                        INSERT INTO knowledge_relationships (
                            source_entity_id, target_entity_id, type, description, created_at
                        ) VALUES (
                            :source_entity_id, :target_entity_id, :type, :description, :created_at
                        )
                    """)
                    try:
                        await db.execute(insert_query, rel)
                        relationship_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert relationship: {e}")

            await db.commit()

            logger.info(f"✅ Document {doc_id} processed: {entity_count} entities, {relationship_count} relationships")

            return {
                "success": True,
                "document_id": doc_id,
                "entities_extracted": entity_count,
                "relationships_extracted": relationship_count
            }

    async def process_all_completed_documents(self, limit: Optional[int] = None) -> Dict:
        """
        모든 documents 테이블의 문서 처리

        Args:
            limit: 최대 처리 문서 수 (None이면 전체)

        Returns:
            처리 결과
        """
        async with AsyncSessionLocal() as db:
            # documents 테이블에서 문서 조회
            query_str = """
                SELECT id FROM documents
                WHERE status = 'completed'
                ORDER BY created_at DESC
            """
            if limit:
                query_str += f" LIMIT {limit}"

            query = text(query_str)
            result = await db.execute(query)
            doc_ids = [str(row[0]) for row in result.fetchall()]

            if not doc_ids:
                logger.info("No completed documents found in documents table")
                return {
                    "success": True,
                    "total_documents": 0,
                    "processed": 0,
                    "failed": 0,
                    "total_entities": 0,
                    "total_relationships": 0
                }

            logger.info(f"📚 Found {len(doc_ids)} completed documents to process")

            # 각 문서 처리
            processed = 0
            failed = 0
            total_entities = 0
            total_relationships = 0

            for doc_id in doc_ids:
                try:
                    result = await self.process_document(doc_id)
                    if result["success"]:
                        processed += 1
                        total_entities += result["entities_extracted"]
                        total_relationships += result["relationships_extracted"]
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Failed to process document {doc_id}: {e}", exc_info=True)
                    failed += 1

            logger.info(f"=" * 80)
            logger.info(f"📊 Processing Summary:")
            logger.info(f"  - Total Documents: {len(doc_ids)}")
            logger.info(f"  - Processed: {processed}")
            logger.info(f"  - Failed: {failed}")
            logger.info(f"  - Total Entities: {total_entities}")
            logger.info(f"  - Total Relationships: {total_relationships}")
            logger.info(f"=" * 80)

            return {
                "success": True,
                "total_documents": len(doc_ids),
                "processed": processed,
                "failed": failed,
                "total_entities": total_entities,
                "total_relationships": total_relationships
            }

    async def get_entity_stats(self) -> Dict:
        """
        엔티티 통계 조회

        Returns:
            엔티티 통계
        """
        async with AsyncSessionLocal() as db:
            # 전체 엔티티 수
            query = text("SELECT COUNT(*) FROM knowledge_entities")
            result = await db.execute(query)
            total_entities = result.scalar()

            # 타입별 엔티티 수
            query = text("""
                SELECT type, COUNT(*) as count
                FROM knowledge_entities
                GROUP BY type
                ORDER BY count DESC
            """)
            result = await db.execute(query)
            type_counts = {row[0]: row[1] for row in result.fetchall()}

            # 전체 관계 수
            query = text("SELECT COUNT(*) FROM knowledge_relationships")
            result = await db.execute(query)
            total_relationships = result.scalar()

            # 관계 타입별 수
            query = text("""
                SELECT type, COUNT(*) as count
                FROM knowledge_relationships
                GROUP BY type
                ORDER BY count DESC
            """)
            result = await db.execute(query)
            rel_type_counts = {row[0]: row[1] for row in result.fetchall()}

            # 보험사별 엔티티 수
            query = text("""
                SELECT insurer, COUNT(*) as count
                FROM knowledge_entities
                GROUP BY insurer
                ORDER BY count DESC
            """)
            result = await db.execute(query)
            insurer_counts = {row[0]: row[1] for row in result.fetchall()}

            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "entity_types": type_counts,
                "relationship_types": rel_type_counts,
                "insurers": insurer_counts
            }


# 전역 인스턴스
doc_processor = DocumentEntityProcessor()
