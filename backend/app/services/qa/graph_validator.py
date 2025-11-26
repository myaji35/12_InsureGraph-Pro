"""
Graph Validator

Neo4j 그래프의 품질과 일관성을 검증합니다.
"""
import logging
from typing import Dict, Any, Optional

from app.models.validation import (
    GraphValidationResult,
    ValidationSeverity,
)
from app.services.graph.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class GraphValidator:
    """그래프 품질 검증기"""

    def __init__(self, neo4j_service: Optional[Neo4jService] = None):
        """
        검증기 초기화

        Args:
            neo4j_service: Neo4j 서비스 (선택사항)
        """
        self.neo4j = neo4j_service

    def validate(
        self, graph_stats: Dict[str, Any], neo4j_service: Optional[Neo4jService] = None
    ) -> GraphValidationResult:
        """
        그래프 검증

        Args:
            graph_stats: 그래프 통계 (Story 1.7)
            neo4j_service: Neo4j 서비스 (선택사항)

        Returns:
            GraphValidationResult
        """
        logger.info("그래프 검증 시작")

        result = GraphValidationResult(is_valid=True)

        # Neo4j 서비스 설정
        if neo4j_service:
            self.neo4j = neo4j_service

        # 1. 기본 통계 검증
        self._validate_basic_stats(graph_stats, result)

        # 2. 노드 검증
        self._validate_nodes(graph_stats, result)

        # 3. 관계 검증
        self._validate_relationships(graph_stats, result)

        # 4. 일관성 검증 (Neo4j 연결이 있는 경우)
        if self.neo4j:
            self._validate_consistency(result)

        logger.info(
            f"그래프 검증 완료: {'통과' if result.is_valid else '실패'} "
            f"({len(result.issues)}개 이슈)"
        )

        return result

    def _validate_basic_stats(
        self, graph_stats: Dict[str, Any], result: GraphValidationResult
    ):
        """기본 통계 검증"""
        total_nodes = graph_stats.get("total_nodes", 0)
        total_relationships = graph_stats.get("total_relationships", 0)

        # 통계 저장
        result.total_nodes = total_nodes
        result.total_relationships = total_relationships
        result.nodes_by_type = graph_stats.get("nodes_by_type", {})
        result.relationships_by_type = graph_stats.get("relationships_by_type", {})

        # 기본 검증: 노드가 생성되었는지
        if total_nodes == 0:
            result.add_issue(
                severity=ValidationSeverity.CRITICAL,
                category="graph",
                message="생성된 노드가 없습니다",
                suggestion="그래프 구축이 올바르게 수행되었는지 확인하세요",
            )
            result.nodes_valid = False
            result.is_valid = False
            return

        # 관계가 생성되었는지
        if total_relationships == 0:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="graph",
                message="생성된 관계가 없습니다",
                suggestion="관계 추출이 올바르게 수행되었는지 확인하세요",
            )
            result.relationships_valid = False

    def _validate_nodes(
        self, graph_stats: Dict[str, Any], result: GraphValidationResult
    ):
        """노드 검증"""
        nodes_by_type = graph_stats.get("nodes_by_type", {})

        # 필수 노드 타입 확인
        required_types = ["Product", "Clause"]
        for node_type in required_types:
            if node_type not in nodes_by_type or nodes_by_type[node_type] == 0:
                result.add_issue(
                    severity=ValidationSeverity.ERROR,
                    category="nodes",
                    message=f"필수 노드 타입이 없습니다: {node_type}",
                    suggestion=f"{node_type} 노드가 생성되도록 확인하세요",
                )
                result.nodes_valid = False

        # Product 노드는 정확히 1개여야 함
        if nodes_by_type.get("Product", 0) > 1:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="nodes",
                message=f"Product 노드가 {nodes_by_type['Product']}개 생성되었습니다",
                suggestion="단일 제품 문서는 Product 노드 1개만 있어야 합니다",
            )

        # Coverage 노드 확인
        if "Coverage" not in nodes_by_type or nodes_by_type["Coverage"] == 0:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="nodes",
                message="Coverage 노드가 없습니다",
                suggestion="보장 항목이 추출되었는지 확인하세요",
            )

        # Disease 노드 확인
        if "Disease" not in nodes_by_type or nodes_by_type["Disease"] == 0:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="nodes",
                message="Disease 노드가 없습니다",
                suggestion="질병 엔티티가 연결되었는지 확인하세요",
            )

    def _validate_relationships(
        self, graph_stats: Dict[str, Any], result: GraphValidationResult
    ):
        """관계 검증"""
        relationships_by_type = graph_stats.get("relationships_by_type", {})

        # 주요 관계 타입 확인
        important_types = ["COVERS", "HAS_COVERAGE"]
        missing_types = []
        for rel_type in important_types:
            if rel_type not in relationships_by_type or relationships_by_type[rel_type] == 0:
                missing_types.append(rel_type)

        if missing_types:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="relationships",
                message=f"주요 관계 타입이 없습니다: {missing_types}",
                suggestion="관계 추출 및 그래프 구축을 확인하세요",
            )
            result.relationships_valid = False

    def _validate_consistency(self, result: GraphValidationResult):
        """일관성 검증 (Neo4j 쿼리 필요)"""
        if not self.neo4j:
            return

        try:
            # 1. 고아 노드 검사 (연결이 없는 노드)
            # Product 노드는 제외
            orphaned_query = """
            MATCH (n)
            WHERE NOT (n:Product)
            AND NOT (n)-[]-()
            RETURN count(n) as orphaned_count
            """
            orphaned_result = self.neo4j._execute_read(orphaned_query, {})
            if orphaned_result:
                orphaned_count = orphaned_result[0].get("orphaned_count", 0)
                result.orphaned_nodes = orphaned_count

                if orphaned_count > 0:
                    result.add_issue(
                        severity=ValidationSeverity.WARNING,
                        category="consistency",
                        message=f"{orphaned_count}개의 고아 노드 발견 (연결 없음)",
                        suggestion="고아 노드를 확인하고 필요시 삭제하세요",
                    )
                    result.consistency_valid = False

            # 2. 중복 노드 검사 (같은 ID를 가진 노드)
            # 실제 구현에서는 각 노드 타입별로 ID 중복 검사
            # 여기서는 간소화

            # 3. 유효하지 않은 관계 검사
            # 예: COVERS 관계가 Coverage → Disease가 아닌 경우
            invalid_covers_query = """
            MATCH (source)-[r:COVERS]->(target)
            WHERE NOT (source:Coverage AND target:Disease)
            RETURN count(r) as invalid_count
            """
            invalid_result = self.neo4j._execute_read(invalid_covers_query, {})
            if invalid_result:
                invalid_count = invalid_result[0].get("invalid_count", 0)
                result.invalid_relationships = invalid_count

                if invalid_count > 0:
                    result.add_issue(
                        severity=ValidationSeverity.ERROR,
                        category="consistency",
                        message=f"{invalid_count}개의 유효하지 않은 COVERS 관계",
                        suggestion="COVERS는 Coverage → Disease만 가능합니다",
                    )
                    result.consistency_valid = False

        except Exception as e:
            logger.warning(f"일관성 검증 중 에러: {e}")
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="consistency",
                message=f"일관성 검증 실패: {str(e)}",
                suggestion="Neo4j 연결을 확인하세요",
            )
