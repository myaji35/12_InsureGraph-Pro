"""
실시간 그래프 업데이터

완료된 문서를 감지하여 자동으로 그래프를 업데이트합니다.
"""
import asyncio
import signal
import sys
import json
from datetime import datetime
from loguru import logger
from sqlalchemy import text

sys.path.append("/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend")
from app.core.database import AsyncSessionLocal


class GraphUpdaterWorker:
    """그래프 자동 업데이트 워커"""

    def __init__(self, check_interval: int = 10):
        """
        Args:
            check_interval: 체크 간격 (초)
        """
        self.check_interval = check_interval
        self.is_running = True
        self.last_completed_count = 0
        self.output_path = "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/sample_graph.json"

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """종료 시그널 처리"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.is_running = False

    async def get_completed_count(self) -> int:
        """완료된 문서 수 조회"""
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT COUNT(*) as count
                FROM crawler_documents
                WHERE status = 'completed'
            """)
            result = await db.execute(query)
            row = result.fetchone()
            return row[0] if row else 0

    async def generate_graph(self):
        """완료된 문서로 GraphRAG 스타일 지식 그래프 생성"""
        async with AsyncSessionLocal() as db:
            # 완료된 문서 조회
            query = text("""
                SELECT id, insurer, product_type, title, processing_detail, updated_at
                FROM crawler_documents
                WHERE status = 'completed'
                ORDER BY updated_at DESC
            """)

            result = await db.execute(query)
            completed_docs = result.fetchall()

            if not completed_docs:
                logger.warning("No completed documents found")
                return

            # 노드와 엣지 생성
            nodes = []
            edges = []

            # 보험사 노드 생성 (중복 제거)
            insurers = {}
            product_types = {}

            for doc in completed_docs:
                insurer = doc[1]
                product_type = doc[2]

                # 보험사 노드
                if insurer not in insurers:
                    insurers[insurer] = {
                        "id": f"insurer_{len(insurers)}",
                        "label": insurer,
                        "type": "insurer",
                        "color": "#3b82f6",
                        "size": 40
                    }

                # 상품 타입 노드
                type_key = f"{insurer}_{product_type}"
                if type_key not in product_types:
                    product_types[type_key] = {
                        "id": f"type_{len(product_types)}",
                        "label": product_type,
                        "type": "product_type",
                        "color": "#8b5cf6",
                        "size": 25,
                        "insurer": insurer
                    }

            nodes.extend(insurers.values())
            nodes.extend(product_types.values())

            # 문서 노드 생성 및 연결
            for i, doc in enumerate(completed_docs):
                doc_id = doc[0]
                insurer = doc[1]
                product_type = doc[2]
                title = doc[3][:50] if doc[3] else "Unknown"
                updated_at = doc[5]

                # 문서 노드
                doc_node = {
                    "id": f"doc_{doc_id}",
                    "label": f"{product_type[:15]}\n{title[:30]}",
                    "type": "document",
                    "color": "#10b981",
                    "size": 15,
                    "metadata": {
                        "insurer": insurer,
                        "product_type": product_type,
                        "title": title,
                        "updated_at": updated_at.isoformat() if updated_at else None
                    }
                }
                nodes.append(doc_node)

                # 보험사 -> 상품타입 엣지
                type_key = f"{insurer}_{product_type}"
                insurer_to_type_id = f"edge_i2t_{insurer}_{product_type}"
                if not any(e["id"] == insurer_to_type_id for e in edges):
                    edges.append({
                        "id": insurer_to_type_id,
                        "source": insurers[insurer]["id"],
                        "target": product_types[type_key]["id"],
                        "label": "제공",
                        "type": "provides"
                    })

                # 상품타입 -> 문서 엣지
                edges.append({
                    "id": f"edge_t2d_{i}",
                    "source": product_types[type_key]["id"],
                    "target": f"doc_{doc_id}",
                    "label": "포함",
                    "type": "contains"
                })

            # ========== 깊이 있는 엔티티 추가 (GraphRAG) ==========
            # knowledge_entities 테이블에서 모든 엔티티 조회
            entity_query = text("""
                SELECT entity_id, label, type, description, source_text,
                       document_id, insurer, product_type
                FROM knowledge_entities
                ORDER BY created_at DESC
            """)
            result = await db.execute(entity_query)
            entities = result.fetchall()

            # 엔티티 타입별 색상 정의
            entity_colors = {
                "coverage_item": "#ef4444",       # 빨강 (보장항목)
                "benefit_amount": "#f59e0b",      # 주황 (보험금액)
                "payment_condition": "#eab308",   # 노랑 (지급조건)
                "exclusion": "#dc2626",           # 진한 빨강 (면책사항)
                "deductible": "#fb923c",          # 연한 주황 (자기부담금)
                "rider": "#a855f7",               # 보라 (특약)
                "eligibility": "#06b6d4",         # 청록 (가입조건)
                "article": "#64748b",             # 회색 (약관조항)
                "term": "#475569",                # 진한 회색 (보험용어)
                "period": "#0ea5e9"               # 파랑 (기간)
            }

            logger.info(f"📊 Found {len(entities)} entities from knowledge_entities table")

            # 엔티티 노드 추가
            for entity in entities:
                entity_id = entity[0]
                label = entity[1]
                entity_type = entity[2]
                description = entity[3]
                source_text = entity[4]
                document_id = entity[5]
                ent_insurer = entity[6]
                ent_product_type = entity[7]

                entity_node = {
                    "id": entity_id,
                    "label": label[:30],  # 라벨 길이 제한
                    "type": entity_type,
                    "color": entity_colors.get(entity_type, "#64748b"),
                    "size": 20,
                    "metadata": {
                        "description": description[:100] if description else None,
                        "source_text": source_text[:100] if source_text else None,
                        "insurer": ent_insurer,
                        "product_type": ent_product_type,
                        "document_id": document_id
                    }
                }
                nodes.append(entity_node)

                # 엔티티 -> 문서 연결
                if document_id:
                    edges.append({
                        "id": f"edge_e2d_{entity_id}",
                        "source": entity_id,
                        "target": f"doc_{document_id}",
                        "label": "출처",
                        "type": "from_document"
                    })

            # knowledge_relationships 테이블에서 관계 조회
            rel_query = text("""
                SELECT source_entity_id, target_entity_id, type, description
                FROM knowledge_relationships
                ORDER BY created_at DESC
            """)
            result = await db.execute(rel_query)
            relationships = result.fetchall()

            logger.info(f"🔗 Found {len(relationships)} relationships from knowledge_relationships table")

            # 관계 엣지 추가
            for rel in relationships:
                source_id = rel[0]
                target_id = rel[1]
                rel_type = rel[2]
                rel_desc = rel[3]

                # 한글 라벨 매핑
                rel_labels = {
                    "provides": "제공",
                    "has_amount": "금액",
                    "requires": "조건",
                    "excludes": "면책",
                    "has_deductible": "자기부담금",
                    "includes_rider": "특약포함",
                    "defines": "정의",
                    "specified_in": "명시",
                    "has_eligibility": "가입조건",
                    "applies_to": "적용대상"
                }

                edges.append({
                    "id": f"edge_rel_{source_id}_{target_id}",
                    "source": source_id,
                    "target": target_id,
                    "label": rel_labels.get(rel_type, rel_type),
                    "type": rel_type
                })

            # 그래프 데이터 생성
            graph_data = {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_documents": len(completed_docs),
                    "total_insurers": len(insurers),
                    "total_product_types": len(product_types),
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }

            # 파일로 저장
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)

            # Neo4j에 저장
            try:
                from neo4j import GraphDatabase
                from app.core.config import settings

                driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )

                with driver.session() as session:
                    # 기존 데이터 삭제 (전체 재생성)
                    session.run("MATCH (n) DETACH DELETE n")

                    # 노드 생성 (동적 라벨 사용)
                    for node in nodes:
                        node_type = node.get("type", "unknown")

                        # 타입별 Neo4j 라벨 매핑
                        label_mapping = {
                            "insurer": "Insurer",
                            "product_type": "ProductType",
                            "document": "Document",
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

                        neo4j_label = label_mapping.get(node_type, "Entity")

                        # 동적으로 라벨을 지정하여 노드 생성
                        query = f"""
                            CREATE (n:{neo4j_label} {{
                                id: $id,
                                label: $label,
                                type: $type,
                                color: $color,
                                size: $size,
                                metadata: $metadata
                            }})
                        """

                        session.run(query, {
                            "id": node["id"],
                            "label": node["label"],
                            "type": node["type"],
                            "color": node["color"],
                            "size": node["size"],
                            "metadata": json.dumps(node.get("metadata", {}))
                        })

                    # 엣지(관계) 생성 (동적 관계 타입 사용)
                    for edge in edges:
                        edge_type = edge.get("type", "RELATES")

                        # 관계 타입별 Neo4j 라벨 매핑
                        rel_type_mapping = {
                            "provides": "PROVIDES",
                            "contains": "CONTAINS",
                            "has_amount": "HAS_AMOUNT",
                            "requires": "REQUIRES",
                            "excludes": "EXCLUDES",
                            "has_deductible": "HAS_DEDUCTIBLE",
                            "includes_rider": "INCLUDES_RIDER",
                            "defines": "DEFINES",
                            "specified_in": "SPECIFIED_IN",
                            "has_eligibility": "HAS_ELIGIBILITY",
                            "applies_to": "APPLIES_TO",
                            "from_document": "FROM_DOCUMENT"
                        }

                        neo4j_rel_type = rel_type_mapping.get(edge_type, "RELATES")

                        # ID로만 매칭 (라벨 무관)
                        query = f"""
                            MATCH (source {{id: $source_id}})
                            MATCH (target {{id: $target_id}})
                            CREATE (source)-[r:{neo4j_rel_type} {{
                                id: $id,
                                label: $label,
                                type: $type
                            }}]->(target)
                        """

                        session.run(query, {
                            "source_id": edge["source"],
                            "target_id": edge["target"],
                            "id": edge["id"],
                            "label": edge["label"],
                            "type": edge["type"]
                        })

                driver.close()
                logger.info(f"✅ Neo4j updated successfully")

            except Exception as neo_error:
                logger.error(f"❌ Failed to update Neo4j: {neo_error}")

            # 엔티티 타입별 집계
            entity_type_counts = {}
            for node in nodes:
                node_type = node.get("type", "unknown")
                entity_type_counts[node_type] = entity_type_counts.get(node_type, 0) + 1

            logger.info(f"✅ Graph updated:")
            logger.info(f"  - Total Nodes: {len(nodes)}")
            logger.info(f"    - Insurers: {len(insurers)}")
            logger.info(f"    - Product Types: {len(product_types)}")
            logger.info(f"    - Documents: {len(completed_docs)}")
            logger.info(f"    - Entities (GraphRAG): {len(entities)}")
            if entity_type_counts:
                logger.info(f"    - Entity Breakdown:")
                for etype, count in sorted(entity_type_counts.items()):
                    if etype not in ["insurer", "product_type", "document"]:
                        logger.info(f"      * {etype}: {count}")
            logger.info(f"  - Total Edges: {len(edges)}")
            logger.info(f"  - Last update: {graph_data['metadata']['last_update']}")

    async def run(self):
        """워커 실행"""
        logger.info("=" * 80)
        logger.info("🔄 Graph Updater Worker Started")
        logger.info(f"  - Check Interval: {self.check_interval}s")
        logger.info(f"  - Output Path: {self.output_path}")
        logger.info("=" * 80)

        # 초기 그래프 생성
        await self.generate_graph()
        self.last_completed_count = await self.get_completed_count()

        while self.is_running:
            try:
                # 현재 완료 문서 수 확인
                current_completed_count = await self.get_completed_count()

                logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"Completed documents: {current_completed_count} "
                          f"(previous: {self.last_completed_count})")

                # 완료 문서가 증가했으면 그래프 업데이트
                if current_completed_count > self.last_completed_count:
                    new_docs = current_completed_count - self.last_completed_count
                    logger.info(f"🔄 Updating graph (+{new_docs} new documents)...")

                    await self.generate_graph()
                    self.last_completed_count = current_completed_count

                    logger.info(f"✅ Graph updated successfully")
                else:
                    logger.info("⏸️  No new documents, skipping update")

                # 다음 체크까지 대기
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Worker error: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

        logger.info("=" * 80)
        logger.info("🛑 Graph Updater Worker Stopped")
        logger.info("=" * 80)


async def main():
    """메인 함수"""
    check_interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    worker = GraphUpdaterWorker(check_interval=check_interval)
    await worker.run()


if __name__ == "__main__":
    # 사용 예:
    # python worker_graph_updater.py 10
    # (10초 간격으로 체크)
    asyncio.run(main())
