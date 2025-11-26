"""
Vector Search Engine

Neo4j 벡터 인덱스를 활용한 유사도 검색 엔진.
"""
import time
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.vector_search import (
    SearchRequest,
    SearchResponse,
    VectorSearchResult,
    VectorSearchResults,
    VectorIndexType,
    SearchStrategy,
    EmbeddingRequest,
)
from app.services.graph.neo4j_service import Neo4jService
from app.services.vector_search.query_embedder import QueryEmbedder


class VectorSearchEngine:
    """
    벡터 검색 엔진

    Neo4j 벡터 인덱스를 사용하여 유사도 기반 검색을 수행합니다.
    """

    def __init__(
        self,
        neo4j_service: Neo4jService,
        query_embedder: Optional[QueryEmbedder] = None,
    ):
        """
        Args:
            neo4j_service: Neo4j 서비스
            query_embedder: 쿼리 임베더
        """
        self.neo4j = neo4j_service
        self.query_embedder = query_embedder or QueryEmbedder()

    async def search(
        self,
        query: str,
        top_k: int = 10,
        index_name: VectorIndexType = VectorIndexType.CLAUSE_EMBEDDINGS,
        min_score: float = 0.0,
    ) -> VectorSearchResults:
        """
        벡터 유사도 검색을 수행합니다.

        Args:
            query: 검색 질문
            top_k: 반환할 결과 개수
            index_name: 벡터 인덱스 이름
            min_score: 최소 유사도 점수

        Returns:
            벡터 검색 결과
        """
        start_time = time.time()

        # 1. 쿼리 임베딩 생성
        embedding_request = EmbeddingRequest(text=query, model="openai")
        embedding_response = await self.query_embedder.embed_query(embedding_request)

        logger.info(
            f"Generated query embedding in {embedding_response.generation_time_ms:.2f}ms"
        )

        # 2. 벡터 검색 실행
        results = self._execute_vector_search(
            embedding=embedding_response.embedding,
            top_k=top_k,
            index_name=index_name.value,
        )

        # 3. 최소 점수 필터링
        if min_score > 0:
            results = [r for r in results if r.score >= min_score]

        search_time_ms = (time.time() - start_time) * 1000

        return VectorSearchResults(
            results=results,
            total_count=len(results),
            search_time_ms=search_time_ms,
            query=query,
            top_k=top_k,
            index_name=index_name.value,
        )

    def _execute_vector_search(
        self, embedding: List[float], top_k: int, index_name: str
    ) -> List[VectorSearchResult]:
        """
        Neo4j 벡터 검색 실행

        Args:
            embedding: 쿼리 임베딩 벡터
            top_k: 반환할 결과 개수
            index_name: 인덱스 이름

        Returns:
            검색 결과 리스트
        """
        # Neo4j 벡터 검색 쿼리
        cypher = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        RETURN
          elementId(node) as node_id,
          score,
          labels(node) as labels,
          properties(node) as properties
        ORDER BY score DESC
        """

        with self.neo4j.driver.session() as session:
            result = session.run(
                cypher,
                index_name=index_name,
                top_k=top_k,
                embedding=embedding,
            )

            search_results = []
            for record in result:
                # 조항 노드인 경우 추가 정보 추출
                properties = record["properties"]
                labels = record["labels"]

                vector_result = VectorSearchResult(
                    node_id=record["node_id"],
                    score=float(record["score"]),
                    labels=labels,
                    properties=properties,
                )

                # Clause 노드 정보 추출
                if "Clause" in labels:
                    vector_result.clause_id = properties.get("clause_id")
                    vector_result.article_num = properties.get("article_num")
                    vector_result.clause_text = properties.get("clause_text")

                search_results.append(vector_result)

            logger.info(f"Vector search returned {len(search_results)} results")
            return search_results

    async def multi_index_search(
        self, query: str, top_k: int = 10, min_score: float = 0.0
    ) -> Dict[str, VectorSearchResults]:
        """
        여러 인덱스에서 동시 검색

        Args:
            query: 검색 질문
            top_k: 각 인덱스당 결과 개수
            min_score: 최소 점수

        Returns:
            인덱스별 검색 결과
        """
        results = {}

        for index_type in VectorIndexType:
            try:
                search_results = await self.search(
                    query=query,
                    top_k=top_k,
                    index_name=index_type,
                    min_score=min_score,
                )
                results[index_type.value] = search_results
            except Exception as e:
                logger.warning(f"Search failed for index {index_type.value}: {e}")
                # 빈 결과 반환
                results[index_type.value] = VectorSearchResults(
                    results=[],
                    total_count=0,
                    search_time_ms=0.0,
                    query=query,
                    top_k=top_k,
                    index_name=index_type.value,
                )

        return results

    def check_index_exists(self, index_name: str) -> bool:
        """
        벡터 인덱스 존재 여부 확인

        Args:
            index_name: 인덱스 이름

        Returns:
            존재 여부
        """
        cypher = """
        SHOW INDEXES
        YIELD name, type
        WHERE name = $index_name AND type = 'VECTOR'
        RETURN count(*) as count
        """

        with self.neo4j.driver.session() as session:
            result = session.run(cypher, index_name=index_name)
            record = result.single()
            return record["count"] > 0 if record else False

    def get_index_info(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        벡터 인덱스 정보 조회

        Args:
            index_name: 인덱스 이름

        Returns:
            인덱스 정보
        """
        cypher = """
        SHOW INDEXES
        YIELD name, type, labelsOrTypes, properties, options
        WHERE name = $index_name AND type = 'VECTOR'
        RETURN name, labelsOrTypes, properties, options
        """

        with self.neo4j.driver.session() as session:
            result = session.run(cypher, index_name=index_name)
            record = result.single()

            if not record:
                return None

            return {
                "name": record["name"],
                "labels": record["labelsOrTypes"],
                "properties": record["properties"],
                "options": record["options"],
            }


class SemanticSearchEngine(VectorSearchEngine):
    """
    의미론적 검색 엔진

    벡터 검색에 추가적인 의미 분석을 결합합니다.
    """

    async def semantic_search(
        self, query: str, context: Optional[Dict[str, Any]] = None, top_k: int = 10
    ) -> VectorSearchResults:
        """
        의미론적 검색

        Args:
            query: 검색 질문
            context: 추가 컨텍스트 (엔티티, 의도 등)
            top_k: 결과 개수

        Returns:
            검색 결과
        """
        # 컨텍스트 기반 쿼리 확장
        expanded_query = self._expand_query_with_context(query, context)

        logger.info(f"Expanded query: {expanded_query}")

        # 벡터 검색
        results = await self.search(
            query=expanded_query,
            top_k=top_k,
            index_name=VectorIndexType.CLAUSE_EMBEDDINGS,
        )

        # 컨텍스트 기반 점수 조정
        if context:
            results = self._adjust_scores_with_context(results, context)

        return results

    def _expand_query_with_context(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """
        컨텍스트를 활용한 쿼리 확장

        Args:
            query: 원본 질문
            context: 컨텍스트

        Returns:
            확장된 질문
        """
        if not context:
            return query

        expanded_parts = [query]

        # 엔티티 추가
        if "entities" in context:
            entities = context["entities"]
            for entity in entities:
                if isinstance(entity, dict) and "text" in entity:
                    expanded_parts.append(entity["text"])

        # 의도 추가 (선택적)
        if "intent" in context:
            # 의도에 따른 키워드 추가
            intent = context["intent"]
            if intent == "coverage_amount":
                expanded_parts.append("보장금액")
            elif intent == "waiting_period":
                expanded_parts.append("대기기간")

        return " ".join(expanded_parts)

    def _adjust_scores_with_context(
        self, results: VectorSearchResults, context: Dict[str, Any]
    ) -> VectorSearchResults:
        """
        컨텍스트 기반 점수 조정

        Args:
            results: 검색 결과
            context: 컨텍스트

        Returns:
            점수 조정된 결과
        """
        adjusted_results = []

        for result in results.results:
            adjusted_score = result.score

            # 엔티티 매칭 부스트
            if "entities" in context:
                entities = context["entities"]
                text_content = result.get_text_content().lower()

                for entity in entities:
                    entity_text = (
                        entity["text"] if isinstance(entity, dict) else str(entity)
                    )
                    if entity_text.lower() in text_content:
                        adjusted_score *= 1.2  # 20% 부스트
                        break

            # 조정된 점수로 업데이트
            adjusted_result = result.model_copy()
            adjusted_result.score = min(adjusted_score, 1.0)  # 최대 1.0
            adjusted_results.append(adjusted_result)

        # 점수로 재정렬
        adjusted_results.sort(key=lambda r: r.score, reverse=True)

        results.results = adjusted_results
        return results
