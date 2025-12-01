"""
LLM Reasoning Service

그래프 탐색 결과를 바탕으로 LLM을 사용하여 자연어 답변을 생성합니다.

Features:
1. Context Assembly - 그래프 경로를 컨텍스트로 조립
2. LLM Integration - OpenAI/Anthropic API 통합
3. Prompt Engineering - 보험 약관 전문 프롬프트
4. Answer Generation - 구조화된 답변 생성
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from app.services.query_parser import ParsedQuery, QueryIntent
from app.services.local_search import SearchResult
from app.services.graph_traversal import GraphPath, TraversalResult
from app.core.config import settings
from loguru import logger

# Optional LLM imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - will use mock responses")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available - will use mock responses")


class LLMProvider(str, Enum):
    """LLM provider options"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class ReasoningContext:
    """Context assembled for LLM reasoning"""
    query: str
    intent: QueryIntent
    search_results: List[SearchResult]
    graph_paths: List[GraphPath]
    total_sources: int

    def to_text(self) -> str:
        """Convert context to text format for LLM"""
        lines = [
            f"# 사용자 질문: {self.query}",
            f"# 질문 유형: {self.intent.value}",
            f"# 참조 문서 수: {self.total_sources}",
            "",
            "## 관련 조문:",
        ]

        # Add search results
        for i, result in enumerate(self.search_results[:10], 1):
            lines.append(f"\n### {i}. {result.node_type} ({result.node_id})")
            lines.append(f"텍스트: {result.text[:500]}...")
            if result.metadata:
                lines.append(f"메타데이터: {result.metadata}")

        # Add graph paths
        if self.graph_paths:
            lines.append("\n## 그래프 경로:")
            for i, path in enumerate(self.graph_paths[:5], 1):
                lines.append(f"\n### 경로 {i}: {path}")
                for node in path.nodes:
                    lines.append(f"  - {node.node_type}: {node.text[:200]}...")

        return "\n".join(lines)


@dataclass
class ReasoningResult:
    """Result of LLM reasoning"""
    query: str
    answer: str
    confidence: float  # 0.0 - 1.0
    sources: List[Dict[str, Any]]  # Referenced sources
    reasoning_steps: List[str]  # Chain of thought
    provider: LLMProvider

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "reasoning_steps": self.reasoning_steps,
            "provider": self.provider.value,
        }


class LLMReasoning:
    """
    LLM-based reasoning service for insurance Q&A.

    Features:
    - Multi-provider support (OpenAI, Anthropic)
    - Context assembly from graph results
    - Chain-of-thought reasoning
    - Source citation
    """

    # System prompts for different query intents
    SYSTEM_PROMPTS = {
        QueryIntent.SEARCH: """당신은 보험 약관 전문가입니다. 사용자의 질문에 대해 제공된 보험 약관 조문을 바탕으로 정확하고 이해하기 쉽게 답변해주세요.

답변 시 다음 사항을 지켜주세요:
1. 제공된 조문의 내용만을 근거로 답변하세요
2. 조문을 직접 인용할 때는 조항 번호를 명시하세요 (예: "제10조에 따르면...")
3. 전문 용어는 쉽게 풀어서 설명하세요
4. 불확실한 경우 "제공된 약관에서 명확하지 않습니다"라고 말하세요""",

        QueryIntent.COMPARISON: """당신은 보험 상품 비교 전문가입니다. 제공된 약관들을 비교하여 차이점을 명확하게 설명해주세요.

비교 시 다음 사항을 지켜주세요:
1. 보장 금액, 보장 범위, 면책 사항 등 핵심 차이점을 중심으로 설명하세요
2. 각 항목별로 비교표 형식으로 정리하세요
3. 장단점을 객관적으로 설명하세요
4. 조문 출처를 명확히 밝히세요""",

        QueryIntent.AMOUNT_FILTER: """당신은 보험금 전문가입니다. 보험금 금액과 관련된 질문에 답변해주세요.

답변 시 다음 사항을 지켜주세요:
1. 보험금 금액을 명확하게 제시하세요
2. 보험금 지급 조건을 함께 설명하세요
3. 면책 사항이나 제한 사항도 반드시 언급하세요
4. 금액이 다른 경우 (예: 질병별 차등) 구분하여 설명하세요""",

        QueryIntent.COVERAGE_CHECK: """당신은 보험 보장 분석 전문가입니다. 특정 질병이나 상황이 보장되는지 확인해주세요.

답변 시 다음 사항을 지켜주세요:
1. 보장 여부를 명확히 답변하세요 (보장함/보장안함/조건부보장)
2. 보장 조건이 있다면 상세히 설명하세요
3. 보험금 금액도 함께 안내하세요
4. 면책 사항을 반드시 확인하세요""",

        QueryIntent.EXCLUSION_CHECK: """당신은 보험 면책 사항 전문가입니다. 면책 사항을 정확하게 안내해주세요.

답변 시 다음 사항을 지켜주세요:
1. 면책 사항을 명확하게 나열하세요
2. 각 면책 사항이 적용되는 조건을 설명하세요
3. 면책 기간이 있다면 명시하세요 (예: 계약일로부터 90일)
4. 예외 사항이 있다면 함께 설명하세요""",

        QueryIntent.PERIOD_CHECK: """당신은 보험 기간 전문가입니다. 대기 기간, 보험 기간 등 기간 관련 질문에 답변해주세요.

답변 시 다음 사항을 지켜주세요:
1. 기간을 명확하게 제시하세요
2. 기간의 시작점과 종료점을 명확히 하세요
3. 기간 중 적용되는 조건을 설명하세요
4. 기간별로 보장 내용이 다르다면 구분하여 설명하세요""",
    }

    USER_PROMPT_TEMPLATE = """다음 보험 약관 정보를 바탕으로 질문에 답변해주세요.

{context}

질문: {query}

답변 형식:
1. 답변: (질문에 대한 직접적인 답변)
2. 근거: (답변의 근거가 되는 조문 인용)
3. 추가 참고사항: (알아두면 좋은 정보)
"""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ):
        """
        Initialize LLM reasoning service.

        Args:
            provider: LLM provider (openai, anthropic, mock)
            model: Model name (optional, uses defaults)
            temperature: LLM temperature (0.0-1.0)
        """
        self.provider = provider
        self.temperature = temperature

        # Set default models
        if model:
            self.model = model
        else:
            if provider == LLMProvider.OPENAI:
                self.model = "gpt-4o-mini"
            elif provider == LLMProvider.ANTHROPIC:
                self.model = "claude-3-5-sonnet-20241022"
            else:
                self.model = "mock"

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None

        if provider == LLMProvider.OPENAI and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.provider = LLMProvider.MOCK

        elif provider == LLMProvider.ANTHROPIC and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info(f"Anthropic client initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
                self.provider = LLMProvider.MOCK

        else:
            self.provider = LLMProvider.MOCK
            logger.info("Using mock LLM provider")

    def assemble_context(
        self,
        parsed_query: ParsedQuery,
        search_results: Optional[List[SearchResult]] = None,
        graph_paths: Optional[List[GraphPath]] = None,
    ) -> ReasoningContext:
        """
        Assemble context from search and graph results.

        Args:
            parsed_query: Parsed query
            search_results: Local search results
            graph_paths: Graph traversal paths

        Returns:
            ReasoningContext for LLM
        """
        search_results = search_results or []
        graph_paths = graph_paths or []

        total_sources = len(search_results) + len(graph_paths)

        return ReasoningContext(
            query=parsed_query.original_query,
            intent=parsed_query.intent,
            search_results=search_results,
            graph_paths=graph_paths,
            total_sources=total_sources,
        )

    def reason(
        self,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """
        Generate answer using LLM reasoning.

        Args:
            context: Assembled reasoning context

        Returns:
            ReasoningResult with answer
        """
        # Get system prompt for intent
        system_prompt = self.SYSTEM_PROMPTS.get(
            context.intent,
            self.SYSTEM_PROMPTS[QueryIntent.SEARCH]
        )

        # Format user prompt
        context_text = context.to_text()
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            context=context_text,
            query=context.query,
        )

        # Generate answer based on provider
        if self.provider == LLMProvider.OPENAI:
            answer, reasoning_steps = self._reason_openai(system_prompt, user_prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            answer, reasoning_steps = self._reason_anthropic(system_prompt, user_prompt)
        else:
            answer, reasoning_steps = self._reason_mock(context)

        # Extract sources
        sources = self._extract_sources(context)

        # Calculate confidence (simplified)
        confidence = self._calculate_confidence(context, answer)

        result = ReasoningResult(
            query=context.query,
            answer=answer,
            confidence=confidence,
            sources=sources,
            reasoning_steps=reasoning_steps,
            provider=self.provider,
        )

        logger.info(f"Generated answer for query: {context.query[:50]}... (confidence: {confidence:.2f})")

        return result

    def _reason_openai(self, system_prompt: str, user_prompt: str) -> tuple[str, List[str]]:
        """Generate answer using OpenAI"""
        if not self.openai_client:
            logger.warning("OpenAI client not available, using mock")
            return self._reason_mock_fallback()

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=2000,
            )

            answer = response.choices[0].message.content
            reasoning_steps = ["OpenAI reasoning completed"]

            return answer, reasoning_steps

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._reason_mock_fallback()

    def _reason_anthropic(self, system_prompt: str, user_prompt: str) -> tuple[str, List[str]]:
        """Generate answer using Anthropic"""
        if not self.anthropic_client:
            logger.warning("Anthropic client not available, using mock")
            return self._reason_mock_fallback()

        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=2000,
            )

            answer = response.content[0].text
            reasoning_steps = ["Anthropic reasoning completed"]

            return answer, reasoning_steps

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._reason_mock_fallback()

    def _reason_mock(self, context: ReasoningContext) -> tuple[str, List[str]]:
        """Generate mock answer for testing"""
        answer_parts = [
            "# 답변:",
            f"'{context.query}'에 대한 답변입니다.",
            "",
            f"검색된 {len(context.search_results)}개의 조문을 바탕으로 답변드립니다.",
        ]

        # Add sample citations
        if context.search_results:
            answer_parts.append("\n## 근거 조문:")
            for i, result in enumerate(context.search_results[:3], 1):
                answer_parts.append(f"{i}. {result.node_id}: {result.text[:100]}...")

        # Add graph info
        if context.graph_paths:
            answer_parts.append(f"\n관련 경로 {len(context.graph_paths)}개가 발견되었습니다.")

        answer_parts.append("\n## 추가 참고사항:")
        answer_parts.append("자세한 내용은 약관 전문을 참조해주세요.")

        answer = "\n".join(answer_parts)
        reasoning_steps = [
            "Query parsed",
            f"Found {len(context.search_results)} search results",
            f"Found {len(context.graph_paths)} graph paths",
            "Generated mock answer",
        ]

        return answer, reasoning_steps

    def _reason_mock_fallback(self) -> tuple[str, List[str]]:
        """Fallback mock response"""
        answer = "죄송합니다. LLM 서비스를 사용할 수 없어 답변을 생성할 수 없습니다. 관리자에게 문의해주세요."
        reasoning_steps = ["LLM unavailable", "Returned fallback response"]
        return answer, reasoning_steps

    def _extract_sources(self, context: ReasoningContext) -> List[Dict[str, Any]]:
        """Extract source references from context"""
        sources = []

        for result in context.search_results[:10]:
            sources.append({
                "node_id": result.node_id,
                "node_type": result.node_type,
                "text": result.text[:200],
                "relevance_score": result.relevance_score,
            })

        return sources

    def _calculate_confidence(self, context: ReasoningContext, answer: str) -> float:
        """
        Calculate confidence score based on context quality.

        Simplified heuristic:
        - More sources = higher confidence
        - Longer answer = higher confidence (up to a point)
        - Graph paths = higher confidence
        """
        confidence = 0.5  # Base confidence

        # Boost for number of sources
        if context.total_sources >= 5:
            confidence += 0.3
        elif context.total_sources >= 3:
            confidence += 0.2
        elif context.total_sources >= 1:
            confidence += 0.1

        # Boost for graph paths
        if context.graph_paths:
            confidence += 0.1

        # Boost for answer length (reasonable answer)
        if len(answer) > 200:
            confidence += 0.1

        return min(confidence, 1.0)


# Singleton instance
_llm_reasoning: Optional[LLMReasoning] = None


def get_llm_reasoning(
    provider: LLMProvider = LLMProvider.OPENAI,
    **kwargs
) -> LLMReasoning:
    """Get or create singleton LLM reasoning instance"""
    global _llm_reasoning
    if _llm_reasoning is None:
        _llm_reasoning = LLMReasoning(provider=provider, **kwargs)
    return _llm_reasoning


if __name__ == "__main__":
    # Test LLM reasoning
    from app.services.query_parser import get_query_parser
    from app.services.local_search import get_local_search, SearchResult

    print("=" * 70)
    print("🧪 LLM Reasoning Test")
    print("=" * 70)

    # Parse query
    print("\n📝 Parsing query...")
    parser = get_query_parser()
    query = "암보험 1억원 이상 보장 상품은?"
    parsed_query = parser.parse(query)

    print(f"  Query: {parsed_query.original_query}")
    print(f"  Intent: {parsed_query.intent.value}")
    print(f"  Entities: {len(parsed_query.entities)}")

    # Mock search results
    print("\n🔍 Creating mock search results...")
    mock_results = [
        SearchResult(
            node_type="Article",
            node_id="policy_123_article_제10조",
            text="제10조 [암보험금 지급] 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 일반암의 경우 1억원을 지급합니다.",
            relevance_score=0.95,
            metadata={"article_num": "제10조"},
            article_num="제10조",
            article_title="암보험금 지급",
        ),
        SearchResult(
            node_type="Article",
            node_id="policy_123_article_제11조",
            text="제11조 [면책사항] 계약일로부터 90일 이내 진단 확정된 암은 보험금을 지급하지 않습니다.",
            relevance_score=0.85,
            metadata={"article_num": "제11조"},
            article_num="제11조",
            article_title="면책사항",
        ),
    ]

    # Test with mock provider
    print("\n🤖 Testing with MOCK provider...")
    reasoning = get_llm_reasoning(provider=LLMProvider.MOCK)

    context = reasoning.assemble_context(
        parsed_query=parsed_query,
        search_results=mock_results,
    )

    print(f"  Context assembled: {context.total_sources} sources")

    result = reasoning.reason(context)

    print(f"\n{'='*70}")
    print(f"📊 Reasoning Result")
    print(f"{'='*70}")
    print(f"Query: {result.query}")
    print(f"Provider: {result.provider.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"\nAnswer:\n{result.answer}")
    print(f"\nReasoning Steps:")
    for i, step in enumerate(result.reasoning_steps, 1):
        print(f"  {i}. {step}")
    print(f"\nSources ({len(result.sources)}):")
    for source in result.sources:
        print(f"  - {source['node_id']}: {source['text'][:80]}...")

    print("\n" + "=" * 70)
    print("✅ LLM reasoning test complete!")
    print("=" * 70)
