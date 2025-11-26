"""
Cypher Query Builder

Neo4j Cypher 쿼리를 생성합니다.
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.query import QueryAnalysisResult, QueryIntent, QueryType, EntityType
from app.models.graph_query import CypherQuery, QueryResultType, QueryTemplate


class QueryTemplates:
    """
    사전 정의된 Cypher 쿼리 템플릿
    """

    # 1. 보장 금액 조회
    COVERAGE_AMOUNT = QueryTemplate(
        name="coverage_amount",
        description="특정 질병의 보장 금액 조회",
        template="""
MATCH (d:Disease)-[r:COVERS]-(c:Coverage)
WHERE d.korean_name = $disease_name
  OR d.standard_name = $disease_name
RETURN
  c.coverage_name as coverage_name,
  c.amount as amount,
  d.korean_name as disease_name,
  d.kcd_code as kcd_code,
  r.conditions as conditions
ORDER BY c.amount DESC
        """.strip(),
        required_params=["disease_name"],
        result_type=QueryResultType.TABLE,
    )

    # 2. 보장 여부 확인
    COVERAGE_CHECK = QueryTemplate(
        name="coverage_check",
        description="특정 질병이 보장되는지 확인",
        template="""
MATCH (d:Disease)
WHERE d.korean_name = $disease_name
  OR d.standard_name = $disease_name
OPTIONAL MATCH (d)-[r:COVERS]-(c:Coverage)
RETURN
  d.korean_name as disease_name,
  d.kcd_code as kcd_code,
  CASE WHEN c IS NOT NULL THEN true ELSE false END as is_covered,
  collect({
    coverage_name: c.coverage_name,
    amount: c.amount,
    conditions: r.conditions
  }) as coverages
        """.strip(),
        required_params=["disease_name"],
        result_type=QueryResultType.TABLE,
    )

    # 3. 질병 간 보장 비교
    DISEASE_COMPARISON = QueryTemplate(
        name="disease_comparison",
        description="두 질병의 보장 내용 비교",
        template="""
MATCH (d1:Disease)-[r1:COVERS]-(c1:Coverage)
WHERE d1.korean_name = $disease1
  OR d1.standard_name = $disease1

MATCH (d2:Disease)-[r2:COVERS]-(c2:Coverage)
WHERE d2.korean_name = $disease2
  OR d2.standard_name = $disease2

WITH d1, d2,
     collect(DISTINCT {name: c1.coverage_name, amount: c1.amount}) as cov1,
     collect(DISTINCT {name: c2.coverage_name, amount: c2.amount}) as cov2

RETURN
  d1.korean_name as disease1_name,
  d1.kcd_code as disease1_kcd,
  cov1,
  d2.korean_name as disease2_name,
  d2.kcd_code as disease2_kcd,
  cov2
        """.strip(),
        required_params=["disease1", "disease2"],
        result_type=QueryResultType.TABLE,
    )

    # 4. 제외 항목 조회
    EXCLUSIONS = QueryTemplate(
        name="exclusions",
        description="제외되는 질병 목록 조회",
        template="""
MATCH (p:Product)-[:EXCLUDES]->(d:Disease)
RETURN
  d.korean_name as disease_name,
  d.kcd_code as kcd_code,
  d.standard_name as standard_name
ORDER BY d.korean_name
        """.strip(),
        required_params=[],
        result_type=QueryResultType.TABLE,
    )

    # 5. 대기기간 조회
    WAITING_PERIOD = QueryTemplate(
        name="waiting_period",
        description="대기기간 조회",
        template="""
MATCH (c:Coverage)-[:HAS_CONDITION]->(cond:Condition)
WHERE cond.type = 'waiting_period'
OPTIONAL MATCH (c)-[:COVERS]-(d:Disease)
WHERE d.korean_name = $disease_name
  OR d.standard_name = $disease_name
  OR $disease_name IS NULL
RETURN
  c.coverage_name as coverage_name,
  cond.value as waiting_period_days,
  collect(d.korean_name) as diseases
        """.strip(),
        required_params=[],
        optional_params=["disease_name"],
        result_type=QueryResultType.TABLE,
    )

    # 6. 나이 제한 조회
    AGE_LIMIT = QueryTemplate(
        name="age_limit",
        description="나이 제한 조회",
        template="""
MATCH (p:Product)-[:HAS_CONDITION]->(cond:Condition)
WHERE cond.type = 'age_limit'
RETURN
  p.product_name as product_name,
  cond.min_age as min_age,
  cond.max_age as max_age
        """.strip(),
        required_params=[],
        result_type=QueryResultType.TABLE,
    )

    # 7. 보장 항목 전체 조회
    ALL_COVERAGES = QueryTemplate(
        name="all_coverages",
        description="모든 보장 항목 조회",
        template="""
MATCH (c:Coverage)
OPTIONAL MATCH (c)-[:COVERS]-(d:Disease)
RETURN
  c.coverage_name as coverage_name,
  c.amount as amount,
  collect(DISTINCT d.korean_name) as diseases
ORDER BY c.coverage_name
LIMIT $limit
        """.strip(),
        required_params=[],
        optional_params=["limit"],
        result_type=QueryResultType.TABLE,
    )

    # 8. 보장 간 비교
    COVERAGE_COMPARISON = QueryTemplate(
        name="coverage_comparison",
        description="두 보장의 차이 비교",
        template="""
MATCH (c1:Coverage)-[:COVERS]-(d1:Disease)
WHERE c1.coverage_name = $coverage1

MATCH (c2:Coverage)-[:COVERS]-(d2:Disease)
WHERE c2.coverage_name = $coverage2

WITH c1, c2,
     collect(DISTINCT {name: d1.korean_name, kcd: d1.kcd_code}) as dis1,
     collect(DISTINCT {name: d2.korean_name, kcd: d2.kcd_code}) as dis2

RETURN
  c1.coverage_name as coverage1_name,
  c1.amount as coverage1_amount,
  dis1 as coverage1_diseases,
  c2.coverage_name as coverage2_name,
  c2.amount as coverage2_amount,
  dis2 as coverage2_diseases
        """.strip(),
        required_params=["coverage1", "coverage2"],
        result_type=QueryResultType.TABLE,
    )

    # 9. KCD 코드로 조회
    DISEASE_BY_KCD = QueryTemplate(
        name="disease_by_kcd",
        description="KCD 코드로 질병 조회",
        template="""
MATCH (d:Disease)
WHERE d.kcd_code = $kcd_code
OPTIONAL MATCH (d)-[r:COVERS]-(c:Coverage)
RETURN
  d.korean_name as disease_name,
  d.standard_name as standard_name,
  d.kcd_code as kcd_code,
  collect({
    coverage_name: c.coverage_name,
    amount: c.amount,
    conditions: r.conditions
  }) as coverages
        """.strip(),
        required_params=["kcd_code"],
        result_type=QueryResultType.TABLE,
    )

    # 10. 벡터 유사도 검색
    VECTOR_SIMILARITY = QueryTemplate(
        name="vector_similarity",
        description="벡터 유사도 기반 조항 검색",
        template="""
CALL db.index.vector.queryNodes(
  'clause_embeddings',
  $top_k,
  $query_embedding
) YIELD node, score
RETURN
  node.clause_id as clause_id,
  node.article_num as article_num,
  node.clause_text as clause_text,
  score
ORDER BY score DESC
        """.strip(),
        required_params=["query_embedding", "top_k"],
        result_type=QueryResultType.TABLE,
    )


class CypherQueryBuilder:
    """
    Cypher 쿼리 빌더

    QueryAnalysisResult를 받아 적절한 Cypher 쿼리를 생성합니다.
    """

    def __init__(self):
        """초기화"""
        self.templates = QueryTemplates()

    def build(self, analysis: QueryAnalysisResult) -> CypherQuery:
        """
        분석 결과를 기반으로 Cypher 쿼리를 생성합니다.

        Args:
            analysis: 쿼리 분석 결과

        Returns:
            Cypher 쿼리
        """
        logger.info(f"Building Cypher query for intent: {analysis.intent}")

        # 의도에 따른 쿼리 생성
        if analysis.intent == QueryIntent.COVERAGE_AMOUNT:
            return self._build_coverage_amount_query(analysis)

        elif analysis.intent == QueryIntent.COVERAGE_CHECK:
            return self._build_coverage_check_query(analysis)

        elif analysis.intent == QueryIntent.DISEASE_COMPARISON:
            return self._build_disease_comparison_query(analysis)

        elif analysis.intent == QueryIntent.COVERAGE_COMPARISON:
            return self._build_coverage_comparison_query(analysis)

        elif analysis.intent == QueryIntent.EXCLUSION_CHECK:
            return self._build_exclusions_query(analysis)

        elif analysis.intent == QueryIntent.WAITING_PERIOD:
            return self._build_waiting_period_query(analysis)

        elif analysis.intent == QueryIntent.AGE_LIMIT:
            return self._build_age_limit_query(analysis)

        elif analysis.intent == QueryIntent.COVERAGE_INQUIRY:
            return self._build_all_coverages_query(analysis)

        elif analysis.intent == QueryIntent.PRODUCT_SUMMARY:
            return self._build_product_summary_query(analysis)

        else:
            # 기본: 벡터 검색 또는 전체 조회
            return self._build_default_query(analysis)

    def _build_coverage_amount_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """보장 금액 쿼리 생성"""
        diseases = analysis.get_diseases()

        if not diseases:
            raise ValueError("No disease entity found for coverage amount query")

        disease_name = diseases[0]

        return CypherQuery(
            query=self.templates.COVERAGE_AMOUNT.template,
            parameters={"disease_name": disease_name},
            result_type=QueryResultType.TABLE,
        )

    def _build_coverage_check_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """보장 여부 확인 쿼리 생성"""
        diseases = analysis.get_diseases()

        if not diseases:
            # KCD 코드로 시도
            kcd_entities = [
                e for e in analysis.entities if e.entity_type == EntityType.KCD_CODE
            ]
            if kcd_entities:
                return CypherQuery(
                    query=self.templates.DISEASE_BY_KCD.template,
                    parameters={"kcd_code": kcd_entities[0].text},
                    result_type=QueryResultType.TABLE,
                )
            raise ValueError("No disease or KCD code found for coverage check")

        disease_name = diseases[0]

        return CypherQuery(
            query=self.templates.COVERAGE_CHECK.template,
            parameters={"disease_name": disease_name},
            result_type=QueryResultType.TABLE,
        )

    def _build_disease_comparison_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """질병 비교 쿼리 생성"""
        diseases = analysis.get_diseases()

        if len(diseases) < 2:
            raise ValueError(
                f"Need at least 2 diseases for comparison, got {len(diseases)}"
            )

        return CypherQuery(
            query=self.templates.DISEASE_COMPARISON.template,
            parameters={"disease1": diseases[0], "disease2": diseases[1]},
            result_type=QueryResultType.TABLE,
        )

    def _build_coverage_comparison_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """보장 비교 쿼리 생성"""
        coverages = analysis.get_coverages()

        if len(coverages) < 2:
            raise ValueError(
                f"Need at least 2 coverages for comparison, got {len(coverages)}"
            )

        return CypherQuery(
            query=self.templates.COVERAGE_COMPARISON.template,
            parameters={"coverage1": coverages[0], "coverage2": coverages[1]},
            result_type=QueryResultType.TABLE,
        )

    def _build_exclusions_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """제외 항목 쿼리 생성"""
        return CypherQuery(
            query=self.templates.EXCLUSIONS.template,
            parameters={},
            result_type=QueryResultType.TABLE,
        )

    def _build_waiting_period_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """대기기간 쿼리 생성"""
        diseases = analysis.get_diseases()

        params = {}
        if diseases:
            params["disease_name"] = diseases[0]
        else:
            params["disease_name"] = None

        return CypherQuery(
            query=self.templates.WAITING_PERIOD.template,
            parameters=params,
            result_type=QueryResultType.TABLE,
        )

    def _build_age_limit_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """나이 제한 쿼리 생성"""
        return CypherQuery(
            query=self.templates.AGE_LIMIT.template,
            parameters={},
            result_type=QueryResultType.TABLE,
        )

    def _build_all_coverages_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """전체 보장 조회 쿼리 생성"""
        return CypherQuery(
            query=self.templates.ALL_COVERAGES.template,
            parameters={"limit": 20},
            result_type=QueryResultType.TABLE,
        )

    def _build_product_summary_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """상품 요약 쿼리 생성"""
        # 상품 기본 정보 + 주요 보장 조회
        query = """
MATCH (p:Product)
OPTIONAL MATCH (p)-[:HAS_COVERAGE]->(c:Coverage)
RETURN
  p.product_name as product_name,
  p.company as company,
  p.product_type as product_type,
  collect({
    coverage_name: c.coverage_name,
    amount: c.amount
  }) as main_coverages
LIMIT 1
        """.strip()

        return CypherQuery(
            query=query,
            parameters={},
            result_type=QueryResultType.TABLE,
        )

    def _build_default_query(
        self, analysis: QueryAnalysisResult
    ) -> CypherQuery:
        """기본 쿼리 생성 (전체 보장 조회)"""
        logger.warning(f"No specific query for intent {analysis.intent}, using default")
        return self._build_all_coverages_query(analysis)

    def build_custom_query(
        self, cypher: str, parameters: Dict[str, Any] = None
    ) -> CypherQuery:
        """
        커스텀 Cypher 쿼리 생성

        Args:
            cypher: Cypher 쿼리 문자열
            parameters: 쿼리 파라미터

        Returns:
            Cypher 쿼리
        """
        return CypherQuery(
            query=cypher,
            parameters=parameters or {},
            result_type=QueryResultType.TABLE,
        )

    def validate_query(self, query: CypherQuery) -> bool:
        """
        쿼리 유효성 검증

        Args:
            query: Cypher 쿼리

        Returns:
            유효 여부
        """
        # 기본 검증
        if not query.query or not query.query.strip():
            return False

        # Cypher 키워드 확인
        query_upper = query.query.upper()
        has_match = "MATCH" in query_upper
        has_return = "RETURN" in query_upper

        return has_match or has_return

    def get_template_by_name(self, name: str) -> Optional[QueryTemplate]:
        """
        이름으로 템플릿 가져오기

        Args:
            name: 템플릿 이름

        Returns:
            쿼리 템플릿
        """
        for attr_name in dir(self.templates):
            if attr_name.isupper():
                template = getattr(self.templates, attr_name)
                if isinstance(template, QueryTemplate) and template.name == name:
                    return template
        return None

    def list_templates(self) -> List[QueryTemplate]:
        """
        사용 가능한 모든 템플릿 목록

        Returns:
            템플릿 리스트
        """
        templates = []
        for attr_name in dir(self.templates):
            if attr_name.isupper():
                template = getattr(self.templates, attr_name)
                if isinstance(template, QueryTemplate):
                    templates.append(template)
        return templates
