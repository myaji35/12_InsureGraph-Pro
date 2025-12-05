"""
LLM-based Entity and Relationship Extractor using Gemini API

Gemini API를 사용하여 보험 문서에서 엔티티와 관계를 추출합니다.
규칙 기반 추출기보다 훨씬 더 많은 관계를 찾아낼 수 있습니다.

Gemini 1.5 Flash 사용:
- 비용: $0.66/문서 (Claude Opus $4.95 대비 87% 절감)
- 속도: ~10분/문서 (Claude Opus 66분 대비 6배 빠름)
- JSON 안정성: 구조화된 출력 모드 지원
"""
import json
import uuid
from typing import List, Dict, Tuple
from datetime import datetime
from loguru import logger
import google.generativeai as genai

from app.core.config import settings


class LLMEntityExtractor:
    """LLM 기반 보험 엔티티 및 관계 추출기"""

    # 엔티티 타입 정의 (rule-based와 동일하게 유지)
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
        "period": "기간",
        "insurer": "보험사",
        "product": "보험상품"
    }

    # 관계 타입 정의
    RELATIONSHIP_TYPES = {
        "INCLUDES": "포함한다",
        "REQUIRES": "필요로한다",
        "EXCLUDES": "제외한다",
        "APPLIES_TO": "적용된다",
        "RELATED_TO": "관련있다",
        "PART_OF": "부분이다",
        "HAS_CONDITION": "조건이있다",
        "HAS_AMOUNT": "금액이있다",
        "HAS_PERIOD": "기간이있다",
        "COVERS": "보장한다",
        "PAYS_FOR": "지급한다"
    }

    def __init__(self):
        """Gemini API 클라이언트 초기화"""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',  # Gemini 2.5 Flash 사용
            generation_config=genai.GenerationConfig(
                temperature=0,
                response_mime_type="application/json"  # JSON 출력 강제
            )
        )

    def extract_entities_and_relationships(
        self,
        text: str,
        insurer: str = "",
        product_type: str = "",
        document_id: str = ""
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        텍스트에서 엔티티와 관계를 추출합니다.

        Args:
            text: 추출할 텍스트
            insurer: 보험사 이름
            product_type: 보험 상품 타입
            document_id: 문서 ID

        Returns:
            (entities, relationships) 튜플
        """
        try:
            # Gemini API를 사용하여 엔티티와 관계 추출
            # 시스템 프롬프트와 사용자 프롬프트를 결합
            full_prompt = f"""{self._get_system_prompt()}

{self._get_user_prompt(text, insurer, product_type)}"""

            response = self.model.generate_content(full_prompt)

            # 응답 파싱
            content = response.text
            result = self._parse_llm_response(content, document_id, insurer, product_type)

            logger.info(
                f"Extracted {len(result['entities'])} entities and "
                f"{len(result['relationships'])} relationships from text (length: {len(text)})"
            )

            return result['entities'], result['relationships']

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return [], []

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 보험 문서를 분석하여 엔티티(entity)와 관계(relationship)를 추출하는 전문가입니다.

**목표**: 주어진 텍스트에서 최대한 많은 엔티티와 그들 사이의 관계를 찾아내어 풍부한 지식 그래프를 구축합니다.

**엔티티 타입**:
- coverage_item: 보장항목 (예: "암진단보험금", "수술급여금")
- benefit_amount: 보험금액 (예: "1억원", "500만원")
- payment_condition: 지급조건 (예: "진단확정시", "입원 3일 이상")
- exclusion: 면책사항 (예: "고의적 사고", "음주운전")
- deductible: 자기부담금 (예: "20만원 공제", "본인부담금 10%")
- rider: 특약 (예: "암진단특약", "수술특약")
- eligibility: 가입조건 (예: "만 15세~60세", "건강한 자")
- article: 약관조항 (예: "제10조", "제3항")
- term: 보험용어 (예: "피보험자", "보험수익자")
- period: 기간 (예: "90일", "5년", "면책기간")
- insurer: 보험사 (예: "삼성화재", "KB손해보험")
- product: 보험상품 (예: "자동차보험", "실손의료보험")

**관계 타입**:
- INCLUDES: A가 B를 포함한다
- REQUIRES: A가 B를 필요로 한다
- EXCLUDES: A가 B를 제외한다
- APPLIES_TO: A가 B에 적용된다
- RELATED_TO: A와 B가 관련있다
- PART_OF: A가 B의 부분이다
- HAS_CONDITION: A가 B라는 조건을 갖는다
- HAS_AMOUNT: A가 B라는 금액을 갖는다
- HAS_PERIOD: A가 B라는 기간을 갖는다
- COVERS: A가 B를 보장한다
- PAYS_FOR: A가 B에 대해 지급한다

**중요**:
1. 명시적인 관계뿐만 아니라 **문맥상 암묵적으로 드러나는 관계**도 모두 추출하세요.
2. 엔티티 간의 모든 가능한 연결을 찾아내어 **풍부하게 연결된 그래프**를 만드세요.
3. 한 문장에서 여러 관계를 추출할 수 있습니다.

**출력 형식**: JSON only (no markdown, no explanations)
{
  "entities": [
    {
      "label": "엔티티 이름",
      "type": "엔티티_타입",
      "description": "엔티티 설명",
      "source_text": "원문 텍스트 일부"
    }
  ],
  "relationships": [
    {
      "source_label": "출발 엔티티 이름",
      "target_label": "도착 엔티티 이름",
      "type": "관계_타입",
      "description": "관계 설명"
    }
  ]
}"""

    def _get_user_prompt(self, text: str, insurer: str, product_type: str) -> str:
        """사용자 프롬프트 생성"""
        context = []
        if insurer:
            context.append(f"보험사: {insurer}")
        if product_type:
            context.append(f"상품 타입: {product_type}")

        context_str = "\n".join(context) if context else "컨텍스트 정보 없음"

        # Gemini는 더 긴 컨텍스트를 처리할 수 있으므로 4000자로 확장
        return f"""다음 보험 문서 텍스트에서 엔티티와 관계를 추출해주세요.

**컨텍스트**:
{context_str}

**텍스트**:
{text[:4000]}

가능한 많은 관계를 찾아내어 풍부한 지식 그래프를 만들어주세요."""

    def _parse_llm_response(
        self,
        response_text: str,
        document_id: str,
        insurer: str,
        product_type: str
    ) -> Dict:
        """LLM 응답을 파싱하여 엔티티와 관계로 변환"""
        try:
            # Markdown 코드 블록 제거
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            # JSON 파싱
            data = json.loads(response_text.strip())

            entities = []
            relationships = []
            entity_label_to_id = {}  # 라벨 -> entity_id 매핑

            # 엔티티 처리
            for entity in data.get("entities", []):
                entity_id = f"entity_{uuid.uuid4().hex[:12]}"
                entity_label_to_id[entity["label"]] = entity_id

                entities.append({
                    "entity_id": entity_id,
                    "label": entity["label"],
                    "type": entity["type"],
                    "description": entity.get("description", ""),
                    "source_text": entity.get("source_text", ""),
                    "document_id": document_id,
                    "insurer": insurer,
                    "product_type": product_type,
                    "created_at": datetime.now().isoformat()
                })

            # 관계 처리
            for rel in data.get("relationships", []):
                source_label = rel["source_label"]
                target_label = rel["target_label"]

                # 엔티티 ID 찾기
                source_id = entity_label_to_id.get(source_label)
                target_id = entity_label_to_id.get(target_label)

                if source_id and target_id:
                    relationships.append({
                        "source_entity_id": source_id,
                        "target_entity_id": target_id,
                        "relationship_type": rel["type"],
                        "description": rel.get("description", ""),
                        "document_id": document_id,
                        "created_at": datetime.now().isoformat()
                    })

            return {
                "entities": entities,
                "relationships": relationships
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nResponse: {response_text[:500]}")
            return {"entities": [], "relationships": []}
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            return {"entities": [], "relationships": []}

    def extract_from_chunks(
        self,
        chunks: List[str],
        insurer: str = "",
        product_type: str = "",
        document_id: str = ""
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        여러 청크에서 엔티티와 관계를 추출하고 병합합니다.

        Args:
            chunks: 텍스트 청크 리스트
            insurer: 보험사 이름
            product_type: 보험 상품 타입
            document_id: 문서 ID

        Returns:
            (all_entities, all_relationships) 튜플
        """
        all_entities = []
        all_relationships = []
        entity_label_map = {}  # 라벨 -> 최종 entity_id 매핑

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")

            entities, relationships = self.extract_entities_and_relationships(
                chunk, insurer, product_type, document_id
            )

            # 엔티티 중복 제거 및 병합
            for entity in entities:
                label = entity["label"]
                if label in entity_label_map:
                    # 이미 존재하는 엔티티 - ID 재사용
                    entity["entity_id"] = entity_label_map[label]
                else:
                    # 새로운 엔티티
                    entity_label_map[label] = entity["entity_id"]
                    all_entities.append(entity)

            # 관계 추가
            all_relationships.extend(relationships)

        # 관계 중복 제거
        unique_relationships = []
        seen_relationships = set()

        for rel in all_relationships:
            key = (rel["source_entity_id"], rel["target_entity_id"], rel["relationship_type"])
            if key not in seen_relationships:
                seen_relationships.add(key)
                unique_relationships.append(rel)

        logger.info(
            f"Total extracted: {len(all_entities)} unique entities, "
            f"{len(unique_relationships)} unique relationships"
        )

        return all_entities, unique_relationships
