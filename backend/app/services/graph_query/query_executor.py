"""
Graph Query Executor

Neo4j 쿼리를 실행하고 결과를 변환합니다.
"""
import time
from typing import List, Dict, Any, Optional
from loguru import logger
from neo4j import Record

from app.models.query import QueryAnalysisResult
from app.models.graph_query import (
    CypherQuery,
    GraphQueryResponse,
    QueryResult,
    QueryResultType,
    QueryError,
    GraphNode,
    GraphRelationship,
    GraphPath,
    CoverageQueryResult,
    DiseaseQueryResult,
    ComparisonResult,
)
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph_query.query_builder import CypherQueryBuilder


class ResultParser:
    """
    Neo4j 쿼리 결과를 파싱합니다.
    """

    @staticmethod
    def parse_records(records: List[Record], result_type: QueryResultType) -> QueryResult:
        """
        Neo4j 레코드를 QueryResult로 변환합니다.

        Args:
            records: Neo4j 레코드 리스트
            result_type: 결과 타입

        Returns:
            QueryResult
        """
        if not records:
            return QueryResult(
                result_type=result_type,
                total_count=0,
            )

        if result_type == QueryResultType.TABLE:
            return ResultParser._parse_table_results(records)
        elif result_type == QueryResultType.NODE:
            return ResultParser._parse_node_results(records)
        elif result_type == QueryResultType.PATH:
            return ResultParser._parse_path_results(records)
        elif result_type == QueryResultType.SCALAR:
            return ResultParser._parse_scalar_results(records)
        else:
            # 기본: 테이블 형식
            return ResultParser._parse_table_results(records)

    @staticmethod
    def _parse_table_results(records: List[Record]) -> QueryResult:
        """테이블 형식 결과 파싱"""
        table = []

        for record in records:
            row = {}
            for key in record.keys():
                value = record[key]
                # Neo4j 타입을 Python 타입으로 변환
                row[key] = ResultParser._convert_value(value)
            table.append(row)

        return QueryResult(
            result_type=QueryResultType.TABLE,
            table=table,
            total_count=len(table),
        )

    @staticmethod
    def _parse_node_results(records: List[Record]) -> QueryResult:
        """노드 결과 파싱"""
        nodes = []

        for record in records:
            for value in record.values():
                if hasattr(value, 'labels'):  # Neo4j Node 객체
                    node = ResultParser._convert_node(value)
                    nodes.append(node)

        return QueryResult(
            result_type=QueryResultType.NODE,
            nodes=nodes,
            total_count=len(nodes),
        )

    @staticmethod
    def _parse_path_results(records: List[Record]) -> QueryResult:
        """경로 결과 파싱"""
        paths = []

        for record in records:
            for value in record.values():
                if hasattr(value, 'nodes'):  # Neo4j Path 객체
                    path = ResultParser._convert_path(value)
                    paths.append(path)

        return QueryResult(
            result_type=QueryResultType.PATH,
            paths=paths,
            total_count=len(paths),
        )

    @staticmethod
    def _parse_scalar_results(records: List[Record]) -> QueryResult:
        """스칼라 값 결과 파싱"""
        scalars = []

        for record in records:
            # 첫 번째 값만 가져오기
            value = list(record.values())[0] if record.values() else None
            scalars.append(ResultParser._convert_value(value))

        return QueryResult(
            result_type=QueryResultType.SCALAR,
            scalars=scalars,
            total_count=len(scalars),
        )

    @staticmethod
    def _convert_node(neo4j_node) -> GraphNode:
        """Neo4j Node를 GraphNode로 변환"""
        return GraphNode(
            node_id=str(neo4j_node.id),
            labels=list(neo4j_node.labels),
            properties=dict(neo4j_node),
        )

    @staticmethod
    def _convert_relationship(neo4j_rel) -> GraphRelationship:
        """Neo4j Relationship를 GraphRelationship로 변환"""
        return GraphRelationship(
            relationship_id=str(neo4j_rel.id),
            type=neo4j_rel.type,
            start_node=str(neo4j_rel.start_node.id),
            end_node=str(neo4j_rel.end_node.id),
            properties=dict(neo4j_rel),
        )

    @staticmethod
    def _convert_path(neo4j_path) -> GraphPath:
        """Neo4j Path를 GraphPath로 변환"""
        nodes = [ResultParser._convert_node(n) for n in neo4j_path.nodes]
        relationships = [
            ResultParser._convert_relationship(r) for r in neo4j_path.relationships
        ]

        return GraphPath(
            nodes=nodes,
            relationships=relationships,
            length=len(neo4j_path),
        )

    @staticmethod
    def _convert_value(value: Any) -> Any:
        """Neo4j 값을 Python 타입으로 변환"""
        if value is None:
            return None

        # Node 객체
        if hasattr(value, 'labels'):
            return dict(value)

        # Relationship 객체
        if hasattr(value, 'type') and hasattr(value, 'start_node'):
            return {
                'type': value.type,
                'properties': dict(value),
            }

        # List
        if isinstance(value, list):
            return [ResultParser._convert_value(v) for v in value]

        # Dict
        if isinstance(value, dict):
            return {k: ResultParser._convert_value(v) for k, v in value.items()}

        # Scalar 값
        return value

    @staticmethod
    def parse_coverage_results(query_result: QueryResult) -> List[CoverageQueryResult]:
        """
        QueryResult를 CoverageQueryResult 리스트로 변환

        Args:
            query_result: 쿼리 결과

        Returns:
            보장 결과 리스트
        """
        coverage_results = []

        for row in query_result.table:
            try:
                coverage = CoverageQueryResult(
                    coverage_name=row.get("coverage_name", ""),
                    disease_name=row.get("disease_name"),
                    amount=row.get("amount"),
                    kcd_code=row.get("kcd_code"),
                    conditions=row.get("conditions", []),
                    exclusions=row.get("exclusions", []),
                    waiting_period_days=row.get("waiting_period_days"),
                )
                coverage_results.append(coverage)
            except Exception as e:
                logger.warning(f"Failed to parse coverage result: {e}")
                continue

        return coverage_results

    @staticmethod
    def parse_disease_results(query_result: QueryResult) -> List[DiseaseQueryResult]:
        """
        QueryResult를 DiseaseQueryResult 리스트로 변환

        Args:
            query_result: 쿼리 결과

        Returns:
            질병 결과 리스트
        """
        disease_results = []

        for row in query_result.table:
            try:
                # coverages 필드 처리
                coverages_data = row.get("coverages", [])
                coverage_names = []
                amounts = []

                if isinstance(coverages_data, list):
                    for cov in coverages_data:
                        if isinstance(cov, dict):
                            if cov.get("coverage_name"):
                                coverage_names.append(cov["coverage_name"])
                            if cov.get("amount"):
                                amounts.append(cov["amount"])

                disease = DiseaseQueryResult(
                    disease_name=row.get("disease_name", ""),
                    standard_name=row.get("standard_name"),
                    kcd_code=row.get("kcd_code"),
                    kcd_name=row.get("kcd_name"),
                    coverages=coverage_names,
                    amounts=amounts,
                )
                disease_results.append(disease)
            except Exception as e:
                logger.warning(f"Failed to parse disease result: {e}")
                continue

        return disease_results

    @staticmethod
    def parse_comparison_result(query_result: QueryResult) -> Optional[ComparisonResult]:
        """
        QueryResult를 ComparisonResult로 변환

        Args:
            query_result: 쿼리 결과

        Returns:
            비교 결과
        """
        if not query_result.table:
            return None

        try:
            row = query_result.table[0]

            # 질병 비교인지 보장 비교인지 판단
            if "disease1_name" in row:
                item1 = {
                    "name": row.get("disease1_name"),
                    "kcd_code": row.get("disease1_kcd"),
                    "coverages": row.get("cov1", []),
                }
                item2 = {
                    "name": row.get("disease2_name"),
                    "kcd_code": row.get("disease2_kcd"),
                    "coverages": row.get("cov2", []),
                }
            elif "coverage1_name" in row:
                item1 = {
                    "name": row.get("coverage1_name"),
                    "amount": row.get("coverage1_amount"),
                    "diseases": row.get("coverage1_diseases", []),
                }
                item2 = {
                    "name": row.get("coverage2_name"),
                    "amount": row.get("coverage2_amount"),
                    "diseases": row.get("coverage2_diseases", []),
                }
            else:
                return None

            # 차이점과 공통점 분석
            differences, similarities = ResultParser._analyze_differences(item1, item2)

            return ComparisonResult(
                item1=item1,
                item2=item2,
                differences=differences,
                similarities=similarities,
            )

        except Exception as e:
            logger.error(f"Failed to parse comparison result: {e}")
            return None

    @staticmethod
    def _analyze_differences(
        item1: Dict[str, Any], item2: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """두 항목의 차이점과 공통점 분석"""
        differences = []
        similarities = []

        # 보장/질병 비교
        if "coverages" in item1:
            cov1 = set(c.get("name", "") for c in item1["coverages"] if isinstance(c, dict))
            cov2 = set(c.get("name", "") for c in item2["coverages"] if isinstance(c, dict))

            only_in_1 = cov1 - cov2
            only_in_2 = cov2 - cov1
            common = cov1 & cov2

            if only_in_1:
                differences.append({
                    "field": "coverages",
                    "item1_only": list(only_in_1),
                })
            if only_in_2:
                differences.append({
                    "field": "coverages",
                    "item2_only": list(only_in_2),
                })
            if common:
                similarities.append({
                    "field": "coverages",
                    "common": list(common),
                })

        elif "diseases" in item1:
            dis1 = set(d.get("name", "") for d in item1["diseases"] if isinstance(d, dict))
            dis2 = set(d.get("name", "") for d in item2["diseases"] if isinstance(d, dict))

            only_in_1 = dis1 - dis2
            only_in_2 = dis2 - dis1
            common = dis1 & dis2

            if only_in_1:
                differences.append({
                    "field": "diseases",
                    "item1_only": list(only_in_1),
                })
            if only_in_2:
                differences.append({
                    "field": "diseases",
                    "item2_only": list(only_in_2),
                })
            if common:
                similarities.append({
                    "field": "diseases",
                    "common": list(common),
                })

        # 금액 비교
        if "amount" in item1 and "amount" in item2:
            amount1 = item1["amount"]
            amount2 = item2["amount"]
            if amount1 != amount2:
                differences.append({
                    "field": "amount",
                    "item1_value": amount1,
                    "item2_value": amount2,
                    "difference": abs(amount1 - amount2) if amount1 and amount2 else None,
                })

        return differences, similarities


class GraphQueryExecutor:
    """
    그래프 쿼리 실행기

    Cypher 쿼리를 실행하고 결과를 GraphQueryResponse로 변환합니다.
    """

    def __init__(self, neo4j_service: Neo4jService):
        """
        Args:
            neo4j_service: Neo4j 서비스
        """
        self.neo4j = neo4j_service
        self.query_builder = CypherQueryBuilder()
        self.result_parser = ResultParser()

    async def execute(
        self, analysis: QueryAnalysisResult, include_explanation: bool = True
    ) -> GraphQueryResponse:
        """
        쿼리 분석 결과를 기반으로 그래프 쿼리를 실행합니다.

        Args:
            analysis: 쿼리 분석 결과
            include_explanation: 설명 포함 여부

        Returns:
            그래프 쿼리 응답
        """
        try:
            # 1. Cypher 쿼리 생성
            cypher_query = self.query_builder.build(analysis)

            logger.info(f"Executing Cypher query:\n{cypher_query}")

            # 2. 쿼리 실행
            start_time = time.time()
            records = await self._execute_cypher(cypher_query)
            execution_time_ms = (time.time() - start_time) * 1000

            # 3. 결과 파싱
            query_result = self.result_parser.parse_records(
                records, cypher_query.result_type
            )
            query_result.execution_time_ms = execution_time_ms

            # 4. 구조화된 결과 생성
            coverage_results = []
            disease_results = []
            comparison_result = None

            if analysis.intent in [
                "coverage_amount",
                "coverage_check",
                "waiting_period",
            ]:
                coverage_results = self.result_parser.parse_coverage_results(
                    query_result
                )

            if analysis.intent in ["coverage_check"]:
                disease_results = self.result_parser.parse_disease_results(
                    query_result
                )

            if "comparison" in analysis.intent.value:
                comparison_result = self.result_parser.parse_comparison_result(
                    query_result
                )

            # 5. 설명 생성
            explanation = None
            if include_explanation:
                explanation = self._generate_explanation(
                    analysis, query_result, coverage_results, disease_results
                )

            # 6. 응답 생성
            response = GraphQueryResponse(
                original_query=analysis.original_query,
                cypher_query=str(cypher_query),
                execution_time_ms=execution_time_ms,
                result=query_result,
                coverage_results=coverage_results,
                disease_results=disease_results,
                comparison_result=comparison_result,
                success=True,
                explanation=explanation,
            )

            logger.info(
                f"Query executed successfully in {execution_time_ms:.2f}ms, "
                f"returned {query_result.total_count} results"
            )

            return response

        except Exception as e:
            logger.error(f"Query execution failed: {e}")

            # 오류 응답 생성
            error = QueryError(
                error_type=type(e).__name__,
                message=str(e),
                suggestion=self._suggest_fix(e),
            )

            return GraphQueryResponse(
                original_query=analysis.original_query,
                cypher_query="",
                execution_time_ms=0.0,
                result=QueryResult(result_type=QueryResultType.TABLE, total_count=0),
                success=False,
                error=error,
            )

    async def _execute_cypher(self, cypher_query: CypherQuery) -> List[Record]:
        """
        Cypher 쿼리 실행

        Args:
            cypher_query: Cypher 쿼리

        Returns:
            Neo4j 레코드 리스트
        """
        with self.neo4j.driver.session() as session:
            result = session.run(cypher_query.query, cypher_query.parameters)
            records = list(result)
            return records

    def _generate_explanation(
        self,
        analysis: QueryAnalysisResult,
        query_result: QueryResult,
        coverage_results: List[CoverageQueryResult],
        disease_results: List[DiseaseQueryResult],
    ) -> str:
        """결과 설명 생성"""
        if query_result.is_empty():
            return "검색 결과가 없습니다."

        explanations = []

        # 의도별 설명
        if analysis.intent == "coverage_amount":
            if coverage_results:
                explanations.append(
                    f"{len(coverage_results)}개의 보장 항목을 찾았습니다."
                )

        elif analysis.intent == "coverage_check":
            if disease_results:
                disease = disease_results[0]
                if disease.coverages:
                    explanations.append(
                        f"{disease.disease_name}은(는) {len(disease.coverages)}개의 "
                        f"보장에 포함되어 있습니다."
                    )
                else:
                    explanations.append(
                        f"{disease.disease_name}은(는) 현재 보장되지 않습니다."
                    )

        elif "comparison" in analysis.intent.value:
            explanations.append("비교 결과를 확인하세요.")

        # 기본 설명
        if not explanations:
            explanations.append(
                f"{query_result.total_count}개의 결과를 찾았습니다."
            )

        return " ".join(explanations)

    def _suggest_fix(self, error: Exception) -> Optional[str]:
        """오류 해결 제안"""
        error_msg = str(error).lower()

        if "not found" in error_msg or "no disease" in error_msg:
            return "질병명이나 보장명을 다시 확인해주세요."

        if "timeout" in error_msg:
            return "쿼리가 너무 복잡합니다. 더 구체적인 질문을 해주세요."

        if "connection" in error_msg:
            return "데이터베이스 연결을 확인해주세요."

        return "쿼리를 다시 시도하거나 질문을 바꿔보세요."
