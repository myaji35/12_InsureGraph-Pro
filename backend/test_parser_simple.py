"""
Simple manual test for LegalStructureParser
Run this without pytest to verify parser functionality
"""
import sys
sys.path.insert(0, '/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend')

from app.services.ingestion.legal_parser import LegalStructureParser

def test_simple():
    """Test simple article parsing"""
    parser = LegalStructureParser()

    text = """
    제1조 [보험금의 지급]
    회사는 피보험자가 보험기간 중 암으로 진단확정되었을 때 보험금을 지급합니다.
    """

    result = parser.parse(text, total_pages=1)

    print("Test 1: Simple Article Parsing")
    print(f"  Articles found: {len(result.articles)}")
    if result.articles:
        print(f"  Article number: {result.articles[0].article_num}")
        print(f"  Article title: {result.articles[0].title}")
    print(f"  Confidence: {result.parsing_confidence}")
    print(f"  ✓ PASS\n" if len(result.articles) == 1 else "  ✗ FAIL\n")

def test_with_paragraphs():
    """Test article with paragraphs"""
    parser = LegalStructureParser()

    text = """
    제10조 [암진단급여금 지급]
    ① 회사는 피보험자가 보험기간 중 암으로 진단확정되었을 때 보험금을 지급합니다.
    ② 제1항의 암진단 급여금은 최초 1회에 한하여 지급합니다.
    ③ 피보험자가 사망한 경우 이 계약은 소멸되며 보험금을 지급하지 않습니다.
    """

    result = parser.parse(text, total_pages=1)

    print("Test 2: Article with Paragraphs")
    print(f"  Articles found: {len(result.articles)}")
    if result.articles:
        article = result.articles[0]
        print(f"  Article number: {article.article_num}")
        print(f"  Paragraphs found: {len(article.paragraphs)}")
        for i, para in enumerate(article.paragraphs):
            print(f"    Paragraph {i+1}: {para.paragraph_num}")
    print(f"  Confidence: {result.parsing_confidence}")
    print(f"  ✓ PASS\n" if len(result.articles) == 1 and len(result.articles[0].paragraphs) == 3 else "  ✗ FAIL\n")

def test_exception_clauses():
    """Test exception clause detection"""
    parser = LegalStructureParser()

    text = """
    제5조 [면책기간]
    ① 회사는 보험금을 지급합니다. 다만, 계약일로부터 90일 이내에 진단확정된 경우는 제외합니다.
    """

    result = parser.parse(text, total_pages=1)

    print("Test 3: Exception Clause Detection")
    print(f"  Articles found: {len(result.articles)}")
    if result.articles:
        paragraph = result.articles[0].paragraphs[0]
        print(f"  Has exception: {paragraph.has_exception}")
        print(f"  Exception keywords: {paragraph.exception_keywords}")
    print(f"  ✓ PASS\n" if paragraph.has_exception else "  ✗ FAIL\n")

def test_subclauses():
    """Test subclause parsing"""
    parser = LegalStructureParser()

    text = """
    제8조 [보장내용]
    ① 회사는 다음의 경우 보험금을 지급합니다.
    1. 일반암(C77 제외): 1억원
    2. 소액암(C77): 1천만원
    3. 고액암(C18-C20): 2억원
    """

    result = parser.parse(text, total_pages=1)

    print("Test 4: Numbered Subclauses")
    print(f"  Articles found: {len(result.articles)}")
    if result.articles:
        paragraph = result.articles[0].paragraphs[0]
        print(f"  Subclauses found: {len(paragraph.subclauses)}")
        for sc in paragraph.subclauses:
            print(f"    Subclause {sc.subclause_num}: {sc.text[:30]}...")
    print(f"  ✓ PASS\n" if len(paragraph.subclauses) == 3 else "  ✗ FAIL\n")

def test_complex_document():
    """Test complex document"""
    parser = LegalStructureParser()

    text = """
    제10조 [암진단급여금 지급]
    ① 회사는 피보험자가 다음 각 호의 암으로 진단확정되었을 때 보험금을 지급합니다.
    1. 일반암(C77 제외): 1억원
    2. 소액암(C77): 1천만원
    ② 제1항의 암진단급여금은 최초 1회에 한하여 지급합니다. 다만, 갱신 시에는 재지급할 수 있습니다.

    제11조 [면책기간]
    ① 회사는 계약일로부터 90일 이내에 진단확정된 암에 대해서는 보험금을 지급하지 않습니다.
    ② 제1항에도 불구하고 갱신계약의 경우는 면책기간을 적용하지 않습니다.
    """

    result = parser.parse(text, total_pages=1)

    print("Test 5: Complex Document")
    print(f"  Articles found: {len(result.articles)}")
    print(f"  Total paragraphs: {result.get_total_paragraphs()}")
    print(f"  Total subclauses: {result.get_total_subclauses()}")
    print(f"  Confidence: {result.parsing_confidence}")
    print(f"  Errors: {len(result.parsing_errors)}")
    print(f"  Warnings: {len(result.parsing_warnings)}")

    for i, article in enumerate(result.articles):
        print(f"\n  Article {i+1}: {article.article_num} {article.title}")
        print(f"    Paragraphs: {len(article.paragraphs)}")
        for para in article.paragraphs:
            print(f"      {para.paragraph_num}: has_exception={para.has_exception}, subclauses={len(para.subclauses)}")

    print(f"  ✓ PASS\n" if len(result.articles) == 2 else "  ✗ FAIL\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Legal Structure Parser Manual Tests")
    print("=" * 60)
    print()

    test_simple()
    test_with_paragraphs()
    test_exception_clauses()
    test_subclauses()
    test_complex_document()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
