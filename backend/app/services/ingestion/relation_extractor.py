"""
Relation Extraction Agent

Extracts relationships (COVERS, EXCLUDES, REQUIRES, etc.) from insurance clauses
using LLM with validation against critical data.

Uses cascade strategy:
1. Try Upstage Solar Pro first (cost-effective)
2. If confidence < 0.7, retry with GPT-4o (more accurate)
3. Validate all extractions against rule-based critical data
"""
import json
import re
from typing import Dict, Any, List, Optional
from app.models.relation import (
    ExtractedRelation,
    RelationExtractionResult,
    RelationCondition,
    RelationAction,
)
from app.models.critical_data import CriticalData
from app.services.ingestion.llm_client import LLMClientFactory


# Prompt template for relation extraction
RELATION_EXTRACTION_PROMPT = """당신은 보험 약관 전문가입니다. 다음 약관 조항에서 관계를 추출하세요.

[약관 조항]
{clause_text}

[추출된 Critical Data]
금액: {amounts}
기간: {periods}
질병코드: {kcd_codes}

[지침]
1. 주체(Subject): 어떤 담보/상품?
2. 행위(Action): COVERS, EXCLUDES, REQUIRES, REDUCES, LIMITS, REFERENCES 중 선택
3. 객체(Object): 어떤 질병/상황?
4. 조건(Conditions): 면책기간, 감액비율 등

**중요**: Critical Data가 제공되었다면 반드시 그 값을 사용하세요. 새로운 숫자를 생성하지 마세요.

[출력 형식 - JSON]
{{
  "relations": [
    {{
      "subject": "암진단특약",
      "action": "COVERS",
      "object": "일반암",
      "conditions": [
        {{"type": "waiting_period", "value": 90, "description": "계약일로부터 90일"}},
        {{"type": "payment_amount", "value": 100000000, "description": "1억원"}}
      ],
      "confidence": 0.95,
      "reasoning": "제10조 ①항에서 명시",
      "source_clause_text": "{clause_text}"
    }}
  ]
}}

답변 (JSON만):"""


class RelationExtractor:
    """Extracts relations from clauses using LLM"""

    def __init__(self):
        self.upstage_client = LLMClientFactory.create_client("upstage")
        self.openai_client = LLMClientFactory.create_client("openai")

        # Confidence thresholds
        self.HIGH_CONFIDENCE = 0.85
        self.RETRY_THRESHOLD = 0.70
        self.REJECT_THRESHOLD = 0.60

    async def extract(
        self,
        clause_text: str,
        critical_data: CriticalData,
        use_cascade: bool = True,
    ) -> RelationExtractionResult:
        """
        Extract relations from clause with validation

        Args:
            clause_text: Text of the clause to extract from
            critical_data: Rule-based critical data for validation
            use_cascade: Whether to use cascade strategy (Solar Pro -> GPT-4o)

        Returns:
            RelationExtractionResult with extracted relations and validation status
        """
        # Step 1: Try Solar Pro first
        llm_response = await self._call_llm(
            self.upstage_client,
            clause_text,
            critical_data,
        )

        # Step 2: Cascade to GPT-4o if confidence is low
        if use_cascade and llm_response["confidence"] < self.RETRY_THRESHOLD:
            llm_response = await self._call_llm(
                self.openai_client,
                clause_text,
                critical_data,
            )

        # Step 3: Parse LLM response
        try:
            relations = self._parse_llm_response(llm_response["text"], clause_text)
        except Exception as e:
            return RelationExtractionResult(
                relations=[],
                llm_model=llm_response["model"],
                extraction_confidence=0.0,
                validation_passed=False,
                validation_errors=[f"Failed to parse LLM response: {str(e)}"],
            )

        # Step 4: Validate against critical data
        validated_relations, validation_errors, validation_warnings = self._validate_relations(
            relations,
            critical_data,
        )

        # Step 5: Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            validated_relations,
            llm_response["confidence"],
            len(validation_errors),
        )

        return RelationExtractionResult(
            relations=validated_relations,
            llm_model=llm_response["model"],
            extraction_confidence=overall_confidence,
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
        )

    async def _call_llm(
        self,
        client,
        clause_text: str,
        critical_data: CriticalData,
    ) -> Dict[str, Any]:
        """Call LLM with prompt"""
        # Format critical data for prompt
        amounts_str = ", ".join([f"{a.original_text} ({a.value:,}원)" for a in critical_data.amounts])
        periods_str = ", ".join([f"{p.original_text} ({p.days}일)" for p in critical_data.periods])
        kcd_codes_str = ", ".join([k.code for k in critical_data.kcd_codes])

        prompt = RELATION_EXTRACTION_PROMPT.format(
            clause_text=clause_text,
            amounts=amounts_str or "없음",
            periods=periods_str or "없음",
            kcd_codes=kcd_codes_str or "없음",
        )

        response = await client.generate(prompt, temperature=0.3, max_tokens=2000)
        return response

    def _parse_llm_response(self, llm_text: str, clause_text: str) -> List[ExtractedRelation]:
        """Parse LLM JSON response into ExtractedRelation objects"""
        # Extract JSON from response (may be wrapped in markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r'\{.*\}', llm_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in LLM response")

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LLM response: {str(e)}")

        # Validate structure
        if "relations" not in data:
            raise ValueError("Missing 'relations' key in LLM response")

        # Convert to ExtractedRelation objects
        relations = []
        for rel_data in data["relations"]:
            # Convert conditions
            conditions = []
            for cond_data in rel_data.get("conditions", []):
                conditions.append(RelationCondition(**cond_data))

            # Ensure source_clause_text is set
            if "source_clause_text" not in rel_data:
                rel_data["source_clause_text"] = clause_text

            relation = ExtractedRelation(
                subject=rel_data["subject"],
                action=rel_data["action"],
                object=rel_data["object"],
                conditions=conditions,
                confidence=rel_data.get("confidence", 0.85),
                reasoning=rel_data.get("reasoning", ""),
                source_clause_text=rel_data["source_clause_text"],
            )
            relations.append(relation)

        return relations

    def _validate_relations(
        self,
        relations: List[ExtractedRelation],
        critical_data: CriticalData,
    ) -> tuple[List[ExtractedRelation], List[str], List[str]]:
        """
        Validate LLM-extracted relations against rule-based critical data

        Returns:
            (validated_relations, errors, warnings)
        """
        errors = []
        warnings = []
        validated_relations = []

        for relation in relations:
            # Validate each condition
            for condition in relation.conditions:
                if condition.type == "waiting_period" and condition.value:
                    # Check against extracted periods
                    extracted_days = [p.days for p in critical_data.periods]
                    if extracted_days and condition.value not in extracted_days:
                        # Override with rule-based value
                        original_value = condition.value
                        condition.value = extracted_days[0]
                        warnings.append(
                            f"Override LLM period {original_value} -> {condition.value} "
                            f"(from rule-based extraction)"
                        )

                elif condition.type == "payment_amount" and condition.value:
                    # Check against extracted amounts
                    extracted_amounts = [a.value for a in critical_data.amounts]
                    if extracted_amounts and condition.value not in extracted_amounts:
                        # Find closest match
                        closest = min(extracted_amounts, key=lambda x: abs(x - condition.value))
                        if abs(closest - condition.value) / closest < 0.1:  # Within 10%
                            original_value = condition.value
                            condition.value = closest
                            warnings.append(
                                f"Override LLM amount {original_value:,} -> {condition.value:,} "
                                f"(from rule-based extraction)"
                            )
                        else:
                            errors.append(
                                f"LLM amount {condition.value:,} does not match any extracted amount"
                            )

            validated_relations.append(relation)

        return validated_relations, errors, warnings

    def _calculate_overall_confidence(
        self,
        relations: List[ExtractedRelation],
        llm_confidence: float,
        num_errors: int,
    ) -> float:
        """Calculate overall extraction confidence"""
        if not relations:
            return 0.0

        # Start with LLM confidence
        confidence = llm_confidence

        # Average relation confidence
        avg_relation_confidence = sum(r.confidence for r in relations) / len(relations)
        confidence = (confidence + avg_relation_confidence) / 2

        # Penalize for validation errors
        if num_errors > 0:
            confidence -= min(0.3, num_errors * 0.1)

        return max(0.0, min(1.0, confidence))
