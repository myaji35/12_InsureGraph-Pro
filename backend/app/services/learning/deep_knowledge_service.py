"""
Deep Knowledge Service

SmartLearner와 GraphRAG Entity Extractor를 연결하여
문서에서 깊이 있는 지식 그래프를 구축합니다.
"""
from typing import Dict, List
from loguru import logger
from sqlalchemy import text

from .graphrag_entity_extractor import GraphRAGEntityExtractor
from app.core.database import AsyncSessionLocal


class DeepKnowledgeService:
    """
    깊이 있는 지식 그래프 구축 서비스

    SmartLearner의 chunk_learning_callback으로 사용되어
    각 청크에서 엔티티와 관계를 추출하고 PostgreSQL에 저장합니다.
    """

    def __init__(self):
        self.extractor = GraphRAGEntityExtractor()
        self.stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "chunks_processed": 0,
            "errors": 0
        }

    async def process_and_extract(
        self,
        chunk_text: str,
        document_id: str,
        chunk_id: str,
        document_info: Dict
    ) -> Dict:
        """
        청크에서 엔티티 추출 및 저장

        Args:
            chunk_text: 청크 텍스트
            document_id: 문서 ID
            chunk_id: 청크 ID
            document_info: {insurer, product_type, title}

        Returns:
            추출 결과 통계
        """
        try:
            # 엔티티 추출
            result = await self.extractor.extract_entities_and_relationships(
                text=chunk_text,
                document_info=document_info,
                chunk_id=chunk_id
            )

            if result.get("error"):
                logger.error(f"[{document_id[:8]}] Entity extraction error: {result['error']}")
                self.stats["errors"] += 1
                return result

            # PostgreSQL에 저장
            entities_saved = await self._save_entities(
                entities=result["entities"],
                document_id=document_id
            )

            relationships_saved = await self._save_relationships(
                relationships=result["relationships"],
                document_id=document_id
            )

            # 통계 업데이트
            self.stats["total_entities"] += entities_saved
            self.stats["total_relationships"] += relationships_saved
            self.stats["chunks_processed"] += 1

            logger.info(
                f"[{document_id[:8]}] Chunk {chunk_id}: "
                f"{entities_saved} entities, {relationships_saved} relationships saved"
            )

            return {
                "entities": entities_saved,
                "relationships": relationships_saved,
                "chunk_hash": result.get("chunk_id", chunk_id),
                "nodes_by_type": result.get("entity_type_counts", {}),
                "relationships_by_type": result.get("relationship_type_counts", {})
            }

        except Exception as e:
            logger.error(f"[{document_id[:8]}] Failed to process chunk {chunk_id}: {e}", exc_info=True)
            self.stats["errors"] += 1
            return {
                "entities": 0,
                "relationships": 0,
                "error": str(e)
            }

    async def _save_entities(self, entities: List[Dict], document_id: str) -> int:
        """엔티티를 PostgreSQL에 저장"""
        if not entities:
            return 0

        saved_count = 0
        async with AsyncSessionLocal() as db:
            for entity in entities:
                try:
                    # INSERT ... ON CONFLICT DO UPDATE 사용
                    query = text("""
                        INSERT INTO knowledge_entities (
                            entity_id, label, type, description, source_text,
                            document_id, chunk_id, insurer, product_type, metadata
                        ) VALUES (
                            :entity_id, :label, :type, :description, :source_text,
                            :document_id, :chunk_id, :insurer, :product_type, :metadata::jsonb
                        )
                        ON CONFLICT (entity_id) DO UPDATE SET
                            label = EXCLUDED.label,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """)

                    doc_info = entity.get("document_info", {})

                    await db.execute(query, {
                        "entity_id": entity["id"],
                        "label": entity.get("label", ""),
                        "type": entity.get("type", "unknown"),
                        "description": entity.get("description"),
                        "source_text": entity.get("source_text"),
                        "document_id": document_id,
                        "chunk_id": entity.get("chunk_id"),
                        "insurer": doc_info.get("insurer"),
                        "product_type": doc_info.get("product_type"),
                        "metadata": "{}"
                    })
                    saved_count += 1

                except Exception as e:
                    logger.error(f"Failed to save entity {entity.get('id')}: {e}")
                    continue

            await db.commit()

        return saved_count

    async def _save_relationships(self, relationships: List[Dict], document_id: str) -> int:
        """관계를 PostgreSQL에 저장"""
        if not relationships:
            return 0

        saved_count = 0
        async with AsyncSessionLocal() as db:
            for rel in relationships:
                try:
                    query = text("""
                        INSERT INTO knowledge_relationships (
                            source_entity_id, target_entity_id, type, description,
                            document_id, chunk_id, metadata
                        ) VALUES (
                            :source_entity_id, :target_entity_id, :type, :description,
                            :document_id, :chunk_id, :metadata::jsonb
                        )
                        ON CONFLICT DO NOTHING
                    """)

                    await db.execute(query, {
                        "source_entity_id": rel.get("source_id"),
                        "target_entity_id": rel.get("target_id"),
                        "type": rel.get("type", "unknown"),
                        "description": rel.get("description"),
                        "document_id": document_id,
                        "chunk_id": rel.get("chunk_id"),
                        "metadata": "{}"
                    })
                    saved_count += 1

                except Exception as e:
                    logger.error(f"Failed to save relationship: {e}")
                    continue

            await db.commit()

        return saved_count

    def get_stats(self) -> Dict:
        """통계 반환"""
        return self.stats.copy()

    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "chunks_processed": 0,
            "errors": 0
        }
