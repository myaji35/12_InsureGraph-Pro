"""
Critical Data Extractor Service

보험 약관에서 중요한 수치 데이터를 100% 정확하게 추출
- 금액 (1억원, 100만원 등)
- 기간 (90일, 3개월, 1년 등)
- KCD 질병 코드 (C77, I21-I25 등)
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ExtractedAmount:
    """추출된 금액"""
    original_text: str
    normalized_value: int  # 원 단위
    start_pos: int
    end_pos: int
    confidence: float = 1.0


@dataclass
class ExtractedPeriod:
    """추출된 기간"""
    original_text: str
    normalized_days: int  # 일 단위
    start_pos: int
    end_pos: int
    confidence: float = 1.0


@dataclass
class ExtractedKCDCode:
    """추출된 KCD 코드"""
    code: str
    start_pos: int
    end_pos: int
    is_range: bool = False
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """전체 추출 결과"""
    amounts: List[ExtractedAmount]
    periods: List[ExtractedPeriod]
    kcd_codes: List[ExtractedKCDCode]

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "amounts": [
                {
                    "original_text": a.original_text,
                    "normalized_value": a.normalized_value,
                    "start_pos": a.start_pos,
                    "end_pos": a.end_pos,
                    "confidence": a.confidence,
                }
                for a in self.amounts
            ],
            "periods": [
                {
                    "original_text": p.original_text,
                    "normalized_days": p.normalized_days,
                    "start_pos": p.start_pos,
                    "end_pos": p.end_pos,
                    "confidence": p.confidence,
                }
                for p in self.periods
            ],
            "kcd_codes": [
                {
                    "code": k.code,
                    "start_pos": k.start_pos,
                    "end_pos": k.end_pos,
                    "is_range": k.is_range,
                    "confidence": k.confidence,
                }
                for k in self.kcd_codes
            ],
        }


class CriticalDataExtractor:
    """중요 데이터 추출기"""

    # 금액 패턴 (우선순위 순서)
    AMOUNT_PATTERNS = [
        # 1억 5천만원
        (re.compile(r'(\d+(?:,\d+)?)\s*억\s*(\d+(?:,\d+)?)\s*만\s*원'), 'oku_man'),
        # 1억원
        (re.compile(r'(\d+(?:,\d+)?)\s*억\s*원'), 'oku'),
        # 1천만원 (천만 조합)
        (re.compile(r'(\d+(?:,\d+)?)\s*천\s*만\s*원'), 'sen_man'),
        # 1000만원
        (re.compile(r'(\d+(?:,\d+)?)\s*만\s*원'), 'man'),
        # 5천원
        (re.compile(r'(\d+(?:,\d+)?)\s*천\s*원'), 'sen'),
        # 100원
        (re.compile(r'(\d+(?:,\d+)?)\s*원'), 'won'),
    ]

    # 기간 패턴
    PERIOD_PATTERNS = [
        (re.compile(r'(\d+)\s*년'), 365),
        (re.compile(r'(\d+)\s*개월'), 30),
        (re.compile(r'(\d+)\s*주'), 7),
        (re.compile(r'(\d+)\s*일'), 1),
    ]

    # KCD 코드 패턴
    KCD_PATTERN = re.compile(r'\b([A-Z]\d{2}(?:-[A-Z]?\d{2})?)\b')

    def __init__(self):
        """Initialize extractor"""
        pass

    def extract_all(self, text: str) -> ExtractionResult:
        """
        모든 중요 데이터 추출

        Args:
            text: 조항 텍스트

        Returns:
            ExtractionResult: 추출 결과
        """
        amounts = self.extract_amounts(text)
        periods = self.extract_periods(text)
        kcd_codes = self.extract_kcd_codes(text)

        return ExtractionResult(
            amounts=amounts,
            periods=periods,
            kcd_codes=kcd_codes,
        )

    def extract_amounts(self, text: str) -> List[ExtractedAmount]:
        """
        금액 추출

        Args:
            text: 텍스트

        Returns:
            List[ExtractedAmount]: 추출된 금액 목록
        """
        amounts = []
        processed_positions = set()

        for pattern, amount_type in self.AMOUNT_PATTERNS:
            for match in pattern.finditer(text):
                start_pos = match.start()
                end_pos = match.end()

                # 이미 처리된 위치는 건너뛰기 (중복 방지)
                if any(start_pos <= pos < end_pos for pos in processed_positions):
                    continue

                # 정규화된 값 계산
                normalized_value = self._normalize_amount(match, amount_type)

                amounts.append(ExtractedAmount(
                    original_text=match.group(0),
                    normalized_value=normalized_value,
                    start_pos=start_pos,
                    end_pos=end_pos,
                ))

                # 처리된 위치 기록
                for pos in range(start_pos, end_pos):
                    processed_positions.add(pos)

        # 위치 순으로 정렬
        amounts.sort(key=lambda x: x.start_pos)

        logger.debug(f"Extracted {len(amounts)} amounts from text")
        return amounts

    def _normalize_amount(self, match: re.Match, amount_type: str) -> int:
        """금액을 원 단위로 정규화"""
        def clean_number(s: str) -> int:
            """쉼표 제거 후 정수 변환"""
            return int(s.replace(',', '')) if s else 0

        if amount_type == 'oku_man':
            # 1억 5천만원 -> 150,000,000
            oku = clean_number(match.group(1))
            man = clean_number(match.group(2))
            return (oku * 100000000) + (man * 10000)

        elif amount_type == 'oku':
            # 1억원 -> 100,000,000
            oku = clean_number(match.group(1))
            return oku * 100000000

        elif amount_type == 'sen_man':
            # 1천만원 -> 10,000,000
            sen = clean_number(match.group(1))
            return sen * 10000000

        elif amount_type == 'man':
            # 1000만원 -> 10,000,000
            man = clean_number(match.group(1))
            return man * 10000

        elif amount_type == 'sen':
            # 5천원 -> 5,000
            sen = clean_number(match.group(1))
            return sen * 1000

        elif amount_type == 'won':
            # 100원 -> 100
            won = clean_number(match.group(1))
            return won

        return 0

    def extract_periods(self, text: str) -> List[ExtractedPeriod]:
        """
        기간 추출

        Args:
            text: 텍스트

        Returns:
            List[ExtractedPeriod]: 추출된 기간 목록
        """
        periods = []

        for pattern, days_multiplier in self.PERIOD_PATTERNS:
            for match in pattern.finditer(text):
                num = int(match.group(1))
                normalized_days = num * days_multiplier

                periods.append(ExtractedPeriod(
                    original_text=match.group(0),
                    normalized_days=normalized_days,
                    start_pos=match.start(),
                    end_pos=match.end(),
                ))

        # 위치 순으로 정렬
        periods.sort(key=lambda x: x.start_pos)

        logger.debug(f"Extracted {len(periods)} periods from text")
        return periods

    def extract_kcd_codes(self, text: str) -> List[ExtractedKCDCode]:
        """
        KCD 질병 코드 추출

        Args:
            text: 텍스트

        Returns:
            List[ExtractedKCDCode]: 추출된 KCD 코드 목록
        """
        kcd_codes = []

        for match in self.KCD_PATTERN.finditer(text):
            code = match.group(1)
            is_range = '-' in code

            kcd_codes.append(ExtractedKCDCode(
                code=code,
                start_pos=match.start(),
                end_pos=match.end(),
                is_range=is_range,
            ))

        logger.debug(f"Extracted {len(kcd_codes)} KCD codes from text")
        return kcd_codes


# Singleton instance
_critical_extractor: Optional[CriticalDataExtractor] = None


def get_critical_extractor() -> CriticalDataExtractor:
    """중요 데이터 추출기 싱글톤 인스턴스"""
    global _critical_extractor
    if _critical_extractor is None:
        _critical_extractor = CriticalDataExtractor()
    return _critical_extractor
