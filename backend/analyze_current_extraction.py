"""
현재 시스템의 PDF 추출 품질 분석

pdfplumber로 추출된 현재 데이터의 품질을 분석하여
Upstage 도입의 필요성을 평가합니다.

Usage:
    python3 analyze_current_extraction.py
"""
import time
import re
from pathlib import Path


# ============================================================================
# 샘플 PDF 파일 선택
# ============================================================================
PDF_DIR = Path(__file__).parent / "data" / "pdfs"
PDF_DIR_LLM = Path(__file__).parent / "data" / "pdfs_llm"


def get_sample_pdfs(limit=5):
    """로컬에서 샘플 PDF 파일 가져오기"""
    pdf_files = []

    if PDF_DIR.exists():
        pdf_files.extend(list(PDF_DIR.glob("*.pdf")))

    if PDF_DIR_LLM.exists():
        pdf_files.extend(list(PDF_DIR_LLM.glob("*.pdf")))

    samples = []
    for pdf_path in pdf_files[:limit]:
        filename = pdf_path.name

        # 보험사 추정
        insurer = "Unknown"
        if "애니카" in filename:
            insurer = "삼성화재"
        elif "KB" in filename or "kb" in filename.lower():
            insurer = "KB손해보험"
        elif "삼성" in filename:
            insurer = "삼성생명"

        # 상품 유형 추정
        product_type = "Unknown"
        if "자동차" in filename:
            product_type = "자동차보험"
        elif "연금" in filename:
            product_type = "연금보험"
        elif "종신" in filename:
            product_type = "종신보험"

        samples.append({
            'file_path': str(pdf_path),
            'filename': filename,
            'insurer': insurer,
            'product_type': product_type,
            'file_size': pdf_path.stat().st_size
        })

    return samples


# ============================================================================
# PDF 텍스트 추출 - pdfplumber (현재 시스템)
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
        print(f"   ❌ 추출 실패: {e}")
        return None


# ============================================================================
# 품질 분석 함수들
# ============================================================================
def calculate_text_quality(text: str):
    """텍스트 품질 점수 계산"""
    if not text:
        return {
            'korean_ratio': 0.0,
            'structure_score': 0.0,
            'readability_score': 0.0,
            'overall_score': 0.0
        }

    # 1. 한글 비율 (보험약관은 한글이 많아야 함)
    korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
    korean_ratio = korean_chars / len(text) if text else 0

    # 2. 구조화 점수 (제1조, 제1장 등의 패턴 인식)
    chapters = len(re.findall(r'제\d+장', text))
    articles = len(re.findall(r'제\d+조', text))
    structure_score = min((chapters * 2 + articles) / 100, 1.0)

    # 3. 가독성 점수
    lines = [line for line in text.split('\n') if line.strip()]
    avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / len(text) if text else 0

    readability_score = 0.0
    readability_score += min(avg_line_length / 50, 0.5)
    readability_score += max(0.5 - special_ratio, 0)

    # 4. 종합 점수
    overall = (
        korean_ratio * 0.4 +
        structure_score * 0.3 +
        readability_score * 0.3
    )

    return {
        'korean_ratio': round(korean_ratio, 3),
        'structure_score': round(structure_score, 3),
        'readability_score': round(readability_score, 3),
        'overall_score': round(overall, 3),
        'chapters': chapters,
        'articles': articles
    }


def calculate_uds_interpretation(text: str):
    """UDS (Understanding, Detail, Structure) 해석력 계산"""
    quality = calculate_text_quality(text)

    # Understanding (이해도): 텍스트 품질 기반
    understanding = quality['overall_score'] * 100

    # Detail (상세도): 텍스트 길이 기반
    text_length = len(text)
    detail = min(text_length / 50000, 1.0) * 100

    # Structure (구조화): 조항 수 기반
    chapters = quality['chapters']
    articles = quality['articles']
    structure = min((chapters * 5 + articles * 2), 100)

    # Total
    total = (understanding * 0.3 + detail * 0.3 + structure * 0.4)

    return {
        'understanding': round(understanding, 1),
        'detail': round(detail, 1),
        'structure': round(structure, 1),
        'total': round(total, 1)
    }


def analyze_potential_issues(text: str):
    """잠재적 문제점 분석"""
    issues = []

    # 1. 텍스트가 너무 짧은 경우
    if len(text) < 1000:
        issues.append("⚠️  추출된 텍스트가 매우 짧습니다 (OCR 필요 가능성)")

    # 2. 한글 비율이 낮은 경우
    korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
    korean_ratio = korean_chars / len(text) if text else 0
    if korean_ratio < 0.3:
        issues.append(f"⚠️  한글 비율이 낮습니다 ({korean_ratio:.1%}) - OCR 품질 문제 가능")

    # 3. 조항 구조가 없는 경우
    articles = len(re.findall(r'제\d+조', text))
    if articles < 5:
        issues.append(f"⚠️  조항 구조 인식 실패 (제N조 패턴: {articles}개만 발견)")

    # 4. 특수문자가 너무 많은 경우
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / len(text) if text else 0
    if special_ratio > 0.3:
        issues.append(f"⚠️  특수문자 비율이 높습니다 ({special_ratio:.1%}) - 레이아웃 깨짐 가능")

    # 5. 표 추출 부재
    table_indicators = ['┌', '┐', '└', '┘', '│', '─']
    has_table_chars = any(char in text for char in table_indicators)
    if not has_table_chars:
        # 표가 있을 법한데 추출 안 됨
        if '보험료' in text or '보상' in text:
            issues.append("⚠️  표 구조 추출 실패 가능 (텍스트만 추출됨)")

    return issues


# ============================================================================
# 분석 실행
# ============================================================================
def analyze_single_pdf(pdf_info: dict):
    """하나의 PDF 파일 분석"""
    file_path = pdf_info['file_path']
    filename = pdf_info['filename']

    print(f"\n{'='*100}")
    print(f"📄 파일: {filename}")
    print(f"   보험사: {pdf_info['insurer']}, 상품: {pdf_info['product_type']}")
    print(f"   파일 크기: {pdf_info['file_size'] / 1024 / 1024:.2f} MB")
    print(f"{'='*100}")

    # 추출
    print("\n🔍 pdfplumber로 텍스트 추출 중...")
    start = time.time()
    result = extract_with_pdfplumber(file_path)
    elapsed = time.time() - start

    if not result:
        return None

    text = result['text']
    total_pages = result['total_pages']

    print(f"✅ 추출 완료: {elapsed:.2f}초")
    print(f"   페이지 수: {total_pages}")
    print(f"   텍스트 길이: {len(text):,}자")

    # 품질 분석
    print("\n📊 품질 분석:")
    quality = calculate_text_quality(text)

    print(f"   한글 비율: {quality['korean_ratio']:.1%}")
    print(f"   구조화 점수: {quality['structure_score']:.3f}")
    print(f"   가독성 점수: {quality['readability_score']:.3f}")
    print(f"   ⭐ 종합 품질: {quality['overall_score']:.3f}")
    print(f"\n   발견된 구조:")
    print(f"   - 제N장: {quality['chapters']}개")
    print(f"   - 제N조: {quality['articles']}개")

    # UDS 해석력
    print("\n🎯 UDS 해석력:")
    uds = calculate_uds_interpretation(text)

    print(f"   이해도 (U): {uds['understanding']:.1f}/100")
    print(f"   상세도 (D): {uds['detail']:.1f}/100")
    print(f"   구조화 (S): {uds['structure']:.1f}/100")
    print(f"   ⭐ UDS 총점: {uds['total']:.1f}/100")

    # 문제점 분석
    print("\n⚠️  잠재적 문제점:")
    issues = analyze_potential_issues(text)

    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"   ✅ 특별한 문제점이 발견되지 않았습니다.")

    # Upstage 권장 여부
    print("\n💡 Upstage 도입 권장도:")
    recommendation_score = 0

    if quality['overall_score'] < 0.7:
        recommendation_score += 30
        print(f"   [+30점] 품질 점수가 낮습니다 ({quality['overall_score']:.3f})")

    if quality['articles'] < 10:
        recommendation_score += 25
        print(f"   [+25점] 조항 구조 인식이 부족합니다 ({quality['articles']}개)")

    if len(issues) >= 2:
        recommendation_score += 25
        print(f"   [+25점] 다수의 문제점이 발견되었습니다 ({len(issues)}개)")

    if uds['structure'] < 50:
        recommendation_score += 20
        print(f"   [+20점] 구조화 점수가 낮습니다 ({uds['structure']:.1f})")

    if recommendation_score == 0:
        print(f"   ✅ 현재 추출 품질이 양호합니다.")
    else:
        print(f"\n   ⭐ Upstage 권장 점수: {recommendation_score}/100")
        if recommendation_score >= 50:
            print(f"   🎯 Upstage Document Parse 도입을 강력히 권장합니다!")
        elif recommendation_score >= 30:
            print(f"   💡 Upstage Document Parse 도입을 고려해볼 만합니다.")
        else:
            print(f"   ℹ️  Upstage는 선택사항입니다.")

    return {
        'filename': filename,
        'pages': total_pages,
        'text_length': len(text),
        'elapsed_time': round(elapsed, 2),
        'quality': quality,
        'uds': uds,
        'issues_count': len(issues),
        'recommendation_score': recommendation_score
    }


def print_summary(all_results):
    """전체 결과 요약"""
    print("\n" + "="*100)
    print("📊 전체 분석 결과 요약")
    print("="*100)

    # 테이블 헤더
    print(f"\n{'파일명':45s} | {'페이지':6s} | {'텍스트':10s} | {'품질':6s} | {'UDS':6s} | {'문제':4s} | {'권장':4s}")
    print("-" * 100)

    # 각 파일 결과
    for r in all_results:
        if r:
            filename_short = r['filename'][:43] + '..' if len(r['filename']) > 45 else r['filename']
            print(
                f"{filename_short:45s} | "
                f"{r['pages']:6d} | "
                f"{r['text_length']:10,d} | "
                f"{r['quality']['overall_score']:6.3f} | "
                f"{r['uds']['total']:6.1f} | "
                f"{r['issues_count']:4d} | "
                f"{r['recommendation_score']:4d}"
            )

    # 평균
    print("-" * 100)
    valid_results = [r for r in all_results if r]

    if valid_results:
        avg_quality = sum(r['quality']['overall_score'] for r in valid_results) / len(valid_results)
        avg_uds = sum(r['uds']['total'] for r in valid_results) / len(valid_results)
        avg_recommendation = sum(r['recommendation_score'] for r in valid_results) / len(valid_results)

        print(f"{'평균':45s} | {'':6s} | {'':10s} | {avg_quality:6.3f} | {avg_uds:6.1f} | {'':4s} | {avg_recommendation:4.0f}")

    print("\n" + "="*100)
    print("💡 Upstage Document Parse 도입 필요성 평가")
    print("="*100)

    if valid_results:
        avg_recommendation = sum(r['recommendation_score'] for r in valid_results) / len(valid_results)

        print(f"\n평균 권장 점수: {avg_recommendation:.0f}/100")

        if avg_recommendation >= 50:
            print("\n🎯 결론: Upstage Document Parse 도입을 **강력히 권장**합니다!")
            print("\n기대 효과:")
            print("  ✅ 한국어 텍스트 추출 품질 10-30% 향상")
            print("  ✅ 보험약관 구조(제N장, 제N조) 자동 인식")
            print("  ✅ 표 자동 추출 및 구조화")
            print("  ✅ OCR 품질 개선 (이미지 기반 PDF)")
            print("  ✅ 스마트 청킹으로 학습 효율 향상")

        elif avg_recommendation >= 30:
            print("\n💡 결론: Upstage Document Parse 도입을 **고려**해볼 만합니다.")
            print("\n기대 효과:")
            print("  ✅ 일부 문서의 추출 품질 개선")
            print("  ✅ 구조화 점수 향상")

        else:
            print("\nℹ️  결론: 현재 pdfplumber 추출 품질이 양호합니다.")
            print("   Upstage는 선택사항이며, 필요 시 특정 문서에만 적용 가능합니다.")


# ============================================================================
# 메인
# ============================================================================
def main():
    print("\n" + "="*80)
    print("🔬 현재 시스템의 PDF 추출 품질 분석")
    print("="*80)
    print("\npdfplumber 기반 현재 추출 품질을 분석하여")
    print("Upstage Document Parse 도입의 필요성을 평가합니다.\n")

    # 샘플 PDF 가져오기
    samples = get_sample_pdfs(limit=5)

    if not samples:
        print("\n❌ 분석할 PDF 파일을 찾을 수 없습니다.")
        print(f"확인 경로:")
        print(f"  - {PDF_DIR}")
        print(f"  - {PDF_DIR_LLM}")
        return

    print(f"✅ {len(samples)}개 PDF 파일을 찾았습니다.\n")

    # 각 파일 분석
    all_results = []

    for i, pdf_info in enumerate(samples, 1):
        print(f"\n\n{'#'*100}")
        print(f"분석 진행: {i}/{len(samples)}")
        print(f"{'#'*100}")

        result = analyze_single_pdf(pdf_info)
        all_results.append(result)

    # 요약 출력
    print_summary(all_results)

    print("\n" + "="*80)
    print("✅ 분석 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
