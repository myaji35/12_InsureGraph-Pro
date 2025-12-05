"""
Knowledge Graph API Endpoints

Neo4j 지식 그래프 데이터를 조회하는 API 엔드포인트입니다.
React Flow 기반 인터랙티브 그래프 시각화를 위한 데이터를 제공합니다.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from neo4j import GraphDatabase

from app.core.config import settings

router = APIRouter()


# ===========================
# Pydantic Models
# ===========================

class GraphNode(BaseModel):
    """그래프 노드 모델 (React Flow 형식)"""
    id: str
    type: str
    label: str
    data: Dict[str, Any]


class GraphEdge(BaseModel):
    """그래프 엣지 모델 (React Flow 형식)"""
    id: str
    source: str
    target: str
    type: str
    label: str
    data: Dict[str, Any]


class GraphData(BaseModel):
    """전체 그래프 데이터"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]


class NodeDetail(BaseModel):
    """노드 상세 정보"""
    entity_id: str
    label: str
    type: str
    description: str
    source_text: str
    document_id: str
    insurer: str
    product_type: str
    created_at: str
    neighbors: List[Dict[str, Any]]


# ===========================
# Neo4j Connection
# ===========================

class Neo4jConnection:
    """Neo4j 연결 관리"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def execute_query(self, query: str, parameters: dict = None) -> List[Dict]:
        """쿼리 실행"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]


# ===========================
# API Endpoints
# ===========================

@router.get("/stats", summary="그래프 통계")
async def get_graph_stats():
    """
    Neo4j 그래프의 통계 정보를 반환합니다.

    Returns:
        - total_nodes: 전체 노드 수
        - total_relationships: 전체 관계 수
        - node_types: 노드 타입별 개수
        - relationship_types: 관계 타입별 개수
    """
    neo4j = Neo4jConnection()

    try:
        # 전체 노드/관계 수
        stats_query = """
        MATCH (n)
        WITH count(n) as node_count
        MATCH ()-[r]->()
        RETURN node_count, count(r) as rel_count
        """
        result = neo4j.execute_query(stats_query)

        if not result:
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_types": {},
                "relationship_types": {}
            }

        total_nodes = result[0]["node_count"]
        total_relationships = result[0]["rel_count"]

        # 노드 타입별 개수
        node_types_query = """
        MATCH (n)
        RETURN labels(n)[0] as type, count(*) as count
        ORDER BY count DESC
        """
        node_types_result = neo4j.execute_query(node_types_query)
        node_types = {item["type"]: item["count"] for item in node_types_result}

        # 관계 타입별 개수
        rel_types_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        """
        rel_types_result = neo4j.execute_query(rel_types_query)
        relationship_types = {item["type"]: item["count"] for item in rel_types_result}

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "node_types": node_types,
            "relationship_types": relationship_types
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph stats: {str(e)}")
    finally:
        neo4j.close()


@router.get("/data", response_model=GraphData, summary="그래프 데이터 조회")
async def get_graph_data(
    limit: int = Query(500, description="최대 노드 수", ge=1, le=5000),
    entity_type: Optional[str] = Query(None, description="엔티티 타입 필터 (예: coverage_item)"),
    insurer: Optional[str] = Query(None, description="보험사 필터 (예: 삼성화재)"),
    product_type: Optional[str] = Query(None, description="상품 타입 필터 (예: 자동차보험)")
):
    """
    Neo4j에서 그래프 데이터를 조회하여 React Flow 형식으로 반환합니다.

    Parameters:
        - limit: 최대 노드 수 (기본 500개)
        - entity_type: 엔티티 타입 필터
        - insurer: 보험사 필터
        - product_type: 상품 타입 필터

    Returns:
        GraphData: nodes, edges, stats
    """
    neo4j = Neo4jConnection()

    try:
        # 필터 조건 구성
        where_conditions = []
        if entity_type:
            where_conditions.append(f"n.type = '{entity_type}'")
        if insurer:
            where_conditions.append(f"n.insurer = '{insurer}'")
        if product_type:
            where_conditions.append(f"n.product_type = '{product_type}'")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 노드 조회
        nodes_query = f"""
        MATCH (n)
        {where_clause}
        RETURN n
        LIMIT {limit}
        """

        nodes_result = neo4j.execute_query(nodes_query)

        # 노드 ID 목록
        node_ids = [node["n"]["entity_id"] for node in nodes_result]

        if not node_ids:
            return GraphData(nodes=[], edges=[], stats={"nodes": 0, "edges": 0})

        # 관계 조회 (조회된 노드들 사이의 관계만)
        edges_query = """
        MATCH (source)-[r]->(target)
        WHERE source.entity_id IN $node_ids AND target.entity_id IN $node_ids
        RETURN source.entity_id as source_id,
               target.entity_id as target_id,
               type(r) as rel_type,
               r.description as description
        """

        edges_result = neo4j.execute_query(edges_query, {"node_ids": node_ids})

        # React Flow 형식으로 변환
        nodes = []
        for item in nodes_result:
            node_data = item["n"]
            entity_id = node_data.get("entity_id")

            # Skip nodes without entity_id
            if not entity_id:
                continue

            nodes.append(GraphNode(
                id=str(entity_id),
                type=node_data.get("type", "unknown"),
                label=node_data.get("label", "Unknown"),
                data={
                    "description": node_data.get("description", ""),
                    "source_text": node_data.get("source_text", "")[:100] + "..." if node_data.get("source_text") else "",
                    "insurer": node_data.get("insurer", ""),
                    "product_type": node_data.get("product_type", ""),
                    "document_id": node_data.get("document_id", ""),
                    "created_at": node_data.get("created_at", "")
                }
            ))

        edges = []
        for idx, item in enumerate(edges_result):
            edges.append(GraphEdge(
                id=f"edge-{idx}",
                source=item["source_id"],
                target=item["target_id"],
                type=item["rel_type"],
                label=item["rel_type"].replace("_", " ").title(),
                data={
                    "description": item.get("description", "")
                }
            ))

        return GraphData(
            nodes=nodes,
            edges=edges,
            stats={
                "nodes": len(nodes),
                "edges": len(edges)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph data: {str(e)}")
    finally:
        neo4j.close()


@router.get("/node/{entity_id}", response_model=NodeDetail, summary="노드 상세 정보")
async def get_node_detail(entity_id: str):
    """
    특정 노드의 상세 정보와 이웃 노드들을 반환합니다.

    Parameters:
        - entity_id: 엔티티 ID

    Returns:
        NodeDetail: 노드 상세 정보 + 이웃 노드 목록
    """
    neo4j = Neo4jConnection()

    try:
        # 노드 정보 조회
        node_query = """
        MATCH (n {entity_id: $entity_id})
        RETURN n
        """

        node_result = neo4j.execute_query(node_query, {"entity_id": entity_id})

        if not node_result:
            raise HTTPException(status_code=404, detail=f"Node not found: {entity_id}")

        node_data = node_result[0]["n"]

        # 이웃 노드 조회 (들어오는 관계 + 나가는 관계)
        neighbors_query = """
        MATCH (n {entity_id: $entity_id})-[r]-(neighbor)
        RETURN neighbor.entity_id as neighbor_id,
               neighbor.label as neighbor_label,
               neighbor.type as neighbor_type,
               type(r) as relationship_type,
               r.description as rel_description,
               CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END as direction
        LIMIT 50
        """

        neighbors_result = neo4j.execute_query(neighbors_query, {"entity_id": entity_id})

        neighbors = [
            {
                "entity_id": item["neighbor_id"],
                "label": item["neighbor_label"],
                "type": item["neighbor_type"],
                "relationship_type": item["relationship_type"],
                "relationship_description": item.get("rel_description", ""),
                "direction": item["direction"]
            }
            for item in neighbors_result
        ]

        return NodeDetail(
            entity_id=node_data["entity_id"],
            label=node_data.get("label", "Unknown"),
            type=node_data.get("type", "unknown"),
            description=node_data.get("description", ""),
            source_text=node_data.get("source_text", ""),
            document_id=node_data.get("document_id", ""),
            insurer=node_data.get("insurer", ""),
            product_type=node_data.get("product_type", ""),
            created_at=node_data.get("created_at", ""),
            neighbors=neighbors
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch node detail: {str(e)}")
    finally:
        neo4j.close()


@router.get("/search", summary="노드 검색")
async def search_nodes(
    query: str = Query(..., description="검색어 (라벨 또는 설명에서 검색)", min_length=2),
    limit: int = Query(20, description="최대 결과 수", ge=1, le=100)
):
    """
    라벨 또는 설명에서 검색어를 포함하는 노드들을 검색합니다.

    Parameters:
        - query: 검색어 (최소 2글자)
        - limit: 최대 결과 수

    Returns:
        검색된 노드 목록
    """
    neo4j = Neo4jConnection()

    try:
        search_query = """
        MATCH (n)
        WHERE toLower(n.label) CONTAINS toLower($query)
           OR toLower(n.description) CONTAINS toLower($query)
        RETURN n.entity_id as entity_id,
               n.label as label,
               n.type as type,
               n.description as description,
               n.insurer as insurer,
               n.product_type as product_type
        LIMIT $limit
        """

        result = neo4j.execute_query(search_query, {"query": query, "limit": limit})

        return {
            "query": query,
            "count": len(result),
            "results": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        neo4j.close()


@router.get("/neighborhood/{entity_id}", summary="이웃 서브그래프 조회")
async def get_neighborhood(
    entity_id: str,
    depth: int = Query(1, description="탐색 깊이 (1-3)", ge=1, le=3)
):
    """
    특정 노드를 중심으로 N-hop 이웃 서브그래프를 반환합니다.

    Parameters:
        - entity_id: 중심 노드 ID
        - depth: 탐색 깊이 (1-3)

    Returns:
        서브그래프 (nodes, edges)
    """
    neo4j = Neo4jConnection()

    try:
        # N-hop 이웃 노드 조회
        neighborhood_query = f"""
        MATCH path = (center {{entity_id: $entity_id}})-[*1..{depth}]-(neighbor)
        WITH collect(distinct center) + collect(distinct neighbor) as all_nodes
        UNWIND all_nodes as n
        RETURN DISTINCT n
        LIMIT 200
        """

        nodes_result = neo4j.execute_query(neighborhood_query, {"entity_id": entity_id})

        if not nodes_result:
            raise HTTPException(status_code=404, detail=f"Node not found: {entity_id}")

        node_ids = [node["n"]["entity_id"] for node in nodes_result]

        # 관계 조회
        edges_query = """
        MATCH (source)-[r]->(target)
        WHERE source.entity_id IN $node_ids AND target.entity_id IN $node_ids
        RETURN source.entity_id as source_id,
               target.entity_id as target_id,
               type(r) as rel_type,
               r.description as description
        """

        edges_result = neo4j.execute_query(edges_query, {"node_ids": node_ids})

        # React Flow 형식 변환
        nodes = []
        for item in nodes_result:
            node_data = item["n"]
            nodes.append({
                "id": node_data["entity_id"],
                "type": node_data.get("type", "unknown"),
                "label": node_data.get("label", "Unknown"),
                "data": {
                    "description": node_data.get("description", ""),
                    "insurer": node_data.get("insurer", ""),
                    "product_type": node_data.get("product_type", ""),
                    "is_center": node_data["entity_id"] == entity_id
                }
            })

        edges = []
        for idx, item in enumerate(edges_result):
            edges.append({
                "id": f"edge-{idx}",
                "source": item["source_id"],
                "target": item["target_id"],
                "type": item["rel_type"],
                "label": item["rel_type"].replace("_", " ").title(),
                "data": {
                    "description": item.get("description", "")
                }
            })

        return {
            "center_node_id": entity_id,
            "depth": depth,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "nodes": len(nodes),
                "edges": len(edges)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch neighborhood: {str(e)}")
    finally:
        neo4j.close()
