"""
완료된 문서를 위한 샘플 그래프 생성

완료된 문서들을 즉시 시각화할 수 있도록 간단한 그래프를 생성합니다.
"""
import asyncio
import sys
sys.path.append("/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend")

from sqlalchemy import text
from loguru import logger
from app.core.database import AsyncSessionLocal


async def generate_sample_graph_from_completed_documents():
    """완료된 문서들로 샘플 그래프 생성"""

    async with AsyncSessionLocal() as db:
        # 1. 완료된 문서 조회
        query = text("""
            SELECT id, insurer, product_type, title, processing_detail
            FROM crawler_documents
            WHERE status = 'completed'
            ORDER BY updated_at DESC
        """)

        result = await db.execute(query)
        completed_docs = result.fetchall()

        if not completed_docs:
            logger.info("No completed documents found")
            return

        logger.info(f"Found {len(completed_docs)} completed documents")

        # 2. 샘플 노드와 엣지 생성
        nodes = []
        edges = []

        # 보험사 노드 생성 (중복 제거)
        insurers = {}
        for doc in completed_docs:
            insurer = doc[1]
            if insurer not in insurers:
                insurers[insurer] = {
                    "id": f"insurer_{len(insurers)}",
                    "label": insurer,
                    "type": "insurer",
                    "color": "#3b82f6",
                    "size": 30
                }

        nodes.extend(insurers.values())

        # 문서 노드 생성 및 보험사와 연결
        for i, doc in enumerate(completed_docs):
            doc_id = doc[0]
            insurer = doc[1]
            product_type = doc[2]
            title = doc[3][:50]  # 제목 50자 제한

            # 문서 노드
            doc_node = {
                "id": f"doc_{doc_id}",
                "label": f"{product_type}\n{title}",
                "type": "document",
                "color": "#10b981",
                "size": 15,
                "metadata": {
                    "insurer": insurer,
                    "product_type": product_type,
                    "title": title
                }
            }
            nodes.append(doc_node)

            # 보험사 -> 문서 엣지
            edges.append({
                "id": f"edge_{i}_insurer",
                "source": insurers[insurer]["id"],
                "target": f"doc_{doc_id}",
                "label": "제공",
                "type": "provides"
            })

        # 3. 그래프 데이터를 JSON으로 저장
        import json
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_documents": len(completed_docs),
                "total_insurers": len(insurers),
                "generated_at": "2025-12-02T11:25:00Z"
            }
        }

        # 파일로 저장
        output_path = "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/sample_graph.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Sample graph generated:")
        logger.info(f"  - Nodes: {len(nodes)}")
        logger.info(f"  - Edges: {len(edges)}")
        logger.info(f"  - Insurers: {len(insurers)}")
        logger.info(f"  - Documents: {len(completed_docs)}")
        logger.info(f"  - Saved to: {output_path}")

        return graph_data


if __name__ == "__main__":
    asyncio.run(generate_sample_graph_from_completed_documents())
