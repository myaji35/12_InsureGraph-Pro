"""
Query Parser & Intent Detection Service

Parses natural language queries about insurance policies and detects user intent.

Supported Query Types:
1. SEARCH - Simple keyword search ("암보험 보장 내용")
2. COMPARISON - Compare multiple policies ("A보험과 B보험 비교")
3. AMOUNT_FILTER - Filter by amount ("1억원 이상 보장")
4. COVERAGE_CHECK - Check specific coverage ("심근경색 보장되나요?")
5. EXCLUSION_CHECK - Check exclusions ("면책 조항은?")
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re


class QueryIntent(str, Enum):
    """User query intent types"""
    SEARCH = "search"  # General keyword search
    COMPARISON = "comparison"  # Compare policies
    AMOUNT_FILTER = "amount_filter"  # Filter by amount
    COVERAGE_CHECK = "coverage_check"  # Check if something is covered
    EXCLUSION_CHECK = "exclusion_check"  # Check exclusions
    PERIOD_CHECK = "period_check"  # Check waiting periods
    UNKNOWN = "unknown"


@dataclass
class ParsedEntity:
    """Extracted entity from query"""
    entity_type: str  # "amount", "period", "disease", "keyword"
    value: str
    normalized_value: Optional[any] = None


@dataclass
class ParsedQuery:
    """Parsed query with intent and entities"""
    original_query: str
    intent: QueryIntent
    entities: List[ParsedEntity]
    keywords: List[str]

    # Specific filters
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    disease_codes: List[str] = None
    insurers: List[str] = None

    def __post_init__(self):
        if self.disease_codes is None:
            self.disease_codes = []
        if self.insurers is None:
            self.insurers = []


class QueryParser:
    """
    Parses natural language queries and detects intent.

    Features:
    - Intent classification
    - Entity extraction (amounts, periods, diseases)
    - Keyword extraction
    - Query normalization
    """

    # Intent detection patterns
    COMPARISON_KEYWORDS = ["비교", "차이", "어떤게", "어느게", "vs"]
    COVERAGE_KEYWORDS = ["보장", "지급", "받을 수", "해당", "포함"]
    EXCLUSION_KEYWORDS = ["면책", "제외", "안되는", "못받는", "불가"]
    PERIOD_KEYWORDS = ["기간", "대기", "경과", "후", "이내"]

    # Amount patterns
    AMOUNT_PATTERNS = [
        (r'(\d+)\s*억\s*(\d+)\s*만\s*원', 'oku_man'),
        (r'(\d+)\s*억\s*원', 'oku'),
        (r'(\d+)\s*천\s*만\s*원', 'sen_man'),
        (r'(\d+)\s*만\s*원', 'man'),
        (r'(\d+)\s*천\s*원', 'sen'),
        (r'(\d+)\s*원', 'won'),
    ]

    # Period patterns
    PERIOD_PATTERNS = [
        (r'(\d+)\s*년', 365),
        (r'(\d+)\s*개월', 30),
        (r'(\d+)\s*주', 7),
        (r'(\d+)\s*일', 1),
    ]

    # Disease name patterns
    DISEASE_PATTERNS = [
        r'암',
        r'심근경색',
        r'뇌졸중',
        r'당뇨',
        r'고혈압',
        r'치매',
        r'암종',
    ]

    def __init__(self):
        """Initialize query parser"""
        pass

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query.

        Args:
            query: User's natural language query

        Returns:
            ParsedQuery with intent and entities
        """
        # Normalize query
        normalized = query.strip()

        # 1. Detect intent
        intent = self._detect_intent(normalized)

        # 2. Extract entities
        entities = []

        # Extract amounts
        amounts = self._extract_amounts(normalized)
        entities.extend(amounts)

        # Extract periods
        periods = self._extract_periods(normalized)
        entities.extend(periods)

        # Extract disease names
        diseases = self._extract_diseases(normalized)
        entities.extend(diseases)

        # 3. Extract keywords (simple tokenization)
        keywords = self._extract_keywords(normalized)

        # 4. Build parsed query
        parsed = ParsedQuery(
            original_query=query,
            intent=intent,
            entities=entities,
            keywords=keywords,
        )

        # Set specific filters
        for entity in entities:
            if entity.entity_type == "amount":
                if "이상" in query or "초과" in query:
                    parsed.min_amount = entity.normalized_value
                elif "이하" in query or "미만" in query:
                    parsed.max_amount = entity.normalized_value
                else:
                    # Default: use as min amount
                    parsed.min_amount = entity.normalized_value

        return parsed

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect query intent from keywords"""
        query_lower = query.lower()

        # Check for comparison
        if any(kw in query_lower for kw in self.COMPARISON_KEYWORDS):
            return QueryIntent.COMPARISON

        # Check for exclusions
        if any(kw in query_lower for kw in self.EXCLUSION_KEYWORDS):
            return QueryIntent.EXCLUSION_CHECK

        # Check for coverage
        if any(kw in query_lower for kw in self.COVERAGE_KEYWORDS):
            return QueryIntent.COVERAGE_CHECK

        # Check for periods
        if any(kw in query_lower for kw in self.PERIOD_KEYWORDS):
            return QueryIntent.PERIOD_CHECK

        # Check for amount filter
        if self._extract_amounts(query):
            return QueryIntent.AMOUNT_FILTER

        # Default to search
        return QueryIntent.SEARCH

    def _extract_amounts(self, text: str) -> List[ParsedEntity]:
        """Extract amount entities"""
        amounts = []
        processed_positions = set()

        for pattern, amount_type in self.AMOUNT_PATTERNS:
            for match in re.finditer(pattern, text):
                start, end = match.span()

                # Skip if already processed
                if any(start <= pos < end for pos in processed_positions):
                    continue

                # Normalize
                normalized = self._normalize_amount(match, amount_type)

                entity = ParsedEntity(
                    entity_type="amount",
                    value=match.group(0),
                    normalized_value=normalized,
                )
                amounts.append(entity)

                # Mark as processed
                for pos in range(start, end):
                    processed_positions.add(pos)

        return amounts

    def _normalize_amount(self, match: re.Match, amount_type: str) -> int:
        """Normalize Korean amount to integer"""
        def clean_number(s: str) -> int:
            return int(s.replace(',', ''))

        if amount_type == 'oku_man':
            oku = clean_number(match.group(1))
            man = clean_number(match.group(2))
            return oku * 100000000 + man * 10000
        elif amount_type == 'oku':
            oku = clean_number(match.group(1))
            return oku * 100000000
        elif amount_type == 'sen_man':
            sen = clean_number(match.group(1))
            return sen * 10000000
        elif amount_type == 'man':
            man = clean_number(match.group(1))
            return man * 10000
        elif amount_type == 'sen':
            sen = clean_number(match.group(1))
            return sen * 1000
        elif amount_type == 'won':
            return clean_number(match.group(1))

        return 0

    def _extract_periods(self, text: str) -> List[ParsedEntity]:
        """Extract period entities"""
        periods = []
        processed_positions = set()

        for pattern, multiplier in self.PERIOD_PATTERNS:
            for match in re.finditer(pattern, text):
                start, end = match.span()

                if any(start <= pos < end for pos in processed_positions):
                    continue

                value = int(match.group(1))
                normalized_days = value * multiplier

                entity = ParsedEntity(
                    entity_type="period",
                    value=match.group(0),
                    normalized_value=normalized_days,
                )
                periods.append(entity)

                for pos in range(start, end):
                    processed_positions.add(pos)

        return periods

    def _extract_diseases(self, text: str) -> List[ParsedEntity]:
        """Extract disease name entities"""
        diseases = []

        for pattern in self.DISEASE_PATTERNS:
            for match in re.finditer(pattern, text):
                entity = ParsedEntity(
                    entity_type="disease",
                    value=match.group(0),
                    normalized_value=match.group(0),
                )
                diseases.append(entity)

        return diseases

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from query (simple tokenization)"""
        # Remove punctuation
        cleaned = re.sub(r'[^\w\s]', ' ', text)

        # Split on whitespace
        words = cleaned.split()

        # Filter out short words and common words
        stopwords = {'은', '는', '이', '가', '을', '를', '의', '에', '와', '과', '도'}
        keywords = [
            word for word in words
            if len(word) >= 2 and word not in stopwords
        ]

        return keywords


# Singleton instance
_query_parser: Optional[QueryParser] = None


def get_query_parser() -> QueryParser:
    """Get or create singleton query parser instance"""
    global _query_parser
    if _query_parser is None:
        _query_parser = QueryParser()
    return _query_parser


if __name__ == "__main__":
    # Test query parser
    test_queries = [
        "암보험 보장 내용",
        "1억원 이상 보장하는 암보험",
        "심근경색 보장되나요?",
        "면책 조항은 뭐가 있나요?",
        "A보험과 B보험 비교해주세요",
        "90일 대기기간",
    ]

    print("=" * 70)
    print("🧪 Query Parser Test")
    print("=" * 70)

    parser = get_query_parser()

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        parsed = parser.parse(query)

        print(f"   Intent: {parsed.intent.value}")
        print(f"   Keywords: {parsed.keywords}")

        if parsed.entities:
            print(f"   Entities:")
            for entity in parsed.entities:
                print(f"     - {entity.entity_type}: {entity.value} → {entity.normalized_value}")

        if parsed.min_amount:
            print(f"   Min amount: {parsed.min_amount:,}원")
        if parsed.max_amount:
            print(f"   Max amount: {parsed.max_amount:,}원")

    print("\n" + "=" * 70)
    print("✅ Query parser test complete!")
    print("=" * 70)
