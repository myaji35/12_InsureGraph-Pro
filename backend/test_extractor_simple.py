"""
Simple manual test for CriticalDataExtractor
Run this without pytest to verify extractor functionality
"""
import sys
sys.path.insert(0, '/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend')

from app.services.ingestion.critical_data_extractor import CriticalDataExtractor


def test_amount_extraction():
    """Test amount extraction"""
    extractor = CriticalDataExtractor()

    tests = [
        ("1억원", 100000000),
        ("2억원", 200000000),
        ("1억 5천만원", 150000000),
        ("5천만원", 50000000),
        ("1천만원", 10000000),
        ("100만원", 1000000),
        ("50만원", 500000),
        ("5천원", 5000),
        ("500원", 500),
    ]

    print("Amount Extraction Tests:")
    print("=" * 60)
    passed = 0
    for text, expected in tests:
        result = extractor.extract(f"보험금은 {text}입니다.")
        if result.has_amounts() and result.amounts[0].value == expected:
            print(f"✓ {text:20s} → {expected:15,d} ✓")
            passed += 1
        else:
            actual = result.amounts[0].value if result.has_amounts() else "N/A"
            print(f"✗ {text:20s} → Expected: {expected:,}, Got: {actual}")

    print(f"\nPassed: {passed}/{len(tests)}\n")
    return passed == len(tests)


def test_period_extraction():
    """Test period extraction"""
    extractor = CriticalDataExtractor()

    tests = [
        ("90일", 90),
        ("3개월", 90),
        ("1년", 365),
        ("2주", 14),
        ("30일", 30),
    ]

    print("Period Extraction Tests:")
    print("=" * 60)
    passed = 0
    for text, expected in tests:
        result = extractor.extract(f"기간은 {text}입니다.")
        if result.has_periods() and result.periods[0].days == expected:
            print(f"✓ {text:15s} → {expected:3d} days ✓")
            passed += 1
        else:
            actual = result.periods[0].days if result.has_periods() else "N/A"
            print(f"✗ {text:15s} → Expected: {expected}, Got: {actual}")

    print(f"\nPassed: {passed}/{len(tests)}\n")
    return passed == len(tests)


def test_kcd_code_extraction():
    """Test KCD code extraction"""
    extractor = CriticalDataExtractor()

    tests = [
        ("C77", "C77", False),
        ("C22", "C22", False),
        ("I21-I25", "I21-I25", True),
        ("C18-C20", "C18-C20", True),
        ("C00-D48", "C00-D48", True),
    ]

    print("KCD Code Extraction Tests:")
    print("=" * 60)
    passed = 0
    for text, expected, is_range in tests:
        result = extractor.extract(f"질병코드 {text}입니다.")
        if (result.has_kcd_codes() and
            result.kcd_codes[0].code == expected and
            result.kcd_codes[0].is_range == is_range):
            range_str = "(range)" if is_range else "(single)"
            print(f"✓ {text:15s} → {expected:15s} {range_str} ✓")
            passed += 1
        else:
            if result.has_kcd_codes():
                actual = result.kcd_codes[0].code
                actual_range = result.kcd_codes[0].is_range
                print(f"✗ {text:15s} → Expected: {expected}, Got: {actual} (range: {actual_range})")
            else:
                print(f"✗ {text:15s} → No KCD codes found")

    print(f"\nPassed: {passed}/{len(tests)}\n")
    return passed == len(tests)


def test_integrated():
    """Test integrated extraction"""
    extractor = CriticalDataExtractor()

    text = """
    회사는 피보험자가 보험기간 중 암(C00-C97)으로 진단확정되었을 때
    다음 각 호의 암진단급여금을 지급합니다.
    1. 일반암(C77 제외): 1억원
    2. 소액암(C77): 1천만원
    3. 고액암(C18-C20): 2억원
    다만, 계약일로부터 90일 이내에 진단확정된 경우는 보험금을 지급하지 않습니다.
    """

    result = extractor.extract(text)

    print("Integrated Extraction Test:")
    print("=" * 60)
    print(f"Text length: {len(text)} characters\n")

    print(f"Amounts found: {len(result.amounts)}")
    for i, amount in enumerate(result.amounts, 1):
        print(f"  {i}. {amount.original_text:15s} → {amount.value:15,d} at pos {amount.position}")

    print(f"\nPeriods found: {len(result.periods)}")
    for i, period in enumerate(result.periods, 1):
        print(f"  {i}. {period.original_text:10s} → {period.days:3d} days at pos {period.position}")

    print(f"\nKCD codes found: {len(result.kcd_codes)}")
    for i, code in enumerate(result.kcd_codes, 1):
        range_str = "(range)" if code.is_range else "(single)"
        print(f"  {i}. {code.original_text:15s} → {code.code:15s} {range_str} at pos {code.position}")

    expected_amounts = 3
    expected_periods = 1
    expected_codes = 4  # C00-C97, C77, C77, C18-C20

    success = (
        len(result.amounts) == expected_amounts and
        len(result.periods) == expected_periods and
        len(result.kcd_codes) >= expected_codes
    )

    print(f"\n{'✓ PASS' if success else '✗ FAIL'}\n")
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("Critical Data Extractor Manual Tests")
    print("=" * 60)
    print()

    results = []
    results.append(test_amount_extraction())
    results.append(test_period_extraction())
    results.append(test_kcd_code_extraction())
    results.append(test_integrated())

    print("=" * 60)
    total_passed = sum(results)
    print(f"Test Suite Results: {total_passed}/{len(results)} groups passed")
    if all(results):
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
