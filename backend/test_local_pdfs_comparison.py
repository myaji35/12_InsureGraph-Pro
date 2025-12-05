"""
로컬 PDF 파일로 pdfplumber vs Upstage 비교 테스트

실제 시스템에 저장된 보험약관 PDF 5건으로 테스트
의존성: pdfplumber, httpx만 필요

Usage:
    python3 test_local_pdfs_comparison.py
"""
import asyncio
import time
import re
from pathlib import Path
import os


# ============================================================================
# 테스트할 로컬 PDF 파일 (실제 학습된 파일)
# ============================================================================
PDF_DIR = Path(__file__).parent / "data" / "pdfs"
PDF_DIR_LLM = Path(__file__).parent / "data" / "pdfs_llm"


def get_sample_pdfs(limit=5):
    """로컬에서 샘플 PDF 파일 가져오기"""
    pdf_files = []

    # data/pdfs 디렉토리에서 PDF 찾기
    if PDF_DIR.exists():
        pdf_files.extend(list(PDF_DIR.glob("*.pdf")))

    # data/pdfs_llm 디렉토리에서 PDF 찾기
    if PDF_DIR_LLM.exists():
        pdf_files.extend(list(PDF_DIR_LLM.glob("*.pdf")))

    # 파일명에서 정보 추출
    samples = []
    for pdf_path in pdf_files[:limit]:
        filename = pdf_path.name

        # 보험사 추정
        insurer = "Unknown"
        if "애니카" in filename or "anicar" in filename.lower():
            insurer = "삼성화재"
        elif "KB" in filename or "kb" in filename.lower():
            insurer = "KB손해보험"
        elif "삼성" in filename:
            insurer = "삼성생명"

        # 카테고리 추정
        category = "약관"
        if "특약" in filename:
            category = "특약"

        samples.append({
            'file_path': str(pdf_path),
            'filename': filename,
            'insurer': insurer,
            'category': category
        })

    return samples


# ============================================================================
# PDF 텍스트 추출 - pdfplumber
# ============================================================================
def extract_with_pdfplumber(file_path: str):
    """pdfplumber를 사용한 텍스트 추출"""
    try:
        import pdfplumber

        extracted_text = ""
        total_pages = 0

        with pdfplumber.open(file_path) as pdf:
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
# PDF 텍스트 추출 - Upstage
# ============================================================================
async def extract_with_upstage(file_path: str, api_key: str):
    """Upstage Document Parse API를 사용한 텍스트 추출"""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=300.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
            }

            # 파일 업로드
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {
                    "ocr": "force",
                    "output_formats": "text,html"
                }

                response = await client.post(
                    "https://api.upstage.ai/v1/document-ai/document-parse",
                    headers=headers,
                    files=files,
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
        import traceback
        traceback.print_exc()
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
        return {
            'korean_ratio': 0.0,
            'structure_score': 0.0,
            'readability_score': 0.0,
            'overall_score': 0.0
        }

    # 1. 한글 비율
    korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
    korean_ratio = korean_chars / len(text) if text else 0

    # 2. 구조 패턴
    chapters = len(re.findall(r'제\d+장', text))
    articles = len(re.findall(r'제\d+조', text))
    structure_score = min((chapters * 2 + articles) / 100, 1.0)

    # 3. 가독성
    lines = [line for line in text.split('\n') if line.strip()]
    avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / len(text) if text else 0

    readability_score = 0.0
    readability_score += min(avg_line_length / 50, 0.5)
    readability_score += max(0.5 - special_ratio, 0)

    # 4. 종합
    overall = (
        korean_ratio * 0.4 +
        structure_score * 0.3 +
        readability_score * 0.3
    )

    return {
        'korean_ratio': round(korean_ratio, 3),
        'structure_score': round(structure_score, 3),
        'readability_score': round(readability_score, 3),
        'overall_score': round(overall, 3)
    }


def calculate_uds_score(text: str, sections=None, tables=None):
    """UDS (Understanding, Detail, Structure) 점수"""
    quality = calculate_quality_score(text)

    # Understanding
    understanding = quality['overall_score'] * 100

    # Detail
    text_length = len(text)
    detail_from_text = min(text_length / 50000, 1.0) * 60
    detail_from_tables = min(len(tables) if tables else 0, 20) * 2
    detail = detail_from_text + detail_from_tables

    # Structure
    if sections:
        num_chapters = sum(1 for s in sections if s.get('type') == 'chapter')
        num_articles = sum(1 for s in sections if s.get('type') == 'article')
        structure = min((num_chapters * 5 + num_articles * 2), 100)
    else:
        chapters = len(re.findall(r'제\d+장', text))
        articles = len(re.findall(r'제\d+조', text))
        structure = min((chapters * 5 + articles * 2), 100)

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
async def compare_single_pdf(pdf_info: dict, api_key: str):
    """하나의 PDF 파일을 두 방식으로 비교"""
    file_path = pdf_info['file_path']
    filename = pdf_info['filename']

    print(f"\n{'='*100}")
    print(f"📄 파일: {filename}")
    print(f"   보험사: {pdf_info['insurer']}, 카테고리: {pdf_info['category']}")
    print(f"{'='*100}")

    results = {}

    # 1. pdfplumber
    print("\n[1] pdfplumber 테스트 중...")
    start = time.time()
    result_pdf = extract_with_pdfplumber(file_path)
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

        print(f"   ✅ 완료: {time_pdf:.2f}초")
        print(f"   페이지: {result_pdf['total_pages']}, 텍스트: {len(result_pdf['text']):,}자")
        print(f"   품질: {quality_pdf['overall_score']:.3f}, UDS 총점: {uds_pdf['total']:.1f}")
    else:
        results['pdfplumber'] = None

    # 2. Upstage
    print("\n[2] Upstage 테스트 중...")
    start = time.time()
    result_upstage = await extract_with_upstage(file_path, api_key)
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

        print(f"   ✅ 완료: {time_upstage:.2f}초")
        print(f"   페이지: {result_upstage['total_pages']}, 텍스트: {len(result_upstage['text']):,}자")
        print(f"   섹션: {len(result_upstage.get('sections', []))}, 표: {len(result_upstage.get('tables', []))}")
        print(f"   품질: {quality_upstage['overall_score']:.3f}, UDS 총점: {uds_upstage['total']:.1f}")
    else:
        results['upstage'] = None

    return results


def print_summary_table(all_results, pdf_infos):
    """결과 요약 테이블"""
    print("\n" + "="*120)
    print("📊 전체 비교 결과 요약")
    print("="*120)

    # 헤더
    print(f"\n{'파일명':40s} | {'방식':12s} | {'시간':7s} | {'텍스트':10s} | {'품질':6s} | {'UDS':6s} | {'섹션':5s} | {'표':5s}")
    print("-" * 120)

    # 각 파일별 결과
    for i, (results, pdf_info) in enumerate(zip(all_results, pdf_infos)):
        filename_short = pdf_info['filename'][:38] + '..' if len(pdf_info['filename']) > 40 else pdf_info['filename']

        for method_name, method_key in [('pdfplumber', 'pdfplumber'), ('Upstage', 'upstage')]:
            method_data = results.get(method_key)

            if method_data:
                print(
                    f"{filename_short:40s} | "
                    f"{method_name:12s} | "
                    f"{method_data['time']:6.2f}s | "
                    f"{method_data['text_length']:10,d} | "
                    f"{method_data['quality']['overall_score']:6.3f} | "
                    f"{method_data['uds']['total']:6.1f} | "
                    f"{method_data['sections']:5d} | "
                    f"{method_data['tables']:5d}"
                )
            else:
                print(
                    f"{filename_short:40s} | "
                    f"{method_name:12s} | "
                    f"{'FAIL':7s} | {'-':10s} | {'-':6s} | {'-':6s} | {'-':5s} | {'-':5s}"
                )

        print("-" * 120)

    # 평균 계산
    print("\n📈 평균 점수:")

    for method_name, method_key in [('pdfplumber', 'pdfplumber'), ('Upstage', 'upstage')]:
        successful = [r[method_key] for r in all_results if r.get(method_key)]

        if successful:
            avg_time = sum(d['time'] for d in successful) / len(successful)
            avg_quality = sum(d['quality']['overall_score'] for d in successful) / len(successful)
            avg_uds = sum(d['uds']['total'] for d in successful) / len(successful)
            avg_sections = sum(d['sections'] for d in successful) / len(successful)
            avg_tables = sum(d['tables'] for d in successful) / len(successful)

            print(
                f"  {method_name:12s}: "
                f"시간={avg_time:5.2f}s, "
                f"품질={avg_quality:5.3f}, "
                f"UDS={avg_uds:5.1f}, "
                f"섹션={avg_sections:4.1f}, "
                f"표={avg_tables:4.1f}"
            )

    # 개선율
    pdf_successful = [r['pdfplumber'] for r in all_results if r.get('pdfplumber')]
    upstage_successful = [r['upstage'] for r in all_results if r.get('upstage')]

    if pdf_successful and upstage_successful:
        print("\n💡 Upstage vs pdfplumber 개선율:")

        pdf_avg_quality = sum(d['quality']['overall_score'] for d in pdf_successful) / len(pdf_successful)
        upstage_avg_quality = sum(d['quality']['overall_score'] for d in upstage_successful) / len(upstage_successful)

        pdf_avg_uds = sum(d['uds']['total'] for d in pdf_successful) / len(pdf_successful)
        upstage_avg_uds = sum(d['uds']['total'] for d in upstage_successful) / len(upstage_successful)

        quality_improvement = ((upstage_avg_quality - pdf_avg_quality) / pdf_avg_quality * 100) if pdf_avg_quality > 0 else 0
        uds_improvement = ((upstage_avg_uds - pdf_avg_uds) / pdf_avg_uds * 100) if pdf_avg_uds > 0 else 0

        print(f"  품질 점수: {quality_improvement:+.1f}%")
        print(f"  UDS 해석력: {uds_improvement:+.1f}%")

        if quality_improvement > 5 or uds_improvement > 5:
            print(f"\n  ✅ Upstage가 유의미한 개선을 보입니다!")
            print(f"  🎯 보험약관 학습에 Upstage 사용을 권장합니다.")


# ============================================================================
# 메인
# ============================================================================
async def main():
    print("\n" + "="*80)
    print("🔬 보험약관 PDF 추출 방식 비교 테스트 (로컬 파일)")
    print("="*80)
    print("\npdfplumber (현재) vs Upstage Document Parse (신규)")
    print("평가 항목: 시간, 텍스트 품질, UDS 해석력, 섹션 분석, 표 추출\n")

    # API 키 확인
    api_key = os.getenv('UPSTAGE_API_KEY')

    if not api_key:
        print("\n❌ UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("실행 방법:")
        print("  export UPSTAGE_API_KEY='your_api_key'")
        print("  python3 test_local_pdfs_comparison.py")
        return

    # 샘플 PDF 가져오기
    samples = get_sample_pdfs(limit=5)

    if not samples:
        print("\n❌ 테스트할 PDF 파일을 찾을 수 없습니다.")
        print(f"확인 경로:")
        print(f"  - {PDF_DIR}")
        print(f"  - {PDF_DIR_LLM}")
        return

    print(f"\n✅ {len(samples)}개 PDF 파일을 찾았습니다.\n")

    # 각 파일 테스트
    all_results = []

    for i, pdf_info in enumerate(samples, 1):
        print(f"\n\n{'#'*100}")
        print(f"테스트 진행: {i}/{len(samples)}")
        print(f"{'#'*100}")

        results = await compare_single_pdf(pdf_info, api_key)
        all_results.append(results)

        # API rate limit 대기
        if i < len(samples):
            await asyncio.sleep(3)

    # 요약 출력
    print_summary_table(all_results, samples)

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
