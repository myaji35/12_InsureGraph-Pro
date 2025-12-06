"""
관계 강화 서비스

추출된 엔티티를 기반으로 추가 관계를 생성하여 그래프 연결성을 높입니다.
"""
from typing import List, Dict, Set
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text


class RelationshipEnhancer:
    """
    규칙 기반으로 추가 관계를 생성하여 그래프의 연결성을 높이는 서비스
    """

    def __init__(self, db: Session):
        self.db = db

    def enhance_relationships(self, document_id: str) -> Dict:
        """
        문서의 엔티티 간 추가 관계 생성

        Args:
            document_id: 문서 ID

        Returns:
            생성된 관계 통계
        """
        logger.info(f"문서 {document_id}의 관계 강화 시작")

        stats = {
            "article_proximity": 0,
            "same_type_in_article": 0,
            "coverage_benefit_link": 0,
            "sequential_articles": 0,
            "total_created": 0
        }

        # 1. 같은 조항 내 엔티티 연결
        stats["article_proximity"] = self._link_entities_in_same_article(document_id)

        # 2. 같은 타입의 엔티티 간 연결 (조항 기준)
        stats["same_type_in_article"] = self._link_same_type_entities(document_id)

        # 3. 보장항목-보험금액 연결 강화
        stats["coverage_benefit_link"] = self._link_coverage_to_amounts(document_id)

        # 4. 순차적 조항 간 연결
        stats["sequential_articles"] = self._link_sequential_articles(document_id)

        stats["total_created"] = sum([
            stats["article_proximity"],
            stats["same_type_in_article"],
            stats["coverage_benefit_link"],
            stats["sequential_articles"]
        ])

        logger.info(f"관계 강화 완료: {stats['total_created']}개 관계 생성")
        return stats

    def _link_entities_in_same_article(self, document_id: str) -> int:
        """
        같은 약관 조항 내의 엔티티들을 'mentioned_with' 관계로 연결
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'mentioned_with',
                '같은 조항에서 함께 언급됨',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON e1.document_id = e2.document_id
            WHERE e1.document_id = :document_id
            AND e1.entity_id < e2.entity_id  -- 중복 방지
            AND e1.metadata->>'article_number' = e2.metadata->>'article_number'
            AND e1.metadata->>'article_number' IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE kr.source_entity_id = e1.entity_id
                AND kr.target_entity_id = e2.entity_id
            )
            ON CONFLICT DO NOTHING
        """)

        result = self.db.execute(query, {"document_id": document_id})
        self.db.commit()
        return result.rowcount

    def _link_same_type_entities(self, document_id: str) -> int:
        """
        같은 타입의 엔티티들을 'related_to' 관계로 연결 (근접 엔티티만)
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'related_to',
                '같은 유형의 관련 항목',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON e1.document_id = e2.document_id
            WHERE e1.document_id = :document_id
            AND e1.entity_id < e2.entity_id
            AND e1.type = e2.type
            AND e1.type IN ('coverage_item', 'benefit_amount', 'period', 'exclusion', 'article')
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE (kr.source_entity_id = e1.entity_id AND kr.target_entity_id = e2.entity_id)
                OR (kr.source_entity_id = e2.entity_id AND kr.target_entity_id = e1.entity_id)
            )
            LIMIT 300
            ON CONFLICT DO NOTHING
        """)

        result = self.db.execute(query, {"document_id": document_id})
        self.db.commit()
        return result.rowcount

    def _link_coverage_to_amounts(self, document_id: str) -> int:
        """
        보장항목과 인근의 보험금액을 연결
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                coverage.entity_id,
                amount.entity_id,
                'has_amount',
                '보장 금액',
                coverage.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities coverage
            JOIN knowledge_entities amount ON coverage.document_id = amount.document_id
            WHERE coverage.document_id = :document_id
            AND coverage.type = 'coverage_item'
            AND amount.type = 'benefit_amount'
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE kr.source_entity_id = coverage.entity_id
                AND kr.target_entity_id = amount.entity_id
                AND kr.type = 'has_amount'
            )
            LIMIT 100
            ON CONFLICT DO NOTHING
        """)

        result = self.db.execute(query, {"document_id": document_id})
        self.db.commit()
        return result.rowcount

    def _link_sequential_articles(self, document_id: str) -> int:
        """
        순차적인 약관 조항들을 'follows' 관계로 연결
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'follows',
                '다음 조항',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON e1.document_id = e2.document_id
            WHERE e1.document_id = :document_id
            AND e1.type = 'article'
            AND e2.type = 'article'
            AND e1.id < e2.id  -- 생성 순서 기반
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE kr.source_entity_id = e1.entity_id
                AND kr.target_entity_id = e2.entity_id
            )
            LIMIT 50
            ON CONFLICT DO NOTHING
        """)

        result = self.db.execute(query, {"document_id": document_id})
        self.db.commit()
        return result.rowcount

    def enhance_all_relationships_for_insurer(self, insurer: str) -> Dict:
        """
        특정 보험사의 모든 완료된 문서에 대해 관계 강화
        """
        # 완료된 문서 ID 조회
        result = self.db.execute(text("""
            SELECT id FROM crawler_documents
            WHERE insurer = :insurer
            AND status = 'completed'
        """), {"insurer": insurer})

        document_ids = [row[0] for row in result.fetchall()]

        total_stats = {
            "documents_processed": 0,
            "total_relationships_created": 0,
            "article_proximity": 0,
            "same_type_in_article": 0,
            "coverage_benefit_link": 0,
            "sequential_articles": 0
        }

        for doc_id in document_ids:
            try:
                stats = self.enhance_relationships(str(doc_id))
                total_stats["documents_processed"] += 1
                total_stats["total_relationships_created"] += stats["total_created"]
                total_stats["article_proximity"] += stats["article_proximity"]
                total_stats["same_type_in_article"] += stats["same_type_in_article"]
                total_stats["coverage_benefit_link"] += stats["coverage_benefit_link"]
                total_stats["sequential_articles"] += stats["sequential_articles"]
            except Exception as e:
                logger.error(f"문서 {doc_id} 관계 강화 실패: {e}")
                continue

        return total_stats

    async def link_cross_document_entities(self, insurer: str) -> int:
        """
        개선방안 1: 같은 보험사의 문서 간 유사한 엔티티 연결
        같은 보장항목, 같은 보험금액 등을 문서 간에 연결
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'similar_across_documents',
                '다른 문서의 유사 항목',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON
                e1.insurer = e2.insurer
                AND e1.type = e2.type
                AND e1.label = e2.label
                AND e1.document_id != e2.document_id
            WHERE e1.insurer = :insurer
            AND e1.entity_id < e2.entity_id
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE (kr.source_entity_id = e1.entity_id AND kr.target_entity_id = e2.entity_id)
                OR (kr.source_entity_id = e2.entity_id AND kr.target_entity_id = e1.entity_id)
            )
            LIMIT 500
            ON CONFLICT DO NOTHING
        """)

        result = await self.db.execute(query, {"insurer": insurer})
        await self.db.commit()
        logger.info(f"문서 간 유사 엔티티 연결: {result.rowcount}개")
        return result.rowcount

    async def link_all_entities_by_type(self, insurer: str) -> int:
        """
        개선방안 2: 같은 타입의 모든 엔티티를 연결 (LIMIT 대폭 증가)
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'type_cluster',
                '같은 타입 클러스터',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON
                e1.insurer = e2.insurer
                AND e1.type = e2.type
            WHERE e1.insurer = :insurer
            AND e1.entity_id < e2.entity_id
            AND e1.type IN ('coverage_item', 'benefit_amount', 'period', 'exclusion', 'article', 'rider')
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE (kr.source_entity_id = e1.entity_id AND kr.target_entity_id = e2.entity_id)
                OR (kr.source_entity_id = e2.entity_id AND kr.target_entity_id = e1.entity_id)
            )
            LIMIT 2000
            ON CONFLICT DO NOTHING
        """)

        result = await self.db.execute(query, {"insurer": insurer})
        await self.db.commit()
        logger.info(f"타입별 클러스터 연결: {result.rowcount}개")
        return result.rowcount

    async def link_entities_by_label_similarity(self, insurer: str) -> int:
        """
        개선방안 3: 레이블 유사도 기반 연결 (부분 일치)
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'semantically_related',
                '의미적으로 연관된 항목',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            JOIN knowledge_entities e2 ON
                e1.insurer = e2.insurer
                AND e1.entity_id < e2.entity_id
                AND (
                    e1.label ILIKE '%' || e2.label || '%'
                    OR e2.label ILIKE '%' || e1.label || '%'
                )
            WHERE e1.insurer = :insurer
            AND LENGTH(e1.label) > 3
            AND LENGTH(e2.label) > 3
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE (kr.source_entity_id = e1.entity_id AND kr.target_entity_id = e2.entity_id)
                OR (kr.source_entity_id = e2.entity_id AND kr.target_entity_id = e1.entity_id)
            )
            LIMIT 1000
            ON CONFLICT DO NOTHING
        """)

        result = await self.db.execute(query, {"insurer": insurer})
        await self.db.commit()
        logger.info(f"레이블 유사도 기반 연결: {result.rowcount}개")
        return result.rowcount

    async def create_hub_nodes(self, insurer: str) -> int:
        """
        개선방안 4: 허브 노드 생성 - 각 문서를 허브로 하여 문서 내 모든 엔티티 연결
        """
        query = text("""
            INSERT INTO knowledge_relationships (
                relationship_id,
                source_entity_id,
                target_entity_id,
                type,
                description,
                document_id,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text,
                e1.entity_id,
                e2.entity_id,
                'in_same_document',
                '같은 문서에 속함',
                e1.document_id,
                NOW(),
                NOW()
            FROM knowledge_entities e1
            CROSS JOIN knowledge_entities e2
            WHERE e1.insurer = :insurer
            AND e1.document_id = e2.document_id
            AND e1.entity_id < e2.entity_id
            AND NOT EXISTS (
                SELECT 1 FROM knowledge_relationships kr
                WHERE (kr.source_entity_id = e1.entity_id AND kr.target_entity_id = e2.entity_id)
                OR (kr.source_entity_id = e2.entity_id AND kr.target_entity_id = e1.entity_id)
            )
            LIMIT 3000
            ON CONFLICT DO NOTHING
        """)

        result = await self.db.execute(query, {"insurer": insurer})
        await self.db.commit()
        logger.info(f"문서 허브 기반 연결: {result.rowcount}개")
        return result.rowcount

    async def apply_all_enhancements(self, insurer: str) -> Dict:
        """
        모든 개선방안을 순차적으로 적용
        """
        logger.info(f"=== {insurer} 그래프 관계 강화 시작 ===")

        stats = {
            "cross_document": 0,
            "type_cluster": 0,
            "label_similarity": 0,
            "hub_nodes": 0,
            "total": 0
        }

        # 개선방안 1: 문서 간 유사 엔티티 연결
        stats["cross_document"] = await self.link_cross_document_entities(insurer)

        # 개선방안 2: 타입별 전체 연결
        stats["type_cluster"] = await self.link_all_entities_by_type(insurer)

        # 개선방안 3: 레이블 유사도 기반 연결
        stats["label_similarity"] = await self.link_entities_by_label_similarity(insurer)

        # 개선방안 4: 문서 허브 노드 생성
        stats["hub_nodes"] = await self.create_hub_nodes(insurer)

        stats["total"] = sum([
            stats["cross_document"],
            stats["type_cluster"],
            stats["label_similarity"],
            stats["hub_nodes"]
        ])

        logger.info(f"=== 총 {stats['total']}개의 관계 생성 완료 ===")
        return stats
