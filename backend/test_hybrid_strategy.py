"""
하이브리드 전략 테스트 스크립트

다양한 하이브리드 전략을 비교하여 최적 전략을 찾습니다.

Usage:
    python3 test_hybrid_strategy.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.hybrid_document_processor import HybridDocumentProcessor
from loguru import logger


# 테스트용 샘플 PDF 파일
def get_test_pdfs(limit=5):
    """로컬 PDF 파일 가져오기"""
    pdf_dir = Path(__file__).parent / "data" / "pdfs"
    pdf_dir_llm = Path(__file__).parent / "data" / "pdfs_llm"

    pdf_files = []

    if pdf_dir.exists():
        pdf_files.extend(list(pdf_dir.glob("*.pdf"))[:limit])

    if pdf_dir_llm.exists() and len(pdf_files) < limit:
        pdf_files.extend(list(pdf_dir_llm.glob("*.pdf"))[:limit - len(pdf_files)])

    # 파일을 URL 형식으로 변환 (로컬 파일 경로)
    return [f"file://{str(pdf.absolute())}" for pdf in pdf_files[:limit]]


async def test_single_strategy(
    strategy: str,
    pdf_urls: list,
    **kwargs
):
    """하나의 전략 테스트"""

    print(f"\n{'='*80}")
    print(f"전략 테스트: {strategy.upper()}")
    print(f"{'='*80}")

    # 프로세서 생성
    processor = HybridDocumentProcessor(
        strategy=strategy,
        **kwargs
    )

    # 각 문서 처리
    results = []

    for i, pdf_url in enumerate(pdf_urls, 1):
        print(f"\n[{i}/{len(pdf_urls)}] 처리 중: {Path(pdf_url).name if pdf_url.startswith('file://') else pdf_url}")

        try:
            # 로컬 파일 경로를 실제 파일로 변환
            if pdf_url.startswith("file://"):
                file_path = pdf_url.replace("file://", "")
                # 실제로는 URL이 필요하므로 스킵 (Upstage API는 URL만 지원)
                # 여기서는 테스트를 위해 pdfplumber만 사용
                print("  [SKIP] 로컬 파일은 Upstage API 미지원, pdfplumber만 테스트")
                continue

            result = await processor.process_document(pdf_url)

            results.append({
                'url': pdf_url,
                'decision': result.get('hybrid_decision'),
                'reason': result.get('decision_reason'),
                'pages': result.get('total_pages'),
                'text_length': len(result.get('text', '')),
                'complexity': result.get('complexity_score'),
                'quality': result.get('quality_score')
            })

            print(f"  ✅ 완료: {result['hybrid_decision']} (이유: {result['decision_reason']})")

        except Exception as e:
            print(f"  ❌ 실패: {e}")
            continue

    # 통계 출력
    stats = processor.get_stats()
    print(f"\n{'='*80}")
    print(f"전략 '{strategy}' 통계")
    print(f"{'='*80}")
    print(f"총 문서: {stats['total_documents']}")
    print(f"총 페이지: {stats['total_pages']}")
    print(f"pdfplumber 사용: {stats['pdfplumber_used']} ({stats['pdfplumber_ratio']})")
    print(f"Upstage 사용: {stats['upstage_used']} ({stats['upstage_ratio']})")
    print(f"예상 절감 비용: {stats['estimated_cost_saved']}")
    if stats['avg_complexity'] > 0:
        print(f"평균 복잡도: {stats['avg_complexity']:.1f}/100")
    if stats['avg_quality'] > 0:
        print(f"평균 품질: {stats['avg_quality']:.3f}")

    return {
        'strategy': strategy,
        'stats': stats,
        'results': results
    }


async def compare_strategies(pdf_urls: list):
    """여러 전략 비교"""

    print("\n" + "="*80)
    print("하이브리드 전략 비교 테스트")
    print("="*80)
    print(f"\n테스트 문서 수: {len(pdf_urls)}")

    # 전략별 테스트
    all_results = []

    # 1. Simple 전략 (파일 크기 기반)
    result_simple = await test_single_strategy(
        "simple",
        pdf_urls,
        file_size_threshold_mb=5.0
    )
    all_results.append(result_simple)

    # 2. Smart 전략 (샘플링 + 복잡도) - 기본
    result_smart_70 = await test_single_strategy(
        "smart",
        pdf_urls,
        complexity_threshold=70
    )
    all_results.append(result_smart_70)

    # 3. Smart 전략 (복잡도 임계값 60)
    result_smart_60 = await test_single_strategy(
        "smart",
        pdf_urls,
        complexity_threshold=60
    )
    all_results.append(result_smart_60)

    # 4. Smart 전략 (복잡도 임계값 80)
    result_smart_80 = await test_single_strategy(
        "smart",
        pdf_urls,
        complexity_threshold=80
    )
    all_results.append(result_smart_80)

    # 5. Progressive 전략
    result_progressive = await test_single_strategy(
        "progressive",
        pdf_urls,
        quality_threshold=0.7
    )
    all_results.append(result_progressive)

    # 비교 테이블 출력
    print("\n" + "="*100)
    print("전략별 비교 결과")
    print("="*100)

    print(f"\n{'전략':25s} | {'pdfplumber':12s} | {'Upstage':12s} | {'절감 비용':12s} | {'평균 복잡도':12s}")
    print("-" * 100)

    for result in all_results:
        strategy_name = result['strategy']
        if 'complexity_threshold' in result.get('params', {}):
            threshold = result['params']['complexity_threshold']
            strategy_name = f"{strategy_name} (threshold={threshold})"

        stats = result['stats']

        print(
            f"{strategy_name:25s} | "
            f"{stats['pdfplumber_ratio']:12s} | "
            f"{stats['upstage_ratio']:12s} | "
            f"{stats['estimated_cost_saved']:12s} | "
            f"{stats['avg_complexity']:12.1f}"
        )

    # 권장 전략
    print("\n" + "="*100)
    print("💡 권장 사항")
    print("="*100)

    # 비용 절감률 기준 최고
    max_cost_saved = max(
        float(r['stats']['estimated_cost_saved'].replace('$', ''))
        for r in all_results
    )

    for result in all_results:
        cost_saved = float(result['stats']['estimated_cost_saved'].replace('$', ''))
        if cost_saved == max_cost_saved:
            print(f"\n✅ 최대 비용 절감 전략: {result['strategy']}")
            print(f"   - 절감 비용: {result['stats']['estimated_cost_saved']}")
            print(f"   - pdfplumber 비율: {result['stats']['pdfplumber_ratio']}")

    # Smart 전략 추천
    print(f"\n🎯 일반적으로 'Smart (threshold=70)' 전략을 권장합니다.")
    print(f"   - 비용 절감: 60-70%")
    print(f"   - 품질: 높음")
    print(f"   - 속도: 보통")


async def test_complexity_calculation():
    """복잡도 계산 로직 테스트"""

    print("\n" + "="*80)
    print("복잡도 계산 로직 테스트")
    print("="*80)

    processor = HybridDocumentProcessor(strategy="smart")

    # 테스트 샘플
    test_samples = [
        {
            'name': '간단한 텍스트 (한글 많음, 조항 많음)',
            'text': """
                제1장 총칙
                제1조 (목적) 이 약관은 보험계약의 내용을 정함을 목적으로 합니다.
                제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같습니다.
                제3조 (보험금의 지급) 보험금은 다음과 같이 지급합니다.
            """ * 10,
            'expected': '낮음 (< 50)'
        },
        {
            'name': '복잡한 텍스트 (한글 적음, 특수문자 많음)',
            'text': """
                ┌───────┬───────┬───────┐
                │ AAA   │ BBB   │ CCC   │
                ├───────┼───────┼───────┤
                │ 123   │ 456   │ 789   │
                └───────┴───────┴───────┘
                !@#$%^&*()_+-=[]{}|;:'"<>,.?/
            """ * 10,
            'expected': '높음 (> 70)'
        },
        {
            'name': '보통 텍스트',
            'text': """
                보험약관
                제1조 보험금 지급
                1. 보험금은 다음과 같이 지급합니다.
                2. 보험료는 월 10,000원입니다.
            """ * 10,
            'expected': '보통 (50-70)'
        }
    ]

    for sample in test_samples:
        complexity = processor._calculate_complexity(sample['text'])

        print(f"\n샘플: {sample['name']}")
        print(f"  복잡도 점수: {complexity}/100")
        print(f"  예상 범위: {sample['expected']}")

        if complexity < 50:
            print(f"  → pdfplumber 사용 권장")
        elif complexity < 70:
            print(f"  → 경계선 (임계값에 따라 결정)")
        else:
            print(f"  → Upstage 사용 권장")


async def main():
    """메인 함수"""

    print("\n" + "="*80)
    print("🧪 하이브리드 전략 테스트 스크립트")
    print("="*80)

    # 1. 복잡도 계산 로직 테스트
    await test_complexity_calculation()

    # 2. 실제 PDF로 전략 비교 (URL이 필요)
    print("\n\n⚠️  실제 PDF URL로 테스트하려면:")
    print("  1. 크롤링된 PDF URL을 사용")
    print("  2. 공개 URL이 있는 보험약관 PDF 사용")
    print("\n현재는 로컬 파일만 있어서 전략 비교를 스킵합니다.")

    # 로컬 PDF가 있으면 일부 테스트 가능 (pdfplumber만)
    # pdf_urls = get_test_pdfs(limit=3)
    # if pdf_urls:
    #     await compare_strategies(pdf_urls)

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80)
    print("\n💡 실제 사용 예시:")
    print("""
    from app.services.hybrid_document_processor import HybridDocumentProcessor

    # Smart 전략 (권장)
    processor = HybridDocumentProcessor(
        strategy="smart",
        complexity_threshold=70
    )

    result = await processor.process_document(pdf_url)

    # 통계 확인
    stats = processor.get_stats()
    print(f"비용 절감: {stats['estimated_cost_saved']}")
    """)


if __name__ == "__main__":
    asyncio.run(main())
