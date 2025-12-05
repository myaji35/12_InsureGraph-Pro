"""
GraphRAG 스타일 엔티티 추출기

보험 문서에서 깊이 있는 엔티티와 관계를 추출합니다.
"""
from typing import List, Dict, Optional
import anthropic
from loguru import logger
import json
import os


class GraphRAGEntityExtractor:
    """
    GraphRAG 스타일 엔티티 추출기

    보험 문서에서 다음 엔티티들을 추출:
    - 보장항목 (coverage_item)
    - 보험금 (benefit_amount)
    - 지급조건 (payment_condition)
    - 면책사항 (exclusion)
    - 자기부담금 (deductible)
    - 특약 (rider)
    - 가입조건 (eligibility)
    - 약관조항 (article)
    """

    # 보험 도메인 엔티티 타입 정의
    ENTITY_TYPES = {
        "coverage_item": "보장항목 (예: 사망보험금, 상해후유장해, 입원일당)",
        "benefit_amount": "보험금액 (예: 1억원, 5,000만원)",
        "payment_condition": "지급조건 (예: 교통사고로 인한 사망, 암진단 시)",
        "exclusion": "면책사항 (예: 고의적 사고, 전쟁, 폭동)",
        "deductible": "자기부담금 (예: 20%, 10만원)",
        "rider": "특약 (예: 암진단특약, 3대질병특약)",
        "eligibility": "가입조건 (예: 만 15세~65세, 건강체)",
        "article": "약관조항 (예: 제1관 제3조)",
        "term": "보험용어 (예: 피보험자, 보험계약자, 보험수익자)",
        "period": "기간 (예: 보험기간 10년, 납입기간 20년)"
    }

    RELATIONSHIP_TYPES = {
        "provides": "보장항목 제공 (보험상품 -> 보장항목)",
        "has_amount": "보험금액 설정 (보장항목 -> 보험금액)",
        "requires": "조건 요구 (보장항목 -> 지급조건)",
        "excludes": "면책 (보장항목 -> 면책사항)",
        "has_deductible": "자기부담금 설정 (보장항목 -> 자기부담금)",
        "includes_rider": "특약 포함 (보험상품 -> 특약)",
        "defines": "정의 (약관조항 -> 보험용어)",
        "specified_in": "명시 (엔티티 -> 약관조항)",
        "has_eligibility": "가입조건 (보험상품 -> 가입조건)",
        "applies_to": "적용 대상 (조건 -> 보장항목)"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Anthropic API key (기본값: 환경변수에서 읽음)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _create_extraction_prompt(self, text: str, document_info: Dict) -> str:
        """엔티티 추출 프롬프트 생성"""
        entity_types_desc = "\n".join([
            f"- {etype}: {desc}"
            for etype, desc in self.ENTITY_TYPES.items()
        ])

        relationship_types_desc = "\n".join([
            f"- {rtype}: {desc}"
            for rtype, desc in self.RELATIONSHIP_TYPES.items()
        ])

        return f"""당신은 보험 전문가입니다. 다음 보험 약관 텍스트에서 엔티티와 관계를 추출하세요.

**문서 정보:**
- 보험사: {document_info.get('insurer', 'Unknown')}
- 상품타입: {document_info.get('product_type', 'Unknown')}
- 제목: {document_info.get('title', 'Unknown')}

**추출할 엔티티 타입:**
{entity_types_desc}

**추출할 관계 타입:**
{relationship_types_desc}

**텍스트:**
{text[:4000]}

**출력 형식 (JSON):**
{{
  "entities": [
    {{
      "id": "unique_id",
      "label": "엔티티 이름",
      "type": "entity_type",
      "description": "엔티티 설명 (선택)",
      "source_text": "원본 텍스트 발췌"
    }}
  ],
  "relationships": [
    {{
      "source_id": "entity1_id",
      "target_id": "entity2_id",
      "type": "relationship_type",
      "description": "관계 설명 (선택)"
    }}
  ]
}}

**중요:**
1. 보험 전문 용어를 정확히 추출하세요
2. 보험금액, 지급조건, 면책사항은 가능한 모두 추출하세요
3. 약관 조항 번호(제X관 제X조)도 엔티티로 추출하세요
4. 엔티티 간 의미있는 관계를 최대한 많이 추출하세요
5. 반드시 유효한 JSON 형식으로 응답하세요"""

    async def extract_entities_and_relationships(
        self,
        text: str,
        document_info: Dict,
        chunk_id: Optional[str] = None
    ) -> Dict:
        """
        텍스트에서 엔티티와 관계 추출

        Args:
            text: 추출할 텍스트
            document_info: 문서 메타데이터 (insurer, product_type, title)
            chunk_id: 청크 ID (선택)

        Returns:
            {
                "entities": [...],
                "relationships": [...],
                "chunk_id": "...",
                "entity_count": N,
                "relationship_count": M
            }
        """
        if not text or len(text.strip()) < 50:
            logger.warning("텍스트가 너무 짧아서 엔티티 추출을 건너뜁니다")
            return {
                "entities": [],
                "relationships": [],
                "chunk_id": chunk_id,
                "entity_count": 0,
                "relationship_count": 0
            }

        try:
            prompt = self._create_extraction_prompt(text, document_info)

            logger.info(f"Extracting entities from text (length: {len(text)})")

            # Claude API 호출
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # 응답 파싱
            response_text = message.content[0].text.strip()

            # JSON 추출 (마크다운 코드블록 제거)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # 결과 검증
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])

            # 엔티티 ID 검증 및 생성
            entity_ids = set()
            for i, entity in enumerate(entities):
                if "id" not in entity:
                    entity["id"] = f"entity_{chunk_id}_{i}"
                entity_ids.add(entity["id"])

                # chunk_id 추가
                if chunk_id:
                    entity["chunk_id"] = chunk_id

                # 문서 정보 추가
                entity["document_info"] = document_info

            # 관계 검증 (존재하지 않는 엔티티 참조 제거)
            valid_relationships = []
            for rel in relationships:
                if rel.get("source_id") in entity_ids and rel.get("target_id") in entity_ids:
                    if chunk_id:
                        rel["chunk_id"] = chunk_id
                    valid_relationships.append(rel)
                else:
                    logger.warning(f"Invalid relationship: {rel}")

            logger.info(f"✅ Extracted {len(entities)} entities and {len(valid_relationships)} relationships")

            return {
                "entities": entities,
                "relationships": valid_relationships,
                "chunk_id": chunk_id,
                "entity_count": len(entities),
                "relationship_count": len(valid_relationships),
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {response_text[:500]}")
            return {
                "entities": [],
                "relationships": [],
                "chunk_id": chunk_id,
                "entity_count": 0,
                "relationship_count": 0,
                "error": f"JSON parse error: {str(e)}"
            }

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}", exc_info=True)
            return {
                "entities": [],
                "relationships": [],
                "chunk_id": chunk_id,
                "entity_count": 0,
                "relationship_count": 0,
                "error": str(e)
            }

    async def extract_from_chunks(
        self,
        chunks: List[Dict],
        document_info: Dict
    ) -> Dict:
        """
        여러 청크에서 엔티티 추출

        Args:
            chunks: 청크 리스트 [{"text": "...", "id": "..."}, ...]
            document_info: 문서 메타데이터

        Returns:
            전체 엔티티 및 관계 집계 결과
        """
        all_entities = []
        all_relationships = []
        total_tokens = 0

        for chunk in chunks:
            result = await self.extract_entities_and_relationships(
                text=chunk.get("text", ""),
                document_info=document_info,
                chunk_id=chunk.get("id")
            )

            all_entities.extend(result["entities"])
            all_relationships.extend(result["relationships"])
            total_tokens += result.get("tokens_used", 0)

        # 엔티티 타입별 집계
        entity_type_counts = {}
        for entity in all_entities:
            etype = entity.get("type", "unknown")
            entity_type_counts[etype] = entity_type_counts.get(etype, 0) + 1

        # 관계 타입별 집계
        relationship_type_counts = {}
        for rel in all_relationships:
            rtype = rel.get("type", "unknown")
            relationship_type_counts[rtype] = relationship_type_counts.get(rtype, 0) + 1

        return {
            "entities": all_entities,
            "relationships": all_relationships,
            "total_entity_count": len(all_entities),
            "total_relationship_count": len(all_relationships),
            "entity_type_counts": entity_type_counts,
            "relationship_type_counts": relationship_type_counts,
            "total_tokens_used": total_tokens,
            "chunks_processed": len(chunks)
        }
