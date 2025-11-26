"""
Entity Extractor

사용자 질문에서 엔티티를 추출합니다.
"""
import re
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models.query import EntityType, ExtractedEntity
from app.services.knowledge.disease_kb import DiseaseKnowledgeBase


class EntityExtractor:
    """
    엔티티 추출기

    사용자 질문에서 질병, 보장, 조건, 금액, 기간, KCD 코드 등을 추출합니다.
    """

    def __init__(
        self,
        disease_kb: Optional[DiseaseKnowledgeBase] = None,
        min_confidence: float = 0.5,
    ):
        """
        Args:
            disease_kb: 질병 지식 베이스 (엔티티 정규화에 사용)
            min_confidence: 최소 신뢰도 임계값
        """
        self.disease_kb = disease_kb
        self.min_confidence = min_confidence

        # 금액 패턴
        self.amount_patterns = [
            # 1천만원, 1억원
            (r"(\d+(?:,\d{3})*)\s*([천만억조])\s*원", self._parse_korean_amount),
            # 10,000,000원
            (r"(\d+(?:,\d{3})*)\s*원", self._parse_numeric_amount),
            # 1000만원
            (r"(\d+)\s*([천만억조])\s*원", self._parse_korean_amount),
        ]

        # 기간 패턴
        self.period_patterns = [
            # 90일, 3개월, 2년
            (r"(\d+)\s*(일|주|개월|월|년)", self._parse_period),
        ]

        # KCD 코드 패턴
        self.kcd_pattern = r"\b([A-Z]\d{2,3}(?:\.\d{1,2})?)\b"

        # 조건 키워드
        self.condition_keywords = [
            "대기기간",
            "면책기간",
            "나이제한",
            "연령제한",
            "가입나이",
            "최고나이",
            "최저나이",
            "보장개시일",
            "계약일",
        ]

        # 보장 키워드
        self.coverage_keywords = [
            "특약",
            "보장",
            "담보",
            "보험금",
            "급여",
            "지급",
        ]

    def extract(self, query: str) -> List[ExtractedEntity]:
        """
        질문에서 모든 엔티티를 추출합니다.

        Args:
            query: 사용자 질문

        Returns:
            추출된 엔티티 리스트
        """
        entities = []

        # 1. 금액 추출
        entities.extend(self._extract_amounts(query))

        # 2. 기간 추출
        entities.extend(self._extract_periods(query))

        # 3. KCD 코드 추출
        entities.extend(self._extract_kcd_codes(query))

        # 4. 조건 추출
        entities.extend(self._extract_conditions(query))

        # 5. 보장 추출
        entities.extend(self._extract_coverages(query))

        # 6. 질병 추출
        entities.extend(self._extract_diseases(query))

        # 신뢰도 기준으로 필터링
        entities = [e for e in entities if e.confidence >= self.min_confidence]

        # 위치 기준으로 정렬
        entities.sort(key=lambda e: e.start_pos or 0)

        logger.info(f"Extracted {len(entities)} entities from query")
        return entities

    def _extract_amounts(self, query: str) -> List[ExtractedEntity]:
        """금액 엔티티를 추출합니다."""
        entities = []

        for pattern, parser in self.amount_patterns:
            for match in re.finditer(pattern, query):
                amount_value = parser(match)
                if amount_value is None:
                    continue

                entity = ExtractedEntity(
                    text=match.group(0),
                    entity_type=EntityType.AMOUNT,
                    normalized_value=str(amount_value),
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
                entities.append(entity)

                logger.debug(f"Extracted amount: {match.group(0)} -> {amount_value}")

        return entities

    def _parse_korean_amount(self, match: re.Match) -> Optional[int]:
        """한글 금액을 숫자로 변환합니다."""
        try:
            number_str = match.group(1).replace(",", "")
            unit = match.group(2)

            number = int(number_str)

            # 단위 변환
            multipliers = {
                "천": 1_000,
                "만": 10_000,
                "억": 100_000_000,
                "조": 1_000_000_000_000,
            }

            return number * multipliers.get(unit, 1)

        except (ValueError, IndexError):
            return None

    def _parse_numeric_amount(self, match: re.Match) -> Optional[int]:
        """숫자 금액을 파싱합니다."""
        try:
            amount_str = match.group(1).replace(",", "")
            return int(amount_str)
        except (ValueError, IndexError):
            return None

    def _extract_periods(self, query: str) -> List[ExtractedEntity]:
        """기간 엔티티를 추출합니다."""
        entities = []

        for pattern, parser in self.period_patterns:
            for match in re.finditer(pattern, query):
                days = parser(match)
                if days is None:
                    continue

                entity = ExtractedEntity(
                    text=match.group(0),
                    entity_type=EntityType.PERIOD,
                    normalized_value=f"{days}일",
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
                entities.append(entity)

                logger.debug(f"Extracted period: {match.group(0)} -> {days}일")

        return entities

    def _parse_period(self, match: re.Match) -> Optional[int]:
        """기간을 일 단위로 변환합니다."""
        try:
            number = int(match.group(1))
            unit = match.group(2)

            # 단위 변환
            if unit in ["일"]:
                return number
            elif unit in ["주"]:
                return number * 7
            elif unit in ["개월", "월"]:
                return number * 30  # 근사값
            elif unit in ["년"]:
                return number * 365  # 근사값

            return None

        except (ValueError, IndexError):
            return None

    def _extract_kcd_codes(self, query: str) -> List[ExtractedEntity]:
        """KCD 코드 엔티티를 추출합니다."""
        entities = []

        for match in re.finditer(self.kcd_pattern, query):
            code = match.group(1)

            # KCD 코드 형식 검증
            if not self._is_valid_kcd_code(code):
                continue

            entity = ExtractedEntity(
                text=code,
                entity_type=EntityType.KCD_CODE,
                normalized_value=code.upper(),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
            )
            entities.append(entity)

            logger.debug(f"Extracted KCD code: {code}")

        return entities

    def _is_valid_kcd_code(self, code: str) -> bool:
        """KCD 코드 형식이 유효한지 검증합니다."""
        # 기본 형식: 알파벳 1자 + 숫자 2~3자 (+ 선택적으로 .숫자)
        # 예: C73, C22, C73.9
        pattern = r"^[A-Z]\d{2,3}(?:\.\d{1,2})?$"
        return bool(re.match(pattern, code))

    def _extract_conditions(self, query: str) -> List[ExtractedEntity]:
        """조건 엔티티를 추출합니다."""
        entities = []

        for keyword in self.condition_keywords:
            if keyword in query:
                start_pos = query.find(keyword)
                entity = ExtractedEntity(
                    text=keyword,
                    entity_type=EntityType.CONDITION,
                    normalized_value=keyword,
                    confidence=0.8,
                    start_pos=start_pos,
                    end_pos=start_pos + len(keyword),
                )
                entities.append(entity)

                logger.debug(f"Extracted condition: {keyword}")

        return entities

    def _extract_coverages(self, query: str) -> List[ExtractedEntity]:
        """보장 엔티티를 추출합니다."""
        entities = []

        # 특약/보장 패턴 (예: "암진단특약", "수술보장")
        coverage_pattern = r"(\w+)(특약|보장|담보)"

        for match in re.finditer(coverage_pattern, query):
            coverage_name = match.group(0)

            # 너무 짧은 이름은 제외
            if len(coverage_name) < 3:
                continue

            entity = ExtractedEntity(
                text=coverage_name,
                entity_type=EntityType.COVERAGE,
                normalized_value=coverage_name,
                confidence=0.75,
                start_pos=match.start(),
                end_pos=match.end(),
            )
            entities.append(entity)

            logger.debug(f"Extracted coverage: {coverage_name}")

        return entities

    def _extract_diseases(self, query: str) -> List[ExtractedEntity]:
        """질병 엔티티를 추출합니다."""
        entities = []

        if self.disease_kb:
            # 지식 베이스를 사용한 정확한 매칭
            entities.extend(self._extract_diseases_with_kb(query))
        else:
            # 패턴 기반 추출
            entities.extend(self._extract_diseases_with_pattern(query))

        return entities

    def _extract_diseases_with_kb(self, query: str) -> List[ExtractedEntity]:
        """지식 베이스를 사용하여 질병을 추출합니다."""
        entities = []

        # 모든 질병명에 대해 질문에 포함되어 있는지 확인
        for disease in self.disease_kb.get_all_diseases():
            # 한국어 이름 확인
            for korean_name in disease.get("korean_names", []):
                if korean_name in query:
                    start_pos = query.find(korean_name)
                    entity = ExtractedEntity(
                        text=korean_name,
                        entity_type=EntityType.DISEASE,
                        normalized_value=disease["standard_name"],
                        confidence=0.9,
                        start_pos=start_pos,
                        end_pos=start_pos + len(korean_name),
                    )
                    entities.append(entity)

                    logger.debug(
                        f"Extracted disease (KB): {korean_name} -> "
                        f"{disease['standard_name']}"
                    )

        return entities

    def _extract_diseases_with_pattern(self, query: str) -> List[ExtractedEntity]:
        """패턴 기반으로 질병을 추출합니다."""
        entities = []

        # 질병 키워드 패턴 (암, 종양, 질환, 질병, 증후군 등)
        disease_suffixes = ["암", "종양", "질환", "질병", "증후군", "염", "출혈"]

        for suffix in disease_suffixes:
            # 예: "갑상선암", "뇌출혈"
            pattern = rf"(\w{{2,}}){re.escape(suffix)}"

            for match in re.finditer(pattern, query):
                disease_name = match.group(0)

                # 너무 짧은 이름은 제외
                if len(disease_name) < 3:
                    continue

                entity = ExtractedEntity(
                    text=disease_name,
                    entity_type=EntityType.DISEASE,
                    normalized_value=disease_name,
                    confidence=0.7,  # KB 사용 시보다 낮은 신뢰도
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
                entities.append(entity)

                logger.debug(f"Extracted disease (pattern): {disease_name}")

        return entities

    def get_entities_by_type(
        self, entities: List[ExtractedEntity], entity_type: EntityType
    ) -> List[ExtractedEntity]:
        """특정 타입의 엔티티만 필터링합니다."""
        return [e for e in entities if e.entity_type == entity_type]

    def deduplicate_entities(
        self, entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """
        중복된 엔티티를 제거합니다.

        같은 위치에 여러 엔티티가 있을 경우 신뢰도가 높은 것을 선택합니다.
        """
        if not entities:
            return []

        # 위치별로 그룹화
        position_groups: Dict[tuple, List[ExtractedEntity]] = {}

        for entity in entities:
            key = (entity.start_pos, entity.end_pos)
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append(entity)

        # 각 그룹에서 신뢰도가 가장 높은 엔티티 선택
        deduped = []
        for group in position_groups.values():
            best_entity = max(group, key=lambda e: e.confidence)
            deduped.append(best_entity)

        return deduped


class LLMEntityExtractor(EntityExtractor):
    """
    LLM 기반 엔티티 추출기

    패턴 기반 추출이 어려운 경우 LLM을 사용합니다.
    """

    def __init__(
        self,
        llm_client=None,
        disease_kb: Optional[DiseaseKnowledgeBase] = None,
        min_confidence: float = 0.5,
        use_llm_fallback: bool = True,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            disease_kb: 질병 지식 베이스
            min_confidence: 최소 신뢰도
            use_llm_fallback: LLM 폴백 사용 여부
        """
        super().__init__(disease_kb, min_confidence)
        self.llm_client = llm_client
        self.use_llm_fallback = use_llm_fallback

    async def extract_with_llm(self, query: str) -> List[ExtractedEntity]:
        """
        LLM을 사용하여 엔티티를 추출합니다.

        Args:
            query: 사용자 질문

        Returns:
            추출된 엔티티 리스트
        """
        if not self.llm_client:
            logger.warning("LLM client not configured, using pattern-based extraction")
            return self.extract(query)

        try:
            # 먼저 패턴 기반 추출 시도
            pattern_entities = self.extract(query)

            # 충분한 엔티티가 추출되었으면 LLM 사용 안 함
            if not self.use_llm_fallback or len(pattern_entities) >= 3:
                return pattern_entities

            # LLM으로 추가 추출
            prompt = self._build_extraction_prompt(query)

            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            llm_entities = self._parse_llm_entities(response, query)

            # 패턴 기반 + LLM 결과 병합
            all_entities = pattern_entities + llm_entities

            # 중복 제거
            all_entities = self.deduplicate_entities(all_entities)

            logger.info(
                f"Extracted {len(all_entities)} entities "
                f"(pattern: {len(pattern_entities)}, LLM: {len(llm_entities)})"
            )

            return all_entities

        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            # 실패 시 패턴 기반 결과 반환
            return self.extract(query)

    def _build_extraction_prompt(self, query: str) -> str:
        """LLM 엔티티 추출 프롬프트를 생성합니다."""
        prompt = f"""다음 질문에서 엔티티를 추출해주세요.

질문: "{query}"

추출할 엔티티 타입:
- disease: 질병명 (예: 갑상선암, 간암)
- coverage: 보장명 (예: 암진단특약, 수술보장)
- condition: 조건 (예: 대기기간, 나이제한)
- amount: 금액 (예: 1천만원, 1억원)
- period: 기간 (예: 90일, 3개월)
- kcd_code: KCD 코드 (예: C73, C22)

응답 형식:
{{
    "entities": [
        {{
            "text": "추출된 텍스트",
            "type": "엔티티 타입",
            "normalized": "정규화된 값",
            "confidence": 0.0~1.0
        }}
    ]
}}

JSON 형식으로만 응답해주세요."""

        return prompt

    def _parse_llm_entities(
        self, response: str, original_query: str
    ) -> List[ExtractedEntity]:
        """LLM 응답에서 엔티티를 파싱합니다."""
        import json

        entities = []

        try:
            data = json.loads(response)

            for entity_data in data.get("entities", []):
                text = entity_data.get("text", "")
                entity_type_str = entity_data.get("type", "")
                normalized = entity_data.get("normalized")
                confidence = float(entity_data.get("confidence", 0.5))

                # 엔티티 타입 변환
                try:
                    entity_type = EntityType(entity_type_str)
                except ValueError:
                    logger.warning(f"Unknown entity type: {entity_type_str}")
                    continue

                # 원본 질문에서 위치 찾기
                start_pos = original_query.find(text)
                end_pos = start_pos + len(text) if start_pos >= 0 else None

                entity = ExtractedEntity(
                    text=text,
                    entity_type=entity_type,
                    normalized_value=normalized,
                    confidence=confidence,
                    start_pos=start_pos if start_pos >= 0 else None,
                    end_pos=end_pos,
                )
                entities.append(entity)

        except Exception as e:
            logger.error(f"Failed to parse LLM entities: {e}")

        return entities
