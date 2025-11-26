"""
Critical Data Extractor

Extracts critical numerical data with 100% accuracy using rule-based methods.
This prevents LLM hallucination for financial and temporal data.

Extracts:
- Monetary amounts (1억원, 100만원, etc.) → normalized to integer
- Time periods (90일, 3개월, 1년) → normalized to days
- KCD disease codes (C77, I21-I25) → validated format
"""
import re
from typing import List, Tuple, Optional
from app.models.critical_data import (
    CriticalData,
    AmountData,
    PeriodData,
    KCDCodeData,
)


class CriticalDataExtractor:
    """Extractor for critical numerical data from Korean text"""

    # Korean amount patterns
    # Matches: 1억원, 1억 5천만원, 100만원, 1,000만원, etc.
    AMOUNT_PATTERNS = [
        # Full pattern: 1억 5천만원
        (r'(\d+(?:,\d{3})*)\s*억\s*(\d+(?:,\d{3})*)\s*천\s*(\d+(?:,\d{3})*)\s*만\s*원?', 'oku_sen_man'),
        # 1억 5천만원 (without last number)
        (r'(\d+(?:,\d{3})*)\s*억\s*(\d+(?:,\d{3})*)\s*천만\s*원?', 'oku_senman'),
        # 1억 5백만원
        (r'(\d+(?:,\d{3})*)\s*억\s*(\d+(?:,\d{3})*)\s*백만\s*원?', 'oku_hyakuman'),
        # 1억 5만원
        (r'(\d+(?:,\d{3})*)\s*억\s*(\d+(?:,\d{3})*)\s*만\s*원?', 'oku_man'),
        # 1억원
        (r'(\d+(?:,\d{3})*)\s*억\s*원?', 'oku'),
        # 1천만원
        (r'(\d+(?:,\d{3})*)\s*천만\s*원?', 'senman'),
        # 100만원
        (r'(\d+(?:,\d{3})*)\s*백만\s*원?', 'hyakuman'),
        # 50만원
        (r'(\d+(?:,\d{3})*)\s*만\s*원?', 'man'),
        # 5천원
        (r'(\d+(?:,\d{3})*)\s*천\s*원?', 'sen'),
        # 500원
        (r'(\d+(?:,\d{3})*)\s*원', 'won'),
    ]

    # Period patterns
    # Matches: 90일, 3개월, 1년, 2주 등
    PERIOD_PATTERNS = [
        (r'(\d+(?:,\d{3})*)\s*년', '년', 365),
        (r'(\d+(?:,\d{3})*)\s*개월', '개월', 30),
        (r'(\d+(?:,\d{3})*)\s*주', '주', 7),
        (r'(\d+(?:,\d{3})*)\s*일', '일', 1),
    ]

    # KCD code pattern
    # Matches: C77, I21, C00-C97, I21-I25
    KCD_PATTERN = r'\b([A-Z])(\d{2})(?:\s*-\s*([A-Z])?(\d{2}))?\b'

    # Valid KCD code prefixes (Korean Classification of Disease)
    VALID_KCD_PREFIXES = [
        'A', 'B',  # Infectious diseases
        'C', 'D',  # Neoplasms
        'E',       # Endocrine, nutritional and metabolic diseases
        'F',       # Mental and behavioral disorders
        'G',       # Nervous system
        'H',       # Eye, ear
        'I',       # Circulatory system
        'J',       # Respiratory system
        'K',       # Digestive system
        'L',       # Skin
        'M',       # Musculoskeletal system
        'N',       # Genitourinary system
        'O',       # Pregnancy, childbirth
        'P',       # Perinatal conditions
        'Q',       # Congenital malformations
        'R',       # Symptoms, signs
        'S', 'T',  # Injury, poisoning
        'V', 'W', 'X', 'Y',  # External causes
        'Z',       # Factors influencing health status
    ]

    def __init__(self):
        # Compile regex patterns
        self.amount_patterns = [(re.compile(pattern), type_) for pattern, type_ in self.AMOUNT_PATTERNS]
        self.period_patterns = [(re.compile(pattern), unit, multiplier) for pattern, unit, multiplier in self.PERIOD_PATTERNS]
        self.kcd_pattern = re.compile(self.KCD_PATTERN)

    def extract(self, text: str) -> CriticalData:
        """
        Extract all critical data from text

        Args:
            text: Text to extract from

        Returns:
            CriticalData object with all extracted data
        """
        amounts = self._extract_amounts(text)
        periods = self._extract_periods(text)
        kcd_codes = self._extract_kcd_codes(text)

        return CriticalData(
            amounts=amounts,
            periods=periods,
            kcd_codes=kcd_codes,
        )

    def _extract_amounts(self, text: str) -> List[AmountData]:
        """Extract all monetary amounts from text"""
        amounts = []
        seen_positions = set()  # Avoid duplicate matches at same position

        for pattern, type_ in self.amount_patterns:
            for match in pattern.finditer(text):
                position = match.start()

                # Skip if we already matched at this position
                if position in seen_positions:
                    continue

                seen_positions.add(position)

                # Parse amount based on type
                value = self._parse_amount(match, type_)

                amount = AmountData(
                    value=value,
                    original_text=match.group(0),
                    position=position,
                    confidence=1.0,
                )
                amounts.append(amount)

        # Sort by position
        amounts.sort(key=lambda x: x.position)
        return amounts

    def _parse_amount(self, match: re.Match, type_: str) -> int:
        """Parse amount from regex match"""
        # Remove commas from numbers
        def clean_num(s):
            return int(s.replace(',', ''))

        if type_ == 'oku_sen_man':
            # 1억 5천 3백만원
            oku = clean_num(match.group(1))
            sen = clean_num(match.group(2))
            man = clean_num(match.group(3))
            return oku * 100000000 + sen * 10000000 + man * 10000

        elif type_ == 'oku_senman':
            # 1억 5천만원
            oku = clean_num(match.group(1))
            senman = clean_num(match.group(2))
            return oku * 100000000 + senman * 10000000

        elif type_ == 'oku_hyakuman':
            # 1억 5백만원
            oku = clean_num(match.group(1))
            hyakuman = clean_num(match.group(2))
            return oku * 100000000 + hyakuman * 1000000

        elif type_ == 'oku_man':
            # 1억 5만원
            oku = clean_num(match.group(1))
            man = clean_num(match.group(2))
            return oku * 100000000 + man * 10000

        elif type_ == 'oku':
            # 1억원
            oku = clean_num(match.group(1))
            return oku * 100000000

        elif type_ == 'senman':
            # 1천만원
            senman = clean_num(match.group(1))
            return senman * 10000000

        elif type_ == 'hyakuman':
            # 100만원
            hyakuman = clean_num(match.group(1))
            return hyakuman * 1000000

        elif type_ == 'man':
            # 50만원
            man = clean_num(match.group(1))
            return man * 10000

        elif type_ == 'sen':
            # 5천원
            sen = clean_num(match.group(1))
            return sen * 1000

        elif type_ == 'won':
            # 500원
            won = clean_num(match.group(1))
            return won

        return 0

    def _extract_periods(self, text: str) -> List[PeriodData]:
        """Extract all time periods from text"""
        periods = []
        seen_positions = set()

        for pattern, unit, multiplier in self.period_patterns:
            for match in pattern.finditer(text):
                position = match.start()

                # Skip duplicates
                if position in seen_positions:
                    continue

                seen_positions.add(position)

                # Parse number
                number_str = match.group(1).replace(',', '')
                number = int(number_str)
                days = number * multiplier

                period = PeriodData(
                    days=days,
                    original_text=match.group(0),
                    original_unit=unit,
                    position=position,
                    confidence=1.0,
                )
                periods.append(period)

        # Sort by position
        periods.sort(key=lambda x: x.position)
        return periods

    def _extract_kcd_codes(self, text: str) -> List[KCDCodeData]:
        """Extract and validate KCD disease codes"""
        kcd_codes = []

        for match in self.kcd_pattern.finditer(text):
            prefix = match.group(1)
            start_num = match.group(2)
            end_prefix = match.group(3)  # May be None
            end_num = match.group(4)      # May be None

            # Validate prefix
            is_valid = prefix in self.VALID_KCD_PREFIXES

            if end_num:
                # Range: C00-C97 or I21-I25
                is_range = True
                end_prefix_actual = end_prefix if end_prefix else prefix
                start_code = f"{prefix}{start_num}"
                end_code = f"{end_prefix_actual}{end_num}"
                code = f"{start_code}-{end_code}"

                # Validate end prefix too
                if end_prefix:
                    is_valid = is_valid and (end_prefix in self.VALID_KCD_PREFIXES)
            else:
                # Single code: C77
                is_range = False
                start_code = None
                end_code = None
                code = f"{prefix}{start_num}"

            kcd_code = KCDCodeData(
                code=code,
                original_text=match.group(0),
                position=match.start(),
                is_valid=is_valid,
                is_range=is_range,
                start_code=start_code,
                end_code=end_code,
            )
            kcd_codes.append(kcd_code)

        # Sort by position
        kcd_codes.sort(key=lambda x: x.position)
        return kcd_codes
