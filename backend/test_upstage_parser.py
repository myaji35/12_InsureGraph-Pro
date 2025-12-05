"""
Upstage Document Parse API 테스트 스크립트

다양한 추출 방법을 비교하여 품질을 평가합니다:
1. pdfplumber (기존 방식)
2. Upstage Document Parse API (신규)

Usage:
    python test_upstage_parser.py <pdf_url>
    python test_upstage_parser.py --file <pdf_path>
"""
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.upstage_document_parser import UpstageDocumentParser
from app.services.streaming_pdf_processor import StreamingPDFProcessor
from loguru import logger


async def compare_extraction_methods(pdf_url: str):
    """
    여러 추출 방법을 비교하여 품질과 성능을 평가

    Args:
        pdf_url: PDF URL 또는 로컬 경로
    """
    print("\n" + "="*80)
    print("📊 PDF 추출 방법 비교 테스트")
    print("="*80)
    print(f"대상 문서: {pdf_url}\n")

    processor = StreamingPDFProcessor()
    results = {}

    # ========================================
    # 방법 1: pdfplumber (기존 방식)
    # ========================================
    print("\n[1] pdfplumber 방식 테스트 중...")
    try:
        start_time = time.time()
        result_pdfplumber = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=False,
            use_remote_api=False
        )
        elapsed_pdfplumber = time.time() - start_time

        results['pdfplumber'] = {
            'result': result_pdfplumber,
            'elapsed_time': elapsed_pdfplumber,
            'success': True
        }

        print(f"✅ pdfplumber 완료")
        print(f"   - 소요 시간: {elapsed_pdfplumber:.2f}초")
        print(f"   - 페이지 수: {result_pdfplumber['total_pages']}")
        print(f"   - 추출 텍스트 길이: {len(result_pdfplumber['text']):,}자")
        print(f"   - 방법: {result_pdfplumber['method']}")

    except Exception as e:
        print(f"❌ pdfplumber 실패: {e}")
        results['pdfplumber'] = {'success': False, 'error': str(e)}

    # ========================================
    # 방법 2: Upstage Document Parse (일반)
    # ========================================
    print("\n[2] Upstage Document Parse 테스트 중...")
    try:
        start_time = time.time()
        result_upstage = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=True,
            extract_tables=True,
            smart_chunking=False
        )
        elapsed_upstage = time.time() - start_time

        results['upstage'] = {
            'result': result_upstage,
            'elapsed_time': elapsed_upstage,
            'success': True
        }

        print(f"✅ Upstage 완료")
        print(f"   - 소요 시간: {elapsed_upstage:.2f}초")
        print(f"   - 페이지 수: {result_upstage['total_pages']}")
        print(f"   - 추출 텍스트 길이: {len(result_upstage['text']):,}자")
        print(f"   - 품질 점수: {result_upstage.get('quality_score', 0):.2f}")
        print(f"   - 섹션 수: {len(result_upstage.get('sections', []))}")
        print(f"   - 표 수: {len(result_upstage.get('tables', []))}")

    except Exception as e:
        print(f"❌ Upstage 실패: {e}")
        results['upstage'] = {'success': False, 'error': str(e)}

    # ========================================
    # 방법 3: Upstage Smart Chunking
    # ========================================
    print("\n[3] Upstage Smart Chunking 테스트 중...")
    try:
        start_time = time.time()
        result_chunking = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=True,
            extract_tables=True,
            smart_chunking=True
        )
        elapsed_chunking = time.time() - start_time

        results['upstage_chunking'] = {
            'result': result_chunking,
            'elapsed_time': elapsed_chunking,
            'success': True
        }

        print(f"✅ Upstage Smart Chunking 완료")
        print(f"   - 소요 시간: {elapsed_chunking:.2f}초")
        print(f"   - 페이지 수: {result_chunking['total_pages']}")
        print(f"   - 청크 수: {len(result_chunking.get('chunks', []))}")
        print(f"   - 품질 점수: {result_chunking.get('quality_score', 0):.2f}")
        print(f"   - 섹션 수: {len(result_chunking.get('sections', []))}")

        # 청크 샘플 출력
        if result_chunking.get('chunks'):
            print(f"\n   📦 청크 샘플 (처음 3개):")
            for i, chunk in enumerate(result_chunking['chunks'][:3]):
                metadata = chunk.get('metadata', {})
                text_preview = chunk['text'][:100].replace('\n', ' ')
                print(f"      [{i+1}] {metadata}")
                print(f"          텍스트: {text_preview}...")

    except Exception as e:
        print(f"❌ Upstage Smart Chunking 실패: {e}")
        results['upstage_chunking'] = {'success': False, 'error': str(e)}

    # ========================================
    # 비교 결과 요약
    # ========================================
    print("\n" + "="*80)
    print("📈 비교 결과 요약")
    print("="*80)

    # 성능 비교
    print("\n⏱️  처리 시간:")
    for method, data in results.items():
        if data.get('success'):
            print(f"  - {method:20s}: {data['elapsed_time']:6.2f}초")

    # 품질 비교
    print("\n📊 추출 품질:")
    for method, data in results.items():
        if data.get('success'):
            result = data['result']
            text_length = len(result.get('text', ''))
            quality_score = result.get('quality_score', 'N/A')
            print(f"  - {method:20s}: {text_length:8,}자, 품질={quality_score}")

    # 기능 비교
    print("\n🔍 추가 기능:")
    for method, data in results.items():
        if data.get('success'):
            result = data['result']
            sections = len(result.get('sections', []))
            tables = len(result.get('tables', []))
            chunks = len(result.get('chunks', []))
            print(f"  - {method:20s}: 섹션={sections}, 표={tables}, 청크={chunks}")

    # 권장 사항
    print("\n💡 권장 사항:")
    if results.get('upstage', {}).get('success'):
        upstage_data = results['upstage']
        pdfplumber_data = results.get('pdfplumber', {})

        if pdfplumber_data.get('success'):
            upstage_text = len(upstage_data['result']['text'])
            pdfplumber_text = len(pdfplumber_data['result']['text'])

            improvement = ((upstage_text - pdfplumber_text) / pdfplumber_text * 100) if pdfplumber_text > 0 else 0

            print(f"  ✅ Upstage가 pdfplumber 대비 {improvement:+.1f}% 더 많은 텍스트 추출")
            print(f"  ✅ 섹션 구조화: {len(upstage_data['result'].get('sections', []))}개 섹션 인식")
            print(f"  ✅ 표 추출: {len(upstage_data['result'].get('tables', []))}개 표 추출")

            if results.get('upstage_chunking', {}).get('success'):
                chunks = len(results['upstage_chunking']['result'].get('chunks', []))
                print(f"  ✅ 스마트 청킹: {chunks}개의 의미 있는 청크로 분할")
                print(f"\n  🎯 보험약관 학습에는 'Upstage Smart Chunking' 방식을 권장합니다!")
            else:
                print(f"\n  🎯 보험약관 학습에는 'Upstage Document Parse' 방식을 권장합니다!")
        else:
            print(f"  ✅ Upstage Document Parse 사용 가능")
    else:
        print(f"  ⚠️  Upstage API 설정을 확인해주세요")

    return results


async def test_with_sample_url():
    """
    샘플 보험약관 URL로 테스트
    """
    # 삼성화재 보험약관 예시 (실제 URL로 교체 필요)
    sample_url = "https://www.samsungfire.com/pdf/sample_insurance_terms.pdf"

    print("\n⚠️  샘플 URL을 실제 보험약관 PDF URL로 교체해주세요")
    print(f"현재 샘플 URL: {sample_url}\n")

    # 실제 테스트는 주석 처리
    # await compare_extraction_methods(sample_url)


async def test_with_file(file_path: str):
    """
    로컬 파일로 테스트
    """
    print(f"\n📁 로컬 파일 테스트: {file_path}")

    # 파일 존재 확인
    if not Path(file_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    # Upstage는 파일도 지원
    parser = UpstageDocumentParser()

    try:
        print("\n[Upstage] 로컬 파일 파싱 중...")
        start_time = time.time()

        result = await parser.parse_document_from_file(
            file_path,
            ocr=True,
            extract_tables=True
        )

        elapsed = time.time() - start_time

        print(f"\n✅ Upstage 파싱 완료!")
        print(f"   - 소요 시간: {elapsed:.2f}초")
        print(f"   - 페이지 수: {result['total_pages']}")
        print(f"   - 추출 텍스트 길이: {len(result['text']):,}자")
        print(f"   - 품질 점수: {result['quality_score']:.2f}")
        print(f"   - 섹션 수: {len(result['sections'])}")
        print(f"   - 표 수: {len(result['tables'])}")

        # 섹션 샘플 출력
        if result['sections']:
            print(f"\n📑 섹션 구조 샘플 (처음 5개):")
            for i, section in enumerate(result['sections'][:5]):
                if section['type'] == 'chapter':
                    print(f"   [{i+1}] 제{section['number']}장: {section['title']}")
                    for article in section.get('articles', [])[:2]:
                        print(f"       - 제{article['number']}조: {article['title']}")
                elif section['type'] == 'article':
                    print(f"   [{i+1}] 제{section['number']}조: {section['title']}")

    except Exception as e:
        print(f"\n❌ 파싱 실패: {e}")
        logger.exception(e)


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Upstage Document Parse API 테스트 스크립트"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="PDF URL (기본값: 샘플 URL 사용)"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="로컬 PDF 파일 경로"
    )

    args = parser.parse_args()

    if args.file:
        # 로컬 파일 테스트
        asyncio.run(test_with_file(args.file))
    elif args.url:
        # URL 테스트
        asyncio.run(compare_extraction_methods(args.url))
    else:
        # 사용 예시 출력
        print("\n" + "="*80)
        print("Upstage Document Parse API 테스트 스크립트")
        print("="*80)
        print("\n사용법:")
        print("  1. URL로 테스트:")
        print("     python test_upstage_parser.py <pdf_url>")
        print("\n  2. 로컬 파일로 테스트:")
        print("     python test_upstage_parser.py --file <pdf_path>")
        print("\n예시:")
        print("  python test_upstage_parser.py https://example.com/insurance.pdf")
        print("  python test_upstage_parser.py --file ./data/sample.pdf")
        print("\n⚠️  .env 파일에 UPSTAGE_API_KEY가 설정되어 있어야 합니다!")
        print("="*80)


if __name__ == "__main__":
    main()
