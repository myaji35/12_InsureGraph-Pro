"""
Rule-based Entity Extractor for Insurance Documents

보험 문서에서 규칙 기반으로 엔티티를 추출합니다.
외부 API 없이 패턴 매칭과 키워드 기반으로 동작합니다.
"""
import re
import uuid
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from loguru import logger


class RuleBasedEntityExtractor:
    """규칙 기반 보험 엔티티 추출기"""

    # 엔티티 타입 정의
    ENTITY_TYPES = {
        "coverage_item": "보장항목",
        "benefit_amount": "보험금액",
        "payment_condition": "지급조건",
        "exclusion": "면책사항",
        "deductible": "자기부담금",
        "rider": "특약",
        "eligibility": "가입조건",
        "article": "약관조항",
        "term": "보험용어",
        "period": "기간"
    }

    def __init__(self):
        """추출 패턴 초기화"""
        # 보장항목 패턴
        self.coverage_patterns = [
            r"([가-힣]{2,10})\s*보장",
            r"([가-힣]{2,10})\s*담보",
            r"([가-힣]{2,10})\s*급부",
            r"([가-힣]{2,10})\s*보험금",
            r"(암|질병|상해|사망|후유장해|입원|수술|통원)\s*[보담급]",
        ]

        # 보험금액 패턴
        self.benefit_patterns = [
            r"([\d,]+원|[\d,]+만원|[\d,]+억원)",
            r"보험금\s*([\d,]+원)",
            r"급부금\s*([\d,]+원)",
            r"([\d,]+)%\s*지급",
        ]

        # 지급조건 패턴
        self.payment_condition_patterns = [
            r"(진단\s*확정\s*시|사망\s*시|발생\s*시)\s*지급",
            r"([가-힣\s]+)\s*경우\s*지급",
            r"지급사유\s*:\s*([^\.]+)",
            r"다음\s*각\s*호의\s*([^\.]+)\s*지급",
        ]

        # 면책사항 패턴
        self.exclusion_patterns = [
            r"보장하지\s*[않아아니]",
            r"면책\s*기간",
            r"지급\s*[불부]\s*가",
            r"제외\s*[됩되]",
            r"([가-힣\s]+)\s*경우에는\s*[보지않]",
            r"다음\s*각\s*호의\s*경우\s*[보지않]",
        ]

        # 자기부담금 패턴
        self.deductible_patterns = [
            r"자기부담금\s*([\d,]+원)",
            r"본인부담금\s*([\d,]+원)",
            r"공제금액\s*([\d,]+원)",
            r"([\d,]+원)\s*공제",
        ]

        # 특약 패턴
        self.rider_patterns = [
            r"([가-힣]{2,15})\s*특약",
            r"특약\s*:\s*([가-힣]{2,15})",
        ]

        # 가입조건 패턴
        self.eligibility_patterns = [
            r"가입\s*연령\s*:\s*([^\.]+)",
            r"(만\s*[\d]+세\s*~\s*만\s*[\d]+세)",
            r"가입\s*조건\s*:\s*([^\.]+)",
            r"피보험자\s*자격\s*:\s*([^\.]+)",
        ]

        # 약관조항 패턴
        self.article_patterns = [
            r"제\s*([\d]+)\s*조",
            r"제\s*([\d]+)\s*항",
            r"제\s*([\d]+)\s*호",
            r"조항\s*([\d]+)",
        ]

        # 보험용어 패턴
        self.term_patterns = [
            r"(피보험자|보험수익자|보험계약자|보험료|보험기간)",
            r"(보험가입금액|책임준비금|해약환급금)",
            r"(진단확정|후유장해|상해|질병|암)",
        ]

        # 기간 패턴
        self.period_patterns = [
            r"([\d]+일|[\d]+개월|[\d]+년)",
            r"보험기간\s*:\s*([^\.]+)",
            r"납입기간\s*:\s*([^\.]+)",
            r"면책기간\s*:\s*([^\.]+)",
        ]

    def extract_entities(self, text: str, document_id: int, insurer: str, product_type: str) -> List[Dict]:
        """
        텍스트에서 모든 엔티티 추출

        Args:
            text: 추출할 텍스트
            document_id: 문서 ID
            insurer: 보험사
            product_type: 상품 타입

        Returns:
            추출된 엔티티 리스트
        """
        entities = []

        # 각 타입별 추출
        entities.extend(self._extract_by_pattern("coverage_item", self.coverage_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("benefit_amount", self.benefit_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("payment_condition", self.payment_condition_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("exclusion", self.exclusion_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("deductible", self.deductible_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("rider", self.rider_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("eligibility", self.eligibility_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("article", self.article_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("term", self.term_patterns, text, document_id, insurer, product_type))
        entities.extend(self._extract_by_pattern("period", self.period_patterns, text, document_id, insurer, product_type))

        logger.info(f"📊 Extracted {len(entities)} entities from document {document_id}")
        return entities

    def _extract_by_pattern(
        self,
        entity_type: str,
        patterns: List[str],
        text: str,
        document_id: int,
        insurer: str,
        product_type: str
    ) -> List[Dict]:
        """
        패턴으로 엔티티 추출

        Args:
            entity_type: 엔티티 타입
            patterns: 정규표현식 패턴 리스트
            text: 추출할 텍스트
            document_id: 문서 ID
            insurer: 보험사
            product_type: 상품 타입

        Returns:
            추출된 엔티티 리스트
        """
        entities = []
        seen_labels = set()  # 중복 방지

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 매칭된 그룹 추출
                label = match.group(1) if match.groups() else match.group(0)
                label = label.strip()

                # 너무 짧거나 긴 라벨 제외
                if len(label) < 2 or len(label) > 50:
                    continue

                # 중복 제외
                if label in seen_labels:
                    continue
                seen_labels.add(label)

                # 컨텍스트 추출 (매칭된 위치 앞뒤 50자)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                # 설명 생성 (컨텍스트에서 첫 문장 추출)
                description = self._extract_first_sentence(context)

                entity = {
                    "entity_id": str(uuid.uuid4()),
                    "label": label,
                    "type": entity_type,
                    "description": description,
                    "source_text": context[:200],  # 최대 200자
                    "document_id": document_id,
                    "insurer": insurer,
                    "product_type": product_type,
                    "created_at": datetime.utcnow()
                }
                entities.append(entity)

        return entities

    def _extract_first_sentence(self, text: str) -> str:
        """
        텍스트에서 첫 번째 문장 추출

        Args:
            text: 입력 텍스트

        Returns:
            첫 번째 문장 (최대 100자)
        """
        # 마침표, 느낌표, 물음표로 문장 분리
        sentences = re.split(r'[\.!?]\s+', text)
        if sentences:
            return sentences[0][:100]
        return text[:100]

    def extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """
        엔티티 간 관계 추출

        Args:
            entities: 추출된 엔티티 리스트
            text: 원본 텍스트

        Returns:
            관계 리스트
        """
        relationships = []

        # 엔티티를 타입별로 그룹화
        entities_by_type = {}
        for entity in entities:
            entity_type = entity["type"]
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # 규칙 기반 관계 생성
        # 1. 보장항목 -> 보험금액
        if "coverage_item" in entities_by_type and "benefit_amount" in entities_by_type:
            for coverage in entities_by_type["coverage_item"]:
                for amount in entities_by_type["benefit_amount"]:
                    # 텍스트 내 거리가 가까운 경우 관계 생성
                    if self._is_close_in_text(coverage["source_text"], amount["source_text"], text, max_distance=100):
                        relationships.append({
                            "source_entity_id": coverage["entity_id"],
                            "target_entity_id": amount["entity_id"],
                            "type": "has_amount",
                            "description": f"{coverage['label']}의 보험금액은 {amount['label']}입니다",
                            "created_at": datetime.utcnow()
                        })

        # 2. 보장항목 -> 지급조건
        if "coverage_item" in entities_by_type and "payment_condition" in entities_by_type:
            for coverage in entities_by_type["coverage_item"]:
                for condition in entities_by_type["payment_condition"]:
                    if self._is_close_in_text(coverage["source_text"], condition["source_text"], text, max_distance=150):
                        relationships.append({
                            "source_entity_id": coverage["entity_id"],
                            "target_entity_id": condition["entity_id"],
                            "type": "requires",
                            "description": f"{coverage['label']} 지급 조건: {condition['label']}",
                            "created_at": datetime.utcnow()
                        })

        # 3. 보장항목 -> 면책사항
        if "coverage_item" in entities_by_type and "exclusion" in entities_by_type:
            for coverage in entities_by_type["coverage_item"]:
                for exclusion in entities_by_type["exclusion"]:
                    if self._is_close_in_text(coverage["source_text"], exclusion["source_text"], text, max_distance=150):
                        relationships.append({
                            "source_entity_id": coverage["entity_id"],
                            "target_entity_id": exclusion["entity_id"],
                            "type": "excludes",
                            "description": f"{coverage['label']} 면책사항: {exclusion['label']}",
                            "created_at": datetime.utcnow()
                        })

        # 4. 특약 -> 보장항목
        if "rider" in entities_by_type and "coverage_item" in entities_by_type:
            for rider in entities_by_type["rider"]:
                for coverage in entities_by_type["coverage_item"]:
                    if self._is_close_in_text(rider["source_text"], coverage["source_text"], text, max_distance=200):
                        relationships.append({
                            "source_entity_id": rider["entity_id"],
                            "target_entity_id": coverage["entity_id"],
                            "type": "provides",
                            "description": f"{rider['label']}은 {coverage['label']}을 제공합니다",
                            "created_at": datetime.utcnow()
                        })

        # 5. 약관조항 -> 보험용어
        if "article" in entities_by_type and "term" in entities_by_type:
            for article in entities_by_type["article"]:
                for term in entities_by_type["term"]:
                    if self._is_close_in_text(article["source_text"], term["source_text"], text, max_distance=100):
                        relationships.append({
                            "source_entity_id": article["entity_id"],
                            "target_entity_id": term["entity_id"],
                            "type": "defines",
                            "description": f"{article['label']}에서 {term['label']}을 정의합니다",
                            "created_at": datetime.utcnow()
                        })

        logger.info(f"🔗 Extracted {len(relationships)} relationships")
        return relationships

    def _is_close_in_text(self, text1: str, text2: str, full_text: str, max_distance: int = 100) -> bool:
        """
        두 텍스트가 원본에서 가까운지 확인

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            full_text: 전체 텍스트
            max_distance: 최대 거리 (문자 수)

        Returns:
            가까우면 True
        """
        try:
            pos1 = full_text.find(text1[:20])  # 첫 20자로 검색
            pos2 = full_text.find(text2[:20])

            if pos1 == -1 or pos2 == -1:
                return False

            return abs(pos1 - pos2) <= max_distance
        except:
            return False


# 전역 인스턴스
rule_extractor = RuleBasedEntityExtractor()
