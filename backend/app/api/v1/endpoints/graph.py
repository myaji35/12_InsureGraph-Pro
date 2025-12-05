"""
Graph API Endpoints

Neo4j 지식 그래프 데이터를 조회하는 API
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from app.core.database import neo4j_manager

router = APIRouter(prefix="/graph", tags=["Graph"])


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
    # Neo4j 연결 실패 시 sample_graph.json 사용
    import os
    import json
    sample_graph_path = "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/sample_graph.json"

    if not neo4j_manager.driver:
        # sample_graph.json 파일이 있으면 사용
        if os.path.exists(sample_graph_path):
            with open(sample_graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)

            # 필터링 적용
            filtered_nodes = graph_data.get("nodes", [])
            filtered_edges = graph_data.get("edges", [])

            if node_types:
                filtered_nodes = [n for n in filtered_nodes if n.get("type") in node_types]
                node_ids = {n["id"] for n in filtered_nodes}
                filtered_edges = [e for e in filtered_edges
                                 if e.get("source") in node_ids and e.get("target") in node_ids]

            # 최대 노드 수 제한
            filtered_nodes = filtered_nodes[:max_nodes]
            node_ids = {n["id"] for n in filtered_nodes}
            filtered_edges = [e for e in filtered_edges
                             if e.get("source") in node_ids and e.get("target") in node_ids]

            return {
                "nodes": filtered_nodes,
                "edges": filtered_edges,
                "metadata": graph_data.get("metadata", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error_code": "NEO4J_UNAVAILABLE",
                    "error_message": "Neo4j 연결이 초기화되지 않았고 샘플 그래프도 없습니다."
                }
            )

    # Neo4j가 연결되어 있는 경우에만 아래 코드 실행
    try:
        # Neo4j 드라이버가 있고 연결 가능한 경우 시도
        if neo4j_manager.driver:
            async with neo4j_manager.driver.session() as session:
                # WHERE 절 동적 생성
                where_clauses = []
                params = {"max_nodes": max_nodes}

                # node_types 필터링
                if node_types:
                    where_clauses.append("n.type IN $node_types")
                    params["node_types"] = node_types

                # WHERE 절 조합
                where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # 노드 조회 - 워커가 생성한 구조에 맞춤
                cypher_query = f"""
                MATCH (n:Node)
                {where_clause}
                RETURN
                    n.id as id,
                    n.type as type,
                    n.label as label,
                    n.color as color,
                    n.size as size,
                    n.metadata as metadata
                LIMIT $max_nodes
                """

                result = await session.run(cypher_query, **params)

                nodes = []
                node_id_map = {}  # id(node) -> n.id 매핑
                async for record in result:
                    node_custom_id = record["id"]
                    node_type = record["type"] or "unknown"
                    label = record["label"] or "Unknown"
                    color = record["color"] or "#6b7280"
                    size = record["size"] or 20

                    # metadata는 JSON 문자열로 저장되어 있을 수 있음
                    import json
                    metadata = record["metadata"]
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    elif metadata is None:
                        metadata = {}

                    nodes.append({
                        "id": node_custom_id,
                        "type": node_type,
                        "label": label,
                        "color": color,
                        "size": size,
                        "metadata": metadata
                    })

                # id 리스트 생성 (관계 쿼리용)
                node_ids = [n["id"] for n in nodes]

                # 관계 조회 - 워커가 생성한 구조에 맞춤
                if node_ids:
                    edge_query = """
                    MATCH (source:Node)-[r:RELATES]->(target:Node)
                    WHERE source.id IN $node_ids AND target.id IN $node_ids
                    RETURN
                        source.id as source_id,
                        target.id as target_id,
                        r.id as rel_id,
                        r.label as rel_label,
                        r.type as rel_type
                    """

                    result = await session.run(edge_query, node_ids=node_ids)

                    edges = []
                    async for record in result:
                        edges.append({
                            "id": record["rel_id"] or f"{record['source_id']}-{record['target_id']}",
                            "source": record["source_id"],
                            "target": record["target_id"],
                            "type": record["rel_type"] or "relates",
                            "label": record["rel_label"] or ""
                        })
                else:
                    edges = []

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
        # Neo4j 인증 실패나 다른 오류 발생 시 sample_graph.json 사용 시도
        import os
        import json

        error_msg = str(e)
        if "Unauthorized" in error_msg or "AuthenticationRateLimit" in error_msg or "authentication" in error_msg.lower():
            sample_graph_path = "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/sample_graph.json"
            if os.path.exists(sample_graph_path):
                with open(sample_graph_path, 'r', encoding='utf-8') as f:
                    graph_data = json.load(f)

                # 필터링 적용
                filtered_nodes = graph_data.get("nodes", [])
                filtered_edges = graph_data.get("edges", [])

                if node_types:
                    filtered_nodes = [n for n in filtered_nodes if n.get("type") in node_types]
                    node_ids = {n["id"] for n in filtered_nodes}
                    filtered_edges = [e for e in filtered_edges
                                     if e.get("source") in node_ids and e.get("target") in node_ids]

                # 최대 노드 수 제한
                filtered_nodes = filtered_nodes[:max_nodes]
                node_ids = {n["id"] for n in filtered_nodes}
                filtered_edges = [e for e in filtered_edges
                                 if e.get("source") in node_ids and e.get("target") in node_ids]

                return {
                    "nodes": filtered_nodes,
                    "edges": filtered_edges,
                    "metadata": {
                        **graph_data.get("metadata", {}),
                        "fallback_reason": "Neo4j authentication failed, using sample data"
                    }
                }

        # 다른 종류의 오류는 그대로 전달
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GRAPH_QUERY_ERROR",
                "error_message": f"그래프 조회 중 오류가 발생했습니다: {error_msg}"
            }
        )


@router.get(
    "/nodes/{node_id}",
    summary="노드 상세 정보 조회"
)
async def get_node_details(node_id: str):
    """노드 상세 정보 조회"""
    if not neo4j_manager.driver:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "NEO4J_UNAVAILABLE",
                "error_message": "Neo4j 연결이 초기화되지 않았습니다."
            }
        )

    try:
        async with neo4j_manager.driver.session() as session:
            cypher_query = """
            MATCH (n)
            WHERE id(n) = $node_id
            RETURN
                id(n) as id,
                labels(n)[0] as type,
                properties(n) as properties
            """

            result = await session.run(cypher_query, node_id=int(node_id))
            record = await result.single()
            
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
