"""
Query Analyzer

사용자 질문을 종합적으로 분석합니다.
"""
import re
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models.query import (
    QueryAnalysisResult,
    QueryIntent,
    QueryType,
    QueryContext,
    ExtractedEntity,
    EntityType,
)
from app.services.query.intent_detector import IntentDetector
from app.services.query.entity_extractor import EntityExtractor


class QueryAnalyzer:
    """
    질의 분석기

    사용자 질문의 의도, 엔티티, 쿼리 타입 등을 종합적으로 분석합니다.
    """

    def __init__(
        self,
        intent_detector: Optional[IntentDetector] = None,
        entity_extractor: Optional[EntityExtractor] = None,
    ):
        """
        Args:
            intent_detector: 의도 감지기
            entity_extractor: 엔티티 추출기
        """
        self.intent_detector = intent_detector or IntentDetector()
        self.entity_extractor = entity_extractor or EntityExtractor()

    def analyze(
        self, query: str, context: Optional[QueryContext] = None
    ) -> QueryAnalysisResult:
        """
        질문을 종합적으로 분석합니다.

        Args:
            query: 사용자 질문
            context: 대화 컨텍스트 (선택)

        Returns:
            분석 결과
        """
        logger.info(f"Analyzing query: {query}")

        # 1. 의도 감지
        intent, intent_confidence = self.intent_detector.detect(query)

        # 2. 엔티티 추출
        entities = self.entity_extractor.extract(query)

        # 3. 쿼리 타입 결정
        query_type = self._determine_query_type(intent, entities, context)

        # 4. 키워드 추출
        keywords = self._extract_keywords(query, entities)

        # 5. 질문 재구성 (필요시)
        reformulated_query = self._reformulate_query(query, intent, entities, context)

        # 6. 답변 가능 여부 판단
        is_answerable = self._check_answerability(intent, entities)

        # 7. 명확화 제안 (필요시)
        suggested_clarification = self._suggest_clarification(
            query, intent, entities, is_answerable
        )

        # 8. 언어 감지
        language = self._detect_language(query)

        result = QueryAnalysisResult(
            original_query=query,
            intent=intent,
            intent_confidence=intent_confidence,
            query_type=query_type,
            entities=entities,
            reformulated_query=reformulated_query,
            keywords=keywords,
            language=language,
            is_answerable=is_answerable,
            suggested_clarification=suggested_clarification,
        )

        logger.info(
            f"Analysis complete: intent={intent}, "
            f"query_type={query_type}, entities={len(entities)}"
        )

        return result

    def _determine_query_type(
        self,
        intent: QueryIntent,
        entities: List[ExtractedEntity],
        context: Optional[QueryContext],
    ) -> QueryType:
        """
        쿼리 실행 타입을 결정합니다.

        Args:
            intent: 질문 의도
            entities: 추출된 엔티티
            context: 대화 컨텍스트

        Returns:
            쿼리 타입
        """
        # 1. 비교 질문 → 그래프 순회
        if intent in [QueryIntent.DISEASE_COMPARISON, QueryIntent.COVERAGE_COMPARISON]:
            return QueryType.GRAPH_TRAVERSAL

        # 2. 특정 엔티티가 있는 경우 → Hybrid
        has_disease = any(e.entity_type == EntityType.DISEASE for e in entities)
        has_coverage = any(e.entity_type == EntityType.COVERAGE for e in entities)

        if has_disease or has_coverage:
            # 구체적인 엔티티 + 조건/금액 질문 → 그래프 순회
            if intent in [
                QueryIntent.COVERAGE_AMOUNT,
                QueryIntent.COVERAGE_CHECK,
                QueryIntent.CONDITION_INQUIRY,
            ]:
                return QueryType.GRAPH_TRAVERSAL

            # 구체적인 엔티티 + 일반 질문 → Hybrid
            return QueryType.HYBRID

        # 3. 일반적인 질문 → 벡터 검색
        if intent in [
            QueryIntent.GENERAL_INFO,
            QueryIntent.PRODUCT_SUMMARY,
            QueryIntent.COVERAGE_INQUIRY,
        ]:
            return QueryType.VECTOR_SEARCH

        # 4. 조건 관련 질문 → 직접 조회
        if intent in [
            QueryIntent.WAITING_PERIOD,
            QueryIntent.AGE_LIMIT,
            QueryIntent.EXCLUSION_CHECK,
        ]:
            return QueryType.DIRECT_LOOKUP

        # 5. 복잡한 질문 → Hybrid
        if intent == QueryIntent.COMPLEX_QUERY:
            return QueryType.HYBRID

        # 6. 기본값 → Hybrid
        return QueryType.HYBRID

    def _extract_keywords(
        self, query: str, entities: List[ExtractedEntity]
    ) -> List[str]:
        """
        주요 키워드를 추출합니다.

        Args:
            query: 사용자 질문
            entities: 추출된 엔티티

        Returns:
            키워드 리스트
        """
        keywords = []

        # 1. 엔티티에서 키워드 추출
        for entity in entities:
            if entity.normalized_value:
                keywords.append(entity.normalized_value)
            else:
                keywords.append(entity.text)

        # 2. 불용어 제거 및 명사 추출
        stopwords = {
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "에서",
            "로",
            "으로",
            "과",
            "와",
            "도",
            "만",
            "까지",
            "부터",
            "뿐",
            "이나",
            "나",
            "하고",
            "이다",
            "있다",
            "없다",
            "되다",
            "하다",
            "이",
            "그",
            "저",
            "것",
            "수",
            "등",
            "및",
        }

        # 단순 토큰화 (공백 기준)
        tokens = query.split()

        for token in tokens:
            # 불용어 제거
            cleaned = token.strip()
            if cleaned and cleaned not in stopwords and len(cleaned) > 1:
                # 이미 엔티티에 포함된 것은 제외
                if not any(cleaned in e.text for e in entities):
                    keywords.append(cleaned)

        # 중복 제거
        keywords = list(dict.fromkeys(keywords))

        return keywords[:10]  # 최대 10개

    def _reformulate_query(
        self,
        query: str,
        intent: QueryIntent,
        entities: List[ExtractedEntity],
        context: Optional[QueryContext],
    ) -> Optional[str]:
        """
        질문을 재구성합니다.

        Args:
            query: 원본 질문
            intent: 의도
            entities: 엔티티
            context: 컨텍스트

        Returns:
            재구성된 질문 (필요시)
        """
        # 1. 대명사 해소 (컨텍스트 활용)
        if context and ("이", "그", "저") in query:
            # 이전 질문에서 언급된 엔티티 참조
            if context.previous_queries:
                # 간단한 구현: 이전 질문을 참고하여 재구성
                reformulated = self._resolve_pronouns(query, context)
                if reformulated != query:
                    return reformulated

        # 2. 생략된 정보 보완
        if intent == QueryIntent.COVERAGE_AMOUNT:
            diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]
            if not diseases and context and context.previous_queries:
                # 이전 질문에서 질병 정보 가져오기
                # (실제 구현에서는 이전 분석 결과를 컨텍스트에 저장해야 함)
                pass

        # 3. 비교 질문 명확화
        if intent in [QueryIntent.DISEASE_COMPARISON, QueryIntent.COVERAGE_COMPARISON]:
            diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]
            coverages = [e for e in entities if e.entity_type == EntityType.COVERAGE]

            if len(diseases) >= 2:
                return f"{diseases[0].text}와 {diseases[1].text}의 보장 차이는 무엇인가요?"
            elif len(coverages) >= 2:
                return f"{coverages[0].text}와 {coverages[1].text}의 차이는 무엇인가요?"

        return None

    def _resolve_pronouns(
        self, query: str, context: QueryContext
    ) -> str:
        """대명사를 해소합니다."""
        # 간단한 구현: "이", "그", "저" → 이전 질문의 엔티티로 대체
        # 실제로는 더 정교한 대명사 해소 알고리즘 필요
        return query

    def _check_answerability(
        self, intent: QueryIntent, entities: List[ExtractedEntity]
    ) -> bool:
        """
        답변 가능 여부를 판단합니다.

        Args:
            intent: 의도
            entities: 엔티티

        Returns:
            답변 가능 여부
        """
        # 1. 의도를 파악하지 못한 경우
        if intent == QueryIntent.UNKNOWN:
            return False

        # 2. 특정 질문인데 필수 엔티티가 없는 경우
        if intent == QueryIntent.COVERAGE_AMOUNT:
            # 금액 질문인데 질병이나 보장이 없으면 답변 불가
            has_disease = any(e.entity_type == EntityType.DISEASE for e in entities)
            has_coverage = any(e.entity_type == EntityType.COVERAGE for e in entities)
            if not (has_disease or has_coverage):
                return False

        if intent in [QueryIntent.COVERAGE_CHECK, QueryIntent.EXCLUSION_CHECK]:
            # 보장 확인인데 질병이 없으면 답변 불가
            has_disease = any(e.entity_type == EntityType.DISEASE for e in entities)
            if not has_disease:
                return False

        # 3. 비교 질문인데 비교 대상이 부족한 경우
        if intent == QueryIntent.DISEASE_COMPARISON:
            diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]
            if len(diseases) < 2:
                return False

        if intent == QueryIntent.COVERAGE_COMPARISON:
            coverages = [e for e in entities if e.entity_type == EntityType.COVERAGE]
            if len(coverages) < 2:
                return False

        return True

    def _suggest_clarification(
        self,
        query: str,
        intent: QueryIntent,
        entities: List[ExtractedEntity],
        is_answerable: bool,
    ) -> Optional[str]:
        """
        명확화가 필요한 경우 제안을 생성합니다.

        Args:
            query: 질문
            intent: 의도
            entities: 엔티티
            is_answerable: 답변 가능 여부

        Returns:
            명확화 제안
        """
        if is_answerable:
            return None

        # 1. 의도 불명확
        if intent == QueryIntent.UNKNOWN:
            return "질문을 좀 더 구체적으로 말씀해 주시겠어요?"

        # 2. 필수 엔티티 누락
        if intent == QueryIntent.COVERAGE_AMOUNT:
            has_disease = any(e.entity_type == EntityType.DISEASE for e in entities)
            has_coverage = any(e.entity_type == EntityType.COVERAGE for e in entities)
            if not (has_disease or has_coverage):
                return "어떤 질병이나 보장에 대한 금액을 알고 싶으신가요?"

        if intent in [QueryIntent.COVERAGE_CHECK, QueryIntent.EXCLUSION_CHECK]:
            has_disease = any(e.entity_type == EntityType.DISEASE for e in entities)
            if not has_disease:
                return "어떤 질병에 대해 확인하고 싶으신가요?"

        # 3. 비교 대상 부족
        if intent == QueryIntent.DISEASE_COMPARISON:
            diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]
            if len(diseases) == 1:
                return f"{diseases[0].text}와 어떤 질병을 비교하고 싶으신가요?"
            elif len(diseases) == 0:
                return "어떤 질병들을 비교하고 싶으신가요?"

        if intent == QueryIntent.COVERAGE_COMPARISON:
            coverages = [e for e in entities if e.entity_type == EntityType.COVERAGE]
            if len(coverages) == 1:
                return f"{coverages[0].text}와 어떤 보장을 비교하고 싶으신가요?"
            elif len(coverages) == 0:
                return "어떤 보장들을 비교하고 싶으신가요?"

        return "질문을 좀 더 명확하게 말씀해 주시겠어요?"

    def _detect_language(self, query: str) -> str:
        """
        질문의 언어를 감지합니다.

        Args:
            query: 질문

        Returns:
            언어 코드 (ko, en, etc.)
        """
        # 한글 패턴
        korean_pattern = re.compile(r"[가-힣]")

        # 영문 패턴
        english_pattern = re.compile(r"[a-zA-Z]")

        korean_count = len(korean_pattern.findall(query))
        english_count = len(english_pattern.findall(query))

        if korean_count > english_count:
            return "ko"
        elif english_count > 0:
            return "en"
        else:
            return "ko"  # 기본값

    def analyze_batch(
        self, queries: List[str], context: Optional[QueryContext] = None
    ) -> List[QueryAnalysisResult]:
        """
        여러 질문을 일괄 분석합니다.

        Args:
            queries: 질문 리스트
            context: 대화 컨텍스트

        Returns:
            분석 결과 리스트
        """
        results = []

        for query in queries:
            result = self.analyze(query, context)
            results.append(result)

            # 컨텍스트 업데이트 (다음 질문에 활용)
            if context:
                context.add_query(query, result.intent)

        return results

    def get_analysis_summary(self, result: QueryAnalysisResult) -> str:
        """
        분석 결과 요약을 생성합니다.

        Args:
            result: 분석 결과

        Returns:
            요약 문자열
        """
        summary_parts = [
            f"질문: {result.original_query}",
            f"의도: {result.intent.value} (신뢰도: {result.intent_confidence:.2f})",
            f"쿼리 타입: {result.query_type.value}",
            f"엔티티: {len(result.entities)}개",
        ]

        if result.entities:
            entity_summary = ", ".join(
                [f"{e.entity_type.value}:{e.text}" for e in result.entities[:3]]
            )
            if len(result.entities) > 3:
                entity_summary += f" 외 {len(result.entities) - 3}개"
            summary_parts.append(f"  - {entity_summary}")

        if result.keywords:
            keyword_summary = ", ".join(result.keywords[:5])
            summary_parts.append(f"키워드: {keyword_summary}")

        if not result.is_answerable:
            summary_parts.append(f"⚠️ 답변 불가: {result.suggested_clarification}")

        return "\n".join(summary_parts)
