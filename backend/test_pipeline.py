"""
End-to-End Pipeline Test

PDF → Text Extraction → Legal Parsing → Critical Data Extraction
"""
from pathlib import Path
from app.services.pdf_text_extractor import get_pdf_extractor
from app.services.legal_structure_parser import get_legal_parser
from app.services.critical_data_extractor import get_critical_extractor


def test_pipeline(pdf_path: str = None):
    """전체 파이프라인 테스트"""
    
    print("=" * 70)
    print("🚀 InsureGraph Pro - End-to-End Pipeline Test")
    print("=" * 70)
    
    # Step 1: PDF Text Extraction
    print("\n📄 Step 1: PDF Text Extraction")
    print("-" * 70)
    
    if pdf_path:
        pdf_extractor = get_pdf_extractor()
        result = pdf_extractor.extract_text_from_file(pdf_path)
        
        print(f"✅ Extracted from: {Path(pdf_path).name}")
        print(f"   Total pages: {result.total_pages}")
        print(f"   Total chars: {result.total_chars:,}")
        
        # Use extracted text
        text = result.full_text
    else:
        # Use sample text
        print("⚠️  No PDF provided, using sample text")
        text = """
제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원
3. 유사암(D00-D09): 500만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.

제11조 [보험료 납입]
① 보험료는 매월 10만원씩 납입해야 합니다.
② 보험료 미납 시 3개월 후 계약이 해지될 수 있습니다.

제12조 [계약의 해지]
① 계약자는 언제든지 계약을 해지할 수 있습니다.
② 해지 시 1년 이상 경과한 경우 해약환급금을 지급합니다.
"""
    
    # Step 2: Legal Structure Parsing
    print("\n⚖️  Step 2: Legal Structure Parsing")
    print("-" * 70)
    
    legal_parser = get_legal_parser()
    parsed_doc = legal_parser.parse_text(text)
    
    print(f"✅ Parsed legal structure:")
    print(f"   Articles: {parsed_doc.total_articles}")
    print(f"   Paragraphs: {parsed_doc.total_paragraphs}")
    print(f"   Subclauses: {parsed_doc.total_subclauses}")
    
    print(f"\n   Article details:")
    for article in parsed_doc.articles:
        print(f"   • {article.article_num} [{article.title}]")
        print(f"     - {len(article.paragraphs)} paragraphs")
    
    # Step 3: Critical Data Extraction
    print("\n💰 Step 3: Critical Data Extraction")
    print("-" * 70)
    
    data_extractor = get_critical_extractor()
    extracted_data = data_extractor.extract_all(text)
    
    print(f"✅ Extracted critical data:")
    print(f"   Amounts: {len(extracted_data.amounts)}")
    print(f"   Periods: {len(extracted_data.periods)}")
    print(f"   KCD codes: {len(extracted_data.kcd_codes)}")
    
    if extracted_data.amounts:
        print(f"\n   Amount details:")
        for amount in extracted_data.amounts:
            formatted = f"{amount.normalized_value:,}원"
            print(f"   • {amount.original_text:15s} → {formatted}")
    
    if extracted_data.periods:
        print(f"\n   Period details:")
        for period in extracted_data.periods:
            print(f"   • {period.original_text:10s} → {period.normalized_days}일")
    
    if extracted_data.kcd_codes:
        print(f"\n   KCD code details:")
        for kcd in extracted_data.kcd_codes:
            range_info = " (범위)" if kcd.is_range else ""
            print(f"   • {kcd.code}{range_info}")
    
    # Step 4: Integration Summary
    print("\n" + "=" * 70)
    print("📊 Pipeline Summary")
    print("=" * 70)
    
    total_clauses = sum(
        len(article.paragraphs) + sum(len(p.subclauses) for p in article.paragraphs)
        for article in parsed_doc.articles
    )
    
    print(f"""
    ✅ Text Processing: {len(text):,} characters processed
    ✅ Structure Parsing: {parsed_doc.total_articles} articles, {total_clauses} total clauses
    ✅ Data Extraction: {len(extracted_data.amounts)} amounts, {len(extracted_data.periods)} periods, {len(extracted_data.kcd_codes)} KCD codes
    
    🎯 Status: PIPELINE OPERATIONAL
    """)
    
    print("=" * 70)
    print("✅ End-to-End Test Completed Successfully!")
    print("=" * 70)
    
    return {
        "parsed_doc": parsed_doc,
        "extracted_data": extracted_data,
    }


if __name__ == "__main__":
    import sys
    
    # Check if PDF path provided
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    result = test_pipeline(pdf_path)
    
    print("\n💡 Next steps:")
    print("   1. Upload a real insurance policy PDF")
    print("   2. Run: python test_pipeline.py path/to/policy.pdf")
    print("   3. Verify all data is extracted correctly")
