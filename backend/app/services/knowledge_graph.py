"""
Knowledge Graph Service

Neo4j를 사용하여 보험 약관 지식 그래프를 생성하고 관리합니다.
"""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime

from loguru import logger
from neo4j import AsyncSession

from app.services.pdf_processor import Article, ExtractedEntity


class KnowledgeGraphService:
    """Neo4j 지식 그래프 서비스"""

    def __init__(self, session: AsyncSession):
        """
        Initialize knowledge graph service

        Args:
            session: Neo4j async session
        """
        self.session = session

    async def create_document_graph(
        self,
        document_id: UUID,
        insurer: str,
        product_name: str,
        product_code: Optional[str],
        articles: List[Article],
        entities: List[ExtractedEntity]
    ) -> Dict:
        """
        문서의 지식 그래프 생성

        Args:
            document_id: 문서 ID
            insurer: 보험사명
            product_name: 상품명
            product_code: 상품코드
            articles: 조항 목록
            entities: 추출된 엔티티 목록

        Returns:
            Dict: 생성된 노드 및 관계 통계
        """
        logger.info(f"Creating knowledge graph for document {document_id}")

        # 통계
        stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "node_types": {},
            "relationship_types": {}
        }

        # 1. 문서 노드 생성
        await self._create_document_node(document_id, insurer, product_name, product_code)
        stats["nodes_created"] += 1
        stats["node_types"]["Document"] = 1

        # 2. 조항 노드 생성 및 문서와 연결
        for article in articles:
            await self._create_article_node(document_id, article)
            stats["nodes_created"] += 1
            stats["node_types"]["Article"] = stats["node_types"].get("Article", 0) + 1
            stats["relationships_created"] += 1
            stats["relationship_types"]["HAS_ARTICLE"] = stats["relationship_types"].get("HAS_ARTICLE", 0) + 1

        # 3. 엔티티 노드 생성 및 조항과 연결
        for entity in entities:
            node_created = await self._create_entity_node(document_id, entity)
            if node_created:
                stats["nodes_created"] += 1
                stats["node_types"][entity.entity_type] = stats["node_types"].get(entity.entity_type, 0) + 1
                stats["relationships_created"] += 1
                stats["relationship_types"]["EXTRACTED_FROM"] = stats["relationship_types"].get("EXTRACTED_FROM", 0) + 1

        # 4. 엔티티 간 관계 추론 (같은 조항 내에서)
        relationship_count = await self._create_entity_relationships(document_id, entities)
        stats["relationships_created"] += relationship_count
        stats["relationship_types"]["RELATED_TO"] = relationship_count

        logger.info(f"Knowledge graph created: {stats}")
        return stats

    async def _create_document_node(
        self,
        document_id: UUID,
        insurer: str,
        product_name: str,
        product_code: Optional[str]
    ):
        """문서 노드 생성"""
        query = """
        MERGE (d:Document {document_id: $document_id})
        SET d.insurer = $insurer,
            d.product_name = $product_name,
            d.product_code = $product_code,
            d.created_at = datetime($created_at),
            d.updated_at = datetime($updated_at)
        RETURN d
        """

        await self.session.run(
            query,
            document_id=str(document_id),
            insurer=insurer,
            product_name=product_name,
            product_code=product_code,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        logger.debug(f"Document node created: {document_id}")

    async def _create_article_node(self, document_id: UUID, article: Article):
        """조항 노드 생성 및 문서와 연결"""
        query = """
        MATCH (d:Document {document_id: $document_id})
        MERGE (a:Article {
            document_id: $document_id,
            article_num: $article_num
        })
        SET a.title = $title,
            a.content = $content,
            a.page = $page,
            a.paragraph_count = $paragraph_count,
            a.created_at = datetime($created_at)
        MERGE (d)-[:HAS_ARTICLE]->(a)
        RETURN a
        """

        await self.session.run(
            query,
            document_id=str(document_id),
            article_num=article.article_num,
            title=article.title,
            content=article.content[:1000],  # 긴 내용은 잘라서 저장
            page=article.page,
            paragraph_count=len(article.paragraphs),
            created_at=datetime.now().isoformat()
        )

        logger.debug(f"Article node created: {article.article_num}")

    async def _create_entity_node(self, document_id: UUID, entity: ExtractedEntity) -> bool:
        """
        엔티티 노드 생성 및 조항과 연결

        Returns:
            bool: 새로운 노드가 생성되었는지 여부
        """
        # 엔티티 타입별로 다른 레이블 사용
        label = self._get_entity_label(entity.entity_type)

        query = f"""
        MATCH (a:Article {{document_id: $document_id, article_num: $article_num}})
        MERGE (e:{label} {{
            document_id: $document_id,
            entity_name: $entity_name
        }})
        ON CREATE SET
            e.entity_type = $entity_type,
            e.description = $description,
            e.confidence = $confidence,
            e.created_at = datetime($created_at)
        MERGE (e)-[:EXTRACTED_FROM]->(a)
        RETURN e
        """

        result = await self.session.run(
            query,
            document_id=str(document_id),
            article_num=entity.source_article,
            entity_name=entity.entity_name,
            entity_type=entity.entity_type,
            description=entity.description,
            confidence=entity.confidence,
            created_at=datetime.now().isoformat()
        )

        record = await result.single()
        return record is not None

    async def _create_entity_relationships(
        self,
        document_id: UUID,
        entities: List[ExtractedEntity]
    ) -> int:
        """
        엔티티 간 관계 생성

        같은 조항에서 추출된 엔티티들을 연결합니다.

        Returns:
            int: 생성된 관계 수
        """
        # 조항별로 엔티티 그룹화
        entities_by_article = {}
        for entity in entities:
            article_num = entity.source_article
            if article_num not in entities_by_article:
                entities_by_article[article_num] = []
            entities_by_article[article_num].append(entity)

        relationship_count = 0

        # 각 조항 내에서 엔티티 간 관계 생성
        for article_num, article_entities in entities_by_article.items():
            # COVERAGE와 CONDITION/REQUIREMENT를 연결
            coverages = [e for e in article_entities if e.entity_type == "COVERAGE"]
            conditions = [e for e in article_entities if e.entity_type in ["CONDITION", "REQUIREMENT"]]
            benefits = [e for e in article_entities if e.entity_type == "BENEFIT"]
            exclusions = [e for e in article_entities if e.entity_type == "EXCLUSION"]

            # COVERAGE -[:HAS_CONDITION]-> CONDITION
            for coverage in coverages:
                for condition in conditions:
                    await self._link_entities(
                        document_id, coverage, condition, "HAS_CONDITION"
                    )
                    relationship_count += 1

            # COVERAGE -[:HAS_BENEFIT]-> BENEFIT
            for coverage in coverages:
                for benefit in benefits:
                    await self._link_entities(
                        document_id, coverage, benefit, "HAS_BENEFIT"
                    )
                    relationship_count += 1

            # COVERAGE -[:HAS_EXCLUSION]-> EXCLUSION
            for coverage in coverages:
                for exclusion in exclusions:
                    await self._link_entities(
                        document_id, coverage, exclusion, "HAS_EXCLUSION"
                    )
                    relationship_count += 1

        logger.debug(f"Created {relationship_count} entity relationships")
        return relationship_count

    async def _link_entities(
        self,
        document_id: UUID,
        entity1: ExtractedEntity,
        entity2: ExtractedEntity,
        relationship_type: str
    ):
        """두 엔티티 사이에 관계 생성"""
        label1 = self._get_entity_label(entity1.entity_type)
        label2 = self._get_entity_label(entity2.entity_type)

        query = f"""
        MATCH (e1:{label1} {{document_id: $document_id, entity_name: $entity1_name}})
        MATCH (e2:{label2} {{document_id: $document_id, entity_name: $entity2_name}})
        MERGE (e1)-[r:{relationship_type}]->(e2)
        ON CREATE SET r.created_at = datetime($created_at)
        RETURN r
        """

        await self.session.run(
            query,
            document_id=str(document_id),
            entity1_name=entity1.entity_name,
            entity2_name=entity2.entity_name,
            created_at=datetime.now().isoformat()
        )

    def _get_entity_label(self, entity_type: str) -> str:
        """엔티티 타입에 따른 Neo4j 레이블 반환"""
        # 모든 엔티티는 Entity 레이블도 가짐 (다중 레이블)
        labels = {
            "COVERAGE": "Coverage",
            "EXCLUSION": "Exclusion",
            "CONDITION": "Condition",
            "TERM": "Term",
            "BENEFIT": "Benefit",
            "REQUIREMENT": "Requirement",
        }
        return labels.get(entity_type, "Entity")

    async def delete_document_graph(self, document_id: UUID) -> int:
        """
        문서의 지식 그래프 삭제

        Args:
            document_id: 문서 ID

        Returns:
            int: 삭제된 노드 수
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[*]-(related)
        DETACH DELETE d, related
        RETURN count(d) + count(related) as deleted_count
        """

        result = await self.session.run(query, document_id=str(document_id))
        record = await result.single()
        deleted_count = record["deleted_count"] if record else 0

        logger.info(f"Deleted {deleted_count} nodes for document {document_id}")
        return deleted_count

    async def get_document_stats(self, document_id: UUID) -> Dict:
        """
        문서의 지식 그래프 통계 조회

        Args:
            document_id: 문서 ID

        Returns:
            Dict: 노드 및 관계 통계
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[:HAS_ARTICLE]->(a:Article)
        OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(a)
        RETURN
            count(DISTINCT a) as article_count,
            count(DISTINCT e) as entity_count,
            labels(e) as entity_labels
        """

        result = await self.session.run(query, document_id=str(document_id))
        record = await result.single()

        if not record:
            return {
                "article_count": 0,
                "entity_count": 0,
                "entity_types": {}
            }

        return {
            "article_count": record["article_count"],
            "entity_count": record["entity_count"],
            "entity_types": {}  # Can be expanded to count by type
        }

    async def search_entities(
        self,
        document_id: UUID,
        entity_type: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        엔티티 검색

        Args:
            document_id: 문서 ID
            entity_type: 엔티티 타입 필터
            search_text: 검색 텍스트
            limit: 최대 결과 수

        Returns:
            List[Dict]: 엔티티 목록
        """
        # 기본 쿼리
        where_clauses = ["e.document_id = $document_id"]
        params = {"document_id": str(document_id), "limit": limit}

        if entity_type:
            where_clauses.append("e.entity_type = $entity_type")
            params["entity_type"] = entity_type

        if search_text:
            where_clauses.append(
                "(e.entity_name CONTAINS $search_text OR e.description CONTAINS $search_text)"
            )
            params["search_text"] = search_text

        where_clause = " AND ".join(where_clauses)

        query = f"""
        MATCH (e)
        WHERE {where_clause}
        OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(a:Article)
        RETURN e, a
        LIMIT $limit
        """

        result = await self.session.run(query, **params)
        records = await result.data()

        entities = []
        for record in records:
            entity_node = record["e"]
            article_node = record.get("a")

            entities.append({
                "entity_name": entity_node.get("entity_name"),
                "entity_type": entity_node.get("entity_type"),
                "description": entity_node.get("description"),
                "confidence": entity_node.get("confidence"),
                "source_article": article_node.get("article_num") if article_node else None,
            })

        return entities


async def create_knowledge_graph(
    session: AsyncSession,
    document_id: UUID,
    insurer: str,
    product_name: str,
    product_code: Optional[str],
    articles: List[Article],
    entities: List[ExtractedEntity]
) -> Dict:
    """
    지식 그래프 생성 헬퍼 함수

    Args:
        session: Neo4j async session
        document_id: 문서 ID
        insurer: 보험사명
        product_name: 상품명
        product_code: 상품코드
        articles: 조항 목록
        entities: 추출된 엔티티 목록

    Returns:
        Dict: 생성 통계
    """
    service = KnowledgeGraphService(session)
    return await service.create_document_graph(
        document_id, insurer, product_name, product_code, articles, entities
    )
