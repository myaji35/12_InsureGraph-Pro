"""
Intent Detector

사용자 질문의 의도를 감지합니다.
"""
import re
from typing import List, Tuple, Optional
from loguru import logger

from app.models.query import (
    QueryIntent,
    IntentPattern,
    INTENT_PATTERNS,
)


class IntentDetector:
    """
    질문 의도 감지기

    패턴 매칭과 키워드 분석을 통해 사용자 질문의 의도를 파악합니다.
    """

    def __init__(
        self,
        patterns: Optional[List[IntentPattern]] = None,
        min_confidence_threshold: float = 0.3,
    ):
        """
        Args:
            patterns: 사용할 의도 패턴 목록 (기본값: INTENT_PATTERNS)
            min_confidence_threshold: 최소 신뢰도 임계값
        """
        self.patterns = patterns or INTENT_PATTERNS
        self.min_confidence_threshold = min_confidence_threshold

        # 우선순위별로 정렬
        self.patterns = sorted(self.patterns, key=lambda p: p.priority, reverse=True)

    def detect(self, query: str) -> Tuple[QueryIntent, float]:
        """
        질문의 의도를 감지합니다.

        Args:
            query: 사용자 질문

        Returns:
            (의도, 신뢰도) 튜플
        """
        query_lower = query.lower().strip()

        if not query_lower:
            return QueryIntent.UNKNOWN, 0.0

        # 각 패턴에 대해 매칭 점수 계산
        scores = []
        for pattern in self.patterns:
            score = self._calculate_pattern_score(query_lower, pattern)
            scores.append((pattern.intent, score))

            logger.debug(f"Pattern {pattern.intent}: score={score:.3f}")

        # 가장 높은 점수 선택
        if not scores:
            return QueryIntent.UNKNOWN, 0.0

        scores.sort(key=lambda x: x[1], reverse=True)
        best_intent, best_score = scores[0]

        # 임계값 미달 시 UNKNOWN
        if best_score < self.min_confidence_threshold:
            logger.warning(
                f"Best score {best_score:.3f} below threshold "
                f"{self.min_confidence_threshold:.3f}"
            )
            return QueryIntent.UNKNOWN, best_score

        logger.info(f"Detected intent: {best_intent} (confidence={best_score:.3f})")
        return best_intent, best_score

    def _calculate_pattern_score(
        self, query: str, pattern: IntentPattern
    ) -> float:
        """
        패턴에 대한 매칭 점수를 계산합니다.

        Args:
            query: 정규화된 질문 (소문자)
            pattern: 의도 패턴

        Returns:
            0.0 ~ 1.0 사이의 점수
        """
        score = 0.0
        max_score = 0.0

        # 1. 패턴 매칭 (50% 가중치)
        pattern_weight = 0.5
        max_score += pattern_weight

        pattern_matches = sum(
            1 for p in pattern.patterns if p.lower() in query
        )
        if pattern.patterns:
            pattern_score = pattern_matches / len(pattern.patterns)
            score += pattern_score * pattern_weight

        # 2. 키워드 매칭 (30% 가중치)
        keyword_weight = 0.3
        max_score += keyword_weight

        if pattern.keywords:
            keyword_matches = sum(
                1 for k in pattern.keywords if k.lower() in query
            )
            keyword_score = keyword_matches / len(pattern.keywords)
            score += keyword_score * keyword_weight

        # 3. 우선순위 보너스 (20% 가중치)
        priority_weight = 0.2
        max_score += priority_weight

        # 우선순위를 0~1 사이로 정규화 (1~5 범위 가정)
        normalized_priority = min(pattern.priority / 5.0, 1.0)
        score += normalized_priority * priority_weight

        # 정규화
        if max_score > 0:
            score = score / max_score

        return score

    def detect_multiple(
        self, query: str, top_k: int = 3
    ) -> List[Tuple[QueryIntent, float]]:
        """
        상위 K개의 의도를 반환합니다.

        Args:
            query: 사용자 질문
            top_k: 반환할 의도 개수

        Returns:
            (의도, 신뢰도) 튜플 리스트
        """
        query_lower = query.lower().strip()

        if not query_lower:
            return [(QueryIntent.UNKNOWN, 0.0)]

        # 모든 패턴 점수 계산
        scores = []
        for pattern in self.patterns:
            score = self._calculate_pattern_score(query_lower, pattern)
            scores.append((pattern.intent, score))

        # 점수 정렬 및 상위 K개 선택
        scores.sort(key=lambda x: x[1], reverse=True)

        # 임계값 이상만 필터링
        filtered_scores = [
            (intent, score)
            for intent, score in scores[:top_k]
            if score >= self.min_confidence_threshold
        ]

        # 결과가 없으면 UNKNOWN 반환
        if not filtered_scores:
            return [(QueryIntent.UNKNOWN, scores[0][1] if scores else 0.0)]

        return filtered_scores

    def is_complex_query(self, query: str) -> bool:
        """
        복잡한 질문인지 판단합니다.

        복잡한 질문의 기준:
        - 여러 의도가 섞여 있을 가능성
        - 상위 2개 의도의 점수 차이가 작음

        Args:
            query: 사용자 질문

        Returns:
            복잡한 질문 여부
        """
        top_intents = self.detect_multiple(query, top_k=2)

        # 상위 2개가 없거나 하나만 있으면 단순 질문
        if len(top_intents) < 2:
            return False

        # 점수 차이가 0.2 미만이면 복잡한 질문
        score_diff = top_intents[0][1] - top_intents[1][1]
        is_complex = score_diff < 0.2

        if is_complex:
            logger.info(
                f"Complex query detected: "
                f"{top_intents[0][0]} ({top_intents[0][1]:.3f}) vs "
                f"{top_intents[1][0]} ({top_intents[1][1]:.3f})"
            )

        return is_complex

    def add_pattern(self, pattern: IntentPattern):
        """새로운 패턴을 추가합니다."""
        self.patterns.append(pattern)
        # 우선순위별로 재정렬
        self.patterns = sorted(
            self.patterns, key=lambda p: p.priority, reverse=True
        )
        logger.info(f"Added new pattern for intent: {pattern.intent}")

    def remove_pattern(self, intent: QueryIntent):
        """특정 의도의 패턴을 제거합니다."""
        self.patterns = [p for p in self.patterns if p.intent != intent]
        logger.info(f"Removed pattern for intent: {intent}")


class LLMIntentDetector(IntentDetector):
    """
    LLM 기반 의도 감지기

    패턴 매칭으로 해결되지 않는 복잡한 질문에 대해
    LLM을 사용하여 의도를 감지합니다.
    """

    def __init__(
        self,
        llm_client=None,
        patterns: Optional[List[IntentPattern]] = None,
        min_confidence_threshold: float = 0.3,
        use_llm_for_complex: bool = True,
    ):
        """
        Args:
            llm_client: LLM 클라이언트 (OpenAI, Upstage 등)
            patterns: 사용할 의도 패턴 목록
            min_confidence_threshold: 최소 신뢰도 임계값
            use_llm_for_complex: 복잡한 질문에 LLM 사용 여부
        """
        super().__init__(patterns, min_confidence_threshold)
        self.llm_client = llm_client
        self.use_llm_for_complex = use_llm_for_complex

    async def detect_with_llm(self, query: str) -> Tuple[QueryIntent, float]:
        """
        LLM을 사용하여 의도를 감지합니다.

        Args:
            query: 사용자 질문

        Returns:
            (의도, 신뢰도) 튜플
        """
        if not self.llm_client:
            logger.warning("LLM client not configured, falling back to pattern matching")
            return self.detect(query)

        # 복잡한 질문인지 확인
        if self.use_llm_for_complex and not self.is_complex_query(query):
            # 단순한 질문은 패턴 매칭으로 충분
            return self.detect(query)

        try:
            # LLM 프롬프트 구성
            prompt = self._build_intent_prompt(query)

            # LLM 호출
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            # 응답 파싱
            intent, confidence = self._parse_llm_response(response)

            logger.info(
                f"LLM detected intent: {intent} (confidence={confidence:.3f})"
            )
            return intent, confidence

        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            # 실패 시 패턴 매칭으로 폴백
            return self.detect(query)

    def _build_intent_prompt(self, query: str) -> str:
        """LLM 의도 감지 프롬프트를 생성합니다."""
        intent_descriptions = "\n".join([
            f"- {intent.value}: {self._get_intent_description(intent)}"
            for intent in QueryIntent
            if intent != QueryIntent.UNKNOWN
        ])

        prompt = f"""다음 사용자 질문의 의도를 분석해주세요.

질문: "{query}"

가능한 의도:
{intent_descriptions}

응답 형식:
{{
    "intent": "의도 타입",
    "confidence": 0.0~1.0 사이의 신뢰도,
    "reasoning": "판단 근거"
}}

JSON 형식으로만 응답해주세요."""

        return prompt

    def _get_intent_description(self, intent: QueryIntent) -> str:
        """의도에 대한 설명을 반환합니다."""
        descriptions = {
            QueryIntent.COVERAGE_INQUIRY: "보장 내용을 묻는 질문",
            QueryIntent.COVERAGE_AMOUNT: "보장 금액을 묻는 질문",
            QueryIntent.COVERAGE_CHECK: "특정 질병/상황의 보장 여부를 묻는 질문",
            QueryIntent.EXCLUSION_CHECK: "제외되는 항목을 묻는 질문",
            QueryIntent.CONDITION_INQUIRY: "보험금 지급 조건을 묻는 질문",
            QueryIntent.WAITING_PERIOD: "대기기간을 묻는 질문",
            QueryIntent.AGE_LIMIT: "나이 제한을 묻는 질문",
            QueryIntent.DISEASE_COMPARISON: "질병 간 보장 차이를 묻는 질문",
            QueryIntent.COVERAGE_COMPARISON: "보장 항목 간 비교를 묻는 질문",
            QueryIntent.GENERAL_INFO: "일반적인 정보를 묻는 질문",
            QueryIntent.PRODUCT_SUMMARY: "상품 요약을 요청하는 질문",
            QueryIntent.COMPLEX_QUERY: "여러 의도가 섞인 복잡한 질문",
        }
        return descriptions.get(intent, "")

    def _parse_llm_response(self, response: str) -> Tuple[QueryIntent, float]:
        """LLM 응답을 파싱합니다."""
        import json

        try:
            # JSON 파싱
            data = json.loads(response)

            # 의도 추출
            intent_str = data.get("intent", "unknown")
            try:
                intent = QueryIntent(intent_str)
            except ValueError:
                intent = QueryIntent.UNKNOWN

            # 신뢰도 추출
            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))  # 0~1 사이로 클램핑

            return intent, confidence

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return QueryIntent.UNKNOWN, 0.0
