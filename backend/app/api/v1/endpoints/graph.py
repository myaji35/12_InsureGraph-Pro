"""
Graph API Endpoints

Neo4j 지식 그래프 데이터를 조회하는 API
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from neo4j import GraphDatabase
import os

router = APIRouter(prefix="/graph", tags=["Graph"])

# Neo4j 연결
def get_neo4j_driver():
    """Neo4j 드라이버 생성"""
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "change-me-in-production")
        )
    )


@router.get(
    "",
    summary="그래프 데이터 조회",
    description="Neo4j에서 노드와 관계를 조회하여 그래프 데이터를 반환합니다."
)
async def get_graph(
    document_ids: Optional[List[str]] = Query(None),
    node_types: Optional[List[str]] = Query(None),
    max_nodes: int = Query(200, ge=1, le=1000)
):
    """
    그래프 데이터 조회
    
    Args:
        document_ids: 필터링할 문서 ID 리스트
        node_types: 필터링할 노드 타입 리스트
        max_nodes: 최대 노드 개수
        
    Returns:
        GraphData: 노드와 엣지 데이터
    """
    driver = get_neo4j_driver()
    
    try:
        with driver.session() as session:
            # WHERE 절 동적 생성
            where_clauses = []
            params = {"max_nodes": max_nodes}

            # document_ids 필터링
            if document_ids:
                where_clauses.append("n.document_id IN $document_ids")
                params["document_ids"] = document_ids

            # node_types 필터링
            if node_types:
                # 노드 타입을 대문자로 변환 (Neo4j 레이블은 대문자 시작)
                formatted_types = [t.capitalize() for t in node_types]
                label_conditions = " OR ".join([f"n:{label}" for label in formatted_types])
                where_clauses.append(f"({label_conditions})")

            # WHERE 절 조합
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # 노드 조회
            cypher_query = f"""
            MATCH (n)
            {where_clause}
            RETURN
                id(n) as id,
                labels(n)[0] as type,
                CASE labels(n)[0]
                    WHEN 'Product' THEN COALESCE(n.product_name, n.name, 'Unknown Product')
                    WHEN 'Coverage' THEN COALESCE(n.coverage_name, n.name, 'Unknown Coverage')
                    WHEN 'Disease' THEN COALESCE(n.name_ko, n.name, 'Unknown Disease')
                    WHEN 'Condition' THEN COALESCE(n.description, n.name, 'Unknown Condition')
                    WHEN 'Clause' THEN COALESCE(n.article_title, n.name, 'Unknown Clause')
                    ELSE COALESCE(n.name, n.label, 'Unknown')
                END as label,
                properties(n) as properties
            LIMIT $max_nodes
            """

            result = session.run(cypher_query, **params)
            
            nodes = []
            node_ids = set()
            for record in result:
                node_id = str(record["id"])
                node_type = record["type"].lower() if record["type"] else "unknown"
                label = record["label"] or "Unknown"
                properties = record["properties"] or {}

                nodes.append({
                    "id": node_id,
                    "type": node_type,
                    "label": label,
                    "properties": properties,
                    "metadata": {
                        "document_id": properties.get("document_id"),
                        "document_name": properties.get("document_name")
                    }
                })
                node_ids.add(int(node_id))

            # 관계 조회 - 필터링된 노드 간의 관계만 가져오기
            edge_query = f"""
            MATCH (source)-[r]->(target)
            WHERE id(source) IN $node_ids AND id(target) IN $node_ids
            RETURN
                id(source) as source_id,
                id(target) as target_id,
                type(r) as relationship_type,
                properties(r) as properties
            """

            result = session.run(edge_query, node_ids=list(node_ids))

            edges = []
            for record in result:
                edges.append({
                    "id": f"{record['source_id']}-{record['target_id']}",
                    "source": str(record["source_id"]),
                    "target": str(record["target_id"]),
                    "type": record["relationship_type"].lower() if record["relationship_type"] else "unknown",
                    "label": record["relationship_type"] or "UNKNOWN",
                    "properties": record["properties"] or {}
                })

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "document_ids": document_ids,
                    "node_types": node_types,
                    "filters_applied": {
                        "document_ids": bool(document_ids),
                        "node_types": bool(node_types)
                    }
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GRAPH_QUERY_ERROR",
                "error_message": f"그래프 조회 중 오류가 발생했습니다: {str(e)}"
            }
        )
    finally:
        driver.close()


@router.get(
    "/nodes/{node_id}",
    summary="노드 상세 정보 조회"
)
async def get_node_details(node_id: str):
    """노드 상세 정보 조회"""
    driver = get_neo4j_driver()
    
    try:
        with driver.session() as session:
            cypher_query = """
            MATCH (n)
            WHERE id(n) = $node_id
            RETURN 
                id(n) as id,
                labels(n)[0] as type,
                properties(n) as properties
            """
            
            result = session.run(cypher_query, node_id=int(node_id))
            record = result.single()
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "NODE_NOT_FOUND",
                        "error_message": f"노드를 찾을 수 없습니다: {node_id}"
                    }
                )
            
            return {
                "id": str(record["id"]),
                "type": record["type"].lower() if record["type"] else "unknown",
                "properties": record["properties"] or {}
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "NODE_QUERY_ERROR",
                "error_message": f"노드 조회 중 오류가 발생했습니다: {str(e)}"
            }
        )
    finally:
        driver.close()
