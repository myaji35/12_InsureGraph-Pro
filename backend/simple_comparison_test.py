"""
Upstage vs pdfplumber 간단 비교 테스트

하드코딩된 샘플 PDF URL로 즉시 테스트 가능
의존성 최소화 버전

Usage:
    python3 simple_comparison_test.py
"""
import asyncio
import time
import re
import httpx
from pathlib import Path


# ============================================================================
# 샘플 PDF URL (실제 공개된 보험약관)
# ============================================================================
SAMPLE_DOCUMENTS = [
    {
        'id': 'sample-1',
        'insurer': '삼성화재',
        'title': '자동차보험 약관 샘플',
        'pdf_url': 'https://www.samsungfire.com/download/termsPDF/car_insurance_terms.pdf',
        'category': '자동차보험',
    },
    # 실제 크롤링된 URL로 교체 필요
]


# ============================================================================
# 간단한 PDF 텍스트 추출 (pdfplumber 방식 시뮬레이션)
# ============================================================================
async def extract_with_pdfplumber(pdf_url: str):
    """pdfplumber를 사용한 간단한 텍스트 추출"""
    print(f"   [pdfplumber] Downloading PDF...")

    try:
        import pdfplumber
        import io

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content

        pdf_file = io.BytesIO(pdf_bytes)

        extracted_text = ""
        total_pages = 0

        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        return {
            'text': extracted_text,
            'total_pages': total_pages,
            'method': 'pdfplumber'
        }

    except Exception as e:
        print(f"   ❌ pdfplumber failed: {e}")
        return None


# ============================================================================
# Upstage Document Parse API (간단 버전)
# ============================================================================
async def extract_with_upstage(pdf_url: str, api_key: str):
    """Upstage Document Parse API를 사용한 텍스트 추출"""
    print(f"   [Upstage] Calling API...")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
            }

            data = {
                "document": pdf_url,
                "ocr": "force",
                "output_formats": "text,html"
            }

            response = await client.post(
                "https://api.upstage.ai/v1/document-ai/document-parse",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            result = response.json()

        # 응답 파싱
        pages = result.get("content", {}).get("pages", [])

        full_text = ""
        for page in pages:
            page_text = page.get("text", "")
            full_text += page_text + "\n\n"

        # 섹션 추출
        sections = extract_sections(full_text)

        # 표 추출
        tables = []
        for page in pages:
            tables.extend(page.get("tables", []))

        return {
            'text': full_text.strip(),
            'total_pages': len(pages),
            'sections': sections,
            'tables': tables,
            'method': 'upstage'
        }

    except Exception as e:
        print(f"   ❌ Upstage failed: {e}")
        return None


def extract_sections(text: str):
    """보험약관 섹션 구조 추출"""
    sections = []

    # 제1장, 제2장 패턴
    chapters = re.findall(r'제(\d+)장\s+(.+?)(?=\n|$)', text)
    for chapter_num, chapter_title in chapters:
        sections.append({
            'type': 'chapter',
            'number': int(chapter_num),
            'title': chapter_title.strip()
        })

    # 제1조, 제2조 패턴
    articles = re.findall(r'제(\d+)조\s*\((.+?)\)', text)
    for article_num, article_title in articles:
        sections.append({
            'type': 'article',
            'number': int(article_num),
            'title': article_title.strip()
        })

    return sections


# ============================================================================
# 품질 점수 계산
# ============================================================================
def calculate_quality_score(text: str):
    """텍스트 품질 점수"""
    if not text:
        return 0.0

    # 한글 비율
    korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
    korean_ratio = korean_chars / len(text) if text else 0

    # 구조 패턴
    chapters = len(re.findall(r'제\d+장', text))
    articles = len(re.findall(r'제\d+조', text))
    structure_score = min((chapters + articles) / 50, 1.0)

    # 종합
    overall = korean_ratio * 0.6 + structure_score * 0.4

    return round(overall, 3)


def calculate_uds_score(text: str, sections=None, tables=None):
    """UDS (Understanding, Detail, Structure) 점수"""
    # Understanding
    quality = calculate_quality_score(text)
    understanding = quality * 100

    # Detail
    text_length = len(text)
    detail = min(text_length / 50000, 1.0) * 100

    # Structure
    if sections:
        structure = min(len(sections) / 50 * 100, 100)
    else:
        structure = min(len(re.findall(r'제\d+조', text)) / 30 * 100, 100)

    # Total
    total = (understanding * 0.3 + detail * 0.3 + structure * 0.4)

    return {
        'understanding': round(understanding, 1),
        'detail': round(detail, 1),
        'structure': round(structure, 1),
        'total': round(total, 1)
    }


# ============================================================================
# 비교 테스트
# ============================================================================
async def compare_methods(pdf_url: str, api_key: str):
    """두 방식 비교"""
    print(f"\n{'='*80}")
    print(f"Testing: {pdf_url}")
    print(f"{'='*80}")

    results = {}

    # 1. pdfplumber
    print("\n[1] pdfplumber test...")
    start = time.time()
    result_pdf = await extract_with_pdfplumber(pdf_url)
    time_pdf = time.time() - start

    if result_pdf:
        quality_pdf = calculate_quality_score(result_pdf['text'])
        uds_pdf = calculate_uds_score(result_pdf['text'])

        results['pdfplumber'] = {
            'time': round(time_pdf, 2),
            'pages': result_pdf['total_pages'],
            'text_length': len(result_pdf['text']),
            'quality': quality_pdf,
            'uds': uds_pdf,
            'sections': 0,
            'tables': 0
        }

        print(f"   ✅ Completed in {time_pdf:.2f}s")
        print(f"   Pages: {result_pdf['total_pages']}, Text: {len(result_pdf['text']):,} chars")
        print(f"   Quality: {quality_pdf:.3f}, UDS: {uds_pdf['total']:.1f}")

    # 2. Upstage
    print("\n[2] Upstage test...")
    start = time.time()
    result_upstage = await extract_with_upstage(pdf_url, api_key)
    time_upstage = time.time() - start

    if result_upstage:
        quality_upstage = calculate_quality_score(result_upstage['text'])
        uds_upstage = calculate_uds_score(
            result_upstage['text'],
            sections=result_upstage.get('sections', []),
            tables=result_upstage.get('tables', [])
        )

        results['upstage'] = {
            'time': round(time_upstage, 2),
            'pages': result_upstage['total_pages'],
            'text_length': len(result_upstage['text']),
            'quality': quality_upstage,
            'uds': uds_upstage,
            'sections': len(result_upstage.get('sections', [])),
            'tables': len(result_upstage.get('tables', []))
        }

        print(f"   ✅ Completed in {time_upstage:.2f}s")
        print(f"   Pages: {result_upstage['total_pages']}, Text: {len(result_upstage['text']):,} chars")
        print(f"   Sections: {len(result_upstage.get('sections', []))}, Tables: {len(result_upstage.get('tables', []))}")
        print(f"   Quality: {quality_upstage:.3f}, UDS: {uds_upstage['total']:.1f}")

    return results


def print_summary(all_results):
    """결과 요약"""
    print("\n" + "="*80)
    print("📊 비교 결과 요약")
    print("="*80)

    print(f"\n{'항목':20s} | {'pdfplumber':15s} | {'Upstage':15s} | {'개선율':10s}")
    print("-" * 80)

    metrics = ['time', 'text_length', 'quality', 'sections', 'tables']
    labels = ['처리 시간 (s)', '텍스트 길이', '품질 점수', '섹션 수', '표 수']

    for metric, label in zip(metrics, labels):
        pdf_vals = [r['pdfplumber'][metric] for r in all_results if 'pdfplumber' in r]
        upstage_vals = [r['upstage'][metric] for r in all_results if 'upstage' in r]

        if pdf_vals and upstage_vals:
            pdf_avg = sum(pdf_vals) / len(pdf_vals)
            upstage_avg = sum(upstage_vals) / len(upstage_vals)

            if metric == 'time':
                # 시간은 적을수록 좋음
                improvement = ((pdf_avg - upstage_avg) / pdf_avg * 100) if pdf_avg > 0 else 0
            else:
                # 나머지는 많을수록 좋음
                improvement = ((upstage_avg - pdf_avg) / pdf_avg * 100) if pdf_avg > 0 else 0

            if metric == 'quality':
                print(f"{label:20s} | {pdf_avg:15.3f} | {upstage_avg:15.3f} | {improvement:+9.1f}%")
            else:
                print(f"{label:20s} | {pdf_avg:15.0f} | {upstage_avg:15.0f} | {improvement:+9.1f}%")

    # UDS 점수
    print("\n" + "="*80)
    print("🎯 UDS 해석력 비교")
    print("="*80)

    uds_metrics = ['understanding', 'detail', 'structure', 'total']
    uds_labels = ['이해도 (U)', '상세도 (D)', '구조화 (S)', '총점']

    for metric, label in zip(uds_metrics, uds_labels):
        pdf_vals = [r['pdfplumber']['uds'][metric] for r in all_results if 'pdfplumber' in r]
        upstage_vals = [r['upstage']['uds'][metric] for r in all_results if 'upstage' in r]

        if pdf_vals and upstage_vals:
            pdf_avg = sum(pdf_vals) / len(pdf_vals)
            upstage_avg = sum(upstage_vals) / len(upstage_vals)
            improvement = ((upstage_avg - pdf_avg) / pdf_avg * 100) if pdf_avg > 0 else 0

            print(f"{label:20s} | {pdf_avg:15.1f} | {upstage_avg:15.1f} | {improvement:+9.1f}%")

    print("\n" + "="*80)


# ============================================================================
# 메인
# ============================================================================
async def main():
    print("\n" + "="*80)
    print("🔬 PDF 텍스트 추출 방식 비교 테스트")
    print("="*80)
    print("\npdfplumber (현재) vs Upstage Document Parse (신규)")

    # API 키 확인
    import os
    api_key = os.getenv('UPSTAGE_API_KEY')

    if not api_key:
        print("\n❌ UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("실행 방법:")
        print("  export UPSTAGE_API_KEY='your_api_key'")
        print("  python3 simple_comparison_test.py")
        return

    # 테스트할 URL 입력
    print("\n📋 테스트할 PDF URL을 입력하세요 (또는 Enter로 샘플 사용):")
    user_input = input("> ").strip()

    test_urls = []
    if user_input:
        test_urls = [user_input]
    else:
        # 실제 크롤링된 PDF URL로 교체 필요
        print("\n⚠️  실제 크롤링된 PDF URL이 필요합니다.")
        print("예시: python3 simple_comparison_test.py")
        print("\n다음 중 하나의 방법으로 테스트하세요:")
        print("1. 직접 URL 입력")
        print("2. 데이터베이스에서 URL 조회 후 하드코딩")
        return

    # 테스트 실행
    all_results = []

    for url in test_urls:
        results = await compare_methods(url, api_key)
        if results:
            all_results.append(results)
        await asyncio.sleep(2)  # API rate limit

    # 결과 요약
    if all_results:
        print_summary(all_results)

    print("\n✅ 테스트 완료!\n")


if __name__ == "__main__":
    asyncio.run(main())
