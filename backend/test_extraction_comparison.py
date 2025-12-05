"""
기존 학습 데이터와 Upstage 추출 결과 비교 테스트

현재 시스템에 학습된 문서 5건을 선택하여:
1. 기존 추출 방식 (pdfplumber) 결과
2. Upstage Document Parse 결과
를 비교하고 품질, 시간, 해석력을 평가합니다.

Usage:
    python test_extraction_comparison.py
"""
import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.services.upstage_document_parser import UpstageDocumentParser
from app.services.streaming_pdf_processor import StreamingPDFProcessor
from loguru import logger


async def get_sample_documents(limit: int = 5) -> List[Dict[str, Any]]:
    """
    데이터베이스에서 학습된 문서 샘플 가져오기

    Args:
        limit: 가져올 문서 수

    Returns:
        문서 리스트
    """
    logger.info(f"Fetching {limit} sample documents from database...")

    db = next(get_db())

    try:
        # crawler_documents 테이블에서 성공적으로 처리된 문서 조회
        query = """
            SELECT
                id,
                insurer,
                title,
                pdf_url,
                category,
                product_type,
                status,
                metadata,
                created_at
            FROM crawler_documents
            WHERE status IN ('processed', 'completed')
            ORDER BY created_at DESC
            LIMIT %s
        """

        result = db.execute(query, (limit,))
        documents = []

        for row in result.fetchall():
            doc = {
                'id': str(row[0]),
                'insurer': row[1],
                'title': row[2],
                'pdf_url': row[3],
                'category': row[4],
                'product_type': row[5],
                'status': row[6],
                'metadata': row[7] or {},
                'created_at': row[8]
            }
            documents.append(doc)

        logger.info(f"✅ Found {len(documents)} documents")
        return documents

    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        # Fallback: 하드코딩된 샘플 URL 사용
        logger.warning("Using hardcoded sample URLs as fallback")
        return get_fallback_sample_urls()
    finally:
        db.close()


def get_fallback_sample_urls() -> List[Dict[str, Any]]:
    """
    데이터베이스 접근 실패 시 사용할 폴백 샘플 URL
    """
    return [
        {
            'id': 'sample-1',
            'insurer': '삼성화재',
            'title': '(무배당)삼성화재자동차보험 약관',
            'pdf_url': 'https://www.samsungfire.com/static/kr/down/terms/Auto_Insurance_Terms.pdf',
            'category': '약관',
            'product_type': '자동차보험',
            'status': 'processed',
            'metadata': {},
            'created_at': datetime.now()
        },
        {
            'id': 'sample-2',
            'insurer': 'KB손해보험',
            'title': '무배당 KB 5.10.10 건강보험 약관',
            'pdf_url': 'https://www.kbinsure.co.kr/CG302120N.ec',
            'category': '약관',
            'product_type': '건강보험',
            'status': 'processed',
            'metadata': {},
            'created_at': datetime.now()
        }
    ]


def calculate_text_quality_score(text: str) -> Dict[str, float]:
    """
    추출된 텍스트의 품질 점수 계산

    Returns:
        {
            'korean_ratio': 한글 비율,
            'structure_score': 구조화 점수,
            'readability_score': 가독성 점수,
            'overall_score': 종합 점수
        }
    """
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
    chapter_pattern = re.findall(r'제\d+장', text)
    article_pattern = re.findall(r'제\d+조', text)
    structure_score = min((len(chapter_pattern) + len(article_pattern)) / 50, 1.0)

    # 3. 가독성 점수 (평균 줄 길이, 특수문자 비율)
    lines = [line for line in text.split('\n') if line.strip()]
    avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / len(text) if text else 0

    readability_score = 0.0
    readability_score += min(avg_line_length / 50, 0.5)  # 적절한 줄 길이
    readability_score += max(0.5 - special_ratio, 0)  # 특수문자가 적을수록 좋음

    # 4. 종합 점수
    overall_score = (
        korean_ratio * 0.4 +
        structure_score * 0.3 +
        readability_score * 0.3
    )

    return {
        'korean_ratio': round(korean_ratio, 3),
        'structure_score': round(structure_score, 3),
        'readability_score': round(readability_score, 3),
        'overall_score': round(overall_score, 3)
    }


def calculate_uds_interpretation(
    text: str,
    sections: List[Dict] = None,
    tables: List[Dict] = None
) -> Dict[str, Any]:
    """
    UDS (Understanding, Detail, Structure) 해석력 계산

    Returns:
        {
            'understanding': 이해도 점수 (0-100),
            'detail': 상세도 점수 (0-100),
            'structure': 구조화 점수 (0-100),
            'total': 총점 (0-100)
        }
    """
    # 1. Understanding (이해도): 텍스트 품질 기반
    quality = calculate_text_quality_score(text)
    understanding = quality['overall_score'] * 100

    # 2. Detail (상세도): 텍스트 길이 및 표 수 기반
    text_length = len(text)
    detail_from_text = min(text_length / 50000, 1.0) * 60  # 최대 60점
    detail_from_tables = min(len(tables) if tables else 0, 20) * 2  # 최대 40점
    detail = detail_from_text + detail_from_tables

    # 3. Structure (구조화): 섹션 분석 기반
    if sections:
        # 섹션이 있으면 구조화가 잘 된 것
        num_chapters = sum(1 for s in sections if s.get('type') == 'chapter')
        num_articles = sum(1 for s in sections if s.get('type') == 'article')

        structure = min((num_chapters * 5 + num_articles * 2) / 100 * 100, 100)
    else:
        # 섹션이 없으면 패턴으로 추정
        chapter_pattern = len(re.findall(r'제\d+장', text))
        article_pattern = len(re.findall(r'제\d+조', text))

        structure = min((chapter_pattern * 5 + article_pattern * 2) / 100 * 100, 100)

    # 4. Total (총점)
    total = (understanding * 0.3 + detail * 0.3 + structure * 0.4)

    return {
        'understanding': round(understanding, 1),
        'detail': round(detail, 1),
        'structure': round(structure, 1),
        'total': round(total, 1)
    }


async def compare_extraction_methods(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    하나의 문서에 대해 기존 방식과 Upstage 방식을 비교

    Args:
        document: 문서 정보

    Returns:
        비교 결과
    """
    pdf_url = document['pdf_url']

    logger.info(f"\n{'='*80}")
    logger.info(f"📄 Document: {document['title']}")
    logger.info(f"   Insurer: {document['insurer']}")
    logger.info(f"   URL: {pdf_url}")
    logger.info(f"{'='*80}")

    processor = StreamingPDFProcessor()
    comparison = {
        'document': document,
        'pdfplumber': {},
        'upstage': {},
        'upstage_smart': {}
    }

    # ========================================
    # 1. pdfplumber (기존 방식)
    # ========================================
    logger.info("\n[1] Testing pdfplumber (current method)...")
    try:
        start_time = time.time()
        result_pdf = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=False
        )
        elapsed_pdf = time.time() - start_time

        quality_pdf = calculate_text_quality_score(result_pdf['text'])
        uds_pdf = calculate_uds_interpretation(result_pdf['text'])

        comparison['pdfplumber'] = {
            'success': True,
            'elapsed_time': round(elapsed_pdf, 2),
            'total_pages': result_pdf['total_pages'],
            'text_length': len(result_pdf['text']),
            'method': result_pdf['method'],
            'quality': quality_pdf,
            'uds': uds_pdf,
            'sections_count': 0,
            'tables_count': 0
        }

        logger.info(f"✅ pdfplumber completed in {elapsed_pdf:.2f}s")
        logger.info(f"   Pages: {result_pdf['total_pages']}, Text: {len(result_pdf['text']):,} chars")
        logger.info(f"   Quality: {quality_pdf['overall_score']:.3f}, UDS Total: {uds_pdf['total']:.1f}")

    except Exception as e:
        logger.error(f"❌ pdfplumber failed: {e}")
        comparison['pdfplumber'] = {'success': False, 'error': str(e)}

    # ========================================
    # 2. Upstage Document Parse (일반)
    # ========================================
    logger.info("\n[2] Testing Upstage Document Parse...")
    try:
        start_time = time.time()
        result_upstage = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=True,
            extract_tables=True,
            smart_chunking=False
        )
        elapsed_upstage = time.time() - start_time

        quality_upstage = calculate_text_quality_score(result_upstage['text'])
        uds_upstage = calculate_uds_interpretation(
            result_upstage['text'],
            sections=result_upstage.get('sections', []),
            tables=result_upstage.get('tables', [])
        )

        comparison['upstage'] = {
            'success': True,
            'elapsed_time': round(elapsed_upstage, 2),
            'total_pages': result_upstage['total_pages'],
            'text_length': len(result_upstage['text']),
            'method': result_upstage['method'],
            'quality': quality_upstage,
            'quality_score': result_upstage.get('quality_score', 0),
            'uds': uds_upstage,
            'sections_count': len(result_upstage.get('sections', [])),
            'tables_count': len(result_upstage.get('tables', []))
        }

        logger.info(f"✅ Upstage completed in {elapsed_upstage:.2f}s")
        logger.info(f"   Pages: {result_upstage['total_pages']}, Text: {len(result_upstage['text']):,} chars")
        logger.info(f"   Sections: {len(result_upstage.get('sections', []))}, Tables: {len(result_upstage.get('tables', []))}")
        logger.info(f"   Quality: {quality_upstage['overall_score']:.3f}, UDS Total: {uds_upstage['total']:.1f}")

    except Exception as e:
        logger.error(f"❌ Upstage failed: {e}")
        comparison['upstage'] = {'success': False, 'error': str(e)}

    # ========================================
    # 3. Upstage Smart Chunking
    # ========================================
    logger.info("\n[3] Testing Upstage Smart Chunking...")
    try:
        start_time = time.time()
        result_smart = await processor.process_pdf_streaming(
            pdf_url,
            use_upstage=True,
            extract_tables=True,
            smart_chunking=True
        )
        elapsed_smart = time.time() - start_time

        quality_smart = calculate_text_quality_score(result_smart['text'])
        uds_smart = calculate_uds_interpretation(
            result_smart['text'],
            sections=result_smart.get('sections', []),
            tables=result_smart.get('tables', [])
        )

        comparison['upstage_smart'] = {
            'success': True,
            'elapsed_time': round(elapsed_smart, 2),
            'total_pages': result_smart['total_pages'],
            'text_length': len(result_smart['text']),
            'chunks_count': len(result_smart.get('chunks', [])),
            'method': result_smart['method'],
            'quality': quality_smart,
            'quality_score': result_smart.get('quality_score', 0),
            'uds': uds_smart,
            'sections_count': len(result_smart.get('sections', [])),
            'tables_count': len(result_smart.get('tables', []))
        }

        logger.info(f"✅ Upstage Smart Chunking completed in {elapsed_smart:.2f}s")
        logger.info(f"   Pages: {result_smart['total_pages']}, Chunks: {len(result_smart.get('chunks', []))}")
        logger.info(f"   Quality: {quality_smart['overall_score']:.3f}, UDS Total: {uds_smart['total']:.1f}")

    except Exception as e:
        logger.error(f"❌ Upstage Smart Chunking failed: {e}")
        comparison['upstage_smart'] = {'success': False, 'error': str(e)}

    return comparison


def print_summary_table(all_comparisons: List[Dict[str, Any]]):
    """
    전체 비교 결과를 테이블 형식으로 출력
    """
    print("\n" + "="*120)
    print("📊 전체 비교 결과 요약")
    print("="*120)

    # 헤더
    print(f"\n{'문서명':30s} | {'방식':15s} | {'시간(s)':8s} | {'텍스트':10s} | {'품질':6s} | {'UDS':6s} | {'섹션':6s} | {'표':6s}")
    print("-" * 120)

    # 각 문서별 결과
    for comp in all_comparisons:
        doc = comp['document']
        doc_name = doc['title'][:28] + '..' if len(doc['title']) > 30 else doc['title']

        for method_name, method_data in [
            ('pdfplumber', comp['pdfplumber']),
            ('Upstage', comp['upstage']),
            ('Upstage Smart', comp['upstage_smart'])
        ]:
            if method_data.get('success'):
                print(
                    f"{doc_name:30s} | "
                    f"{method_name:15s} | "
                    f"{method_data['elapsed_time']:8.2f} | "
                    f"{method_data['text_length']:10,d} | "
                    f"{method_data['quality']['overall_score']:6.3f} | "
                    f"{method_data['uds']['total']:6.1f} | "
                    f"{method_data['sections_count']:6d} | "
                    f"{method_data['tables_count']:6d}"
                )
            else:
                print(
                    f"{doc_name:30s} | "
                    f"{method_name:15s} | "
                    f"{'FAILED':8s} | "
                    f"{'-':10s} | "
                    f"{'-':6s} | "
                    f"{'-':6s} | "
                    f"{'-':6s} | "
                    f"{'-':6s}"
                )
        print("-" * 120)

    # 평균 계산
    print("\n📈 평균 점수:")

    for method_name, key in [
        ('pdfplumber', 'pdfplumber'),
        ('Upstage', 'upstage'),
        ('Upstage Smart', 'upstage_smart')
    ]:
        successful = [c[key] for c in all_comparisons if c[key].get('success')]
        if successful:
            avg_time = sum(d['elapsed_time'] for d in successful) / len(successful)
            avg_quality = sum(d['quality']['overall_score'] for d in successful) / len(successful)
            avg_uds = sum(d['uds']['total'] for d in successful) / len(successful)
            avg_sections = sum(d['sections_count'] for d in successful) / len(successful)
            avg_tables = sum(d['tables_count'] for d in successful) / len(successful)

            print(
                f"  {method_name:15s}: "
                f"시간={avg_time:6.2f}s, "
                f"품질={avg_quality:6.3f}, "
                f"UDS={avg_uds:6.1f}, "
                f"섹션={avg_sections:6.1f}, "
                f"표={avg_tables:6.1f}"
            )

    # 개선율 계산
    print("\n💡 Upstage vs pdfplumber 개선율:")

    pdf_successful = [c['pdfplumber'] for c in all_comparisons if c['pdfplumber'].get('success')]
    upstage_successful = [c['upstage'] for c in all_comparisons if c['upstage'].get('success')]

    if pdf_successful and upstage_successful:
        pdf_avg_quality = sum(d['quality']['overall_score'] for d in pdf_successful) / len(pdf_successful)
        upstage_avg_quality = sum(d['quality']['overall_score'] for d in upstage_successful) / len(upstage_successful)

        pdf_avg_uds = sum(d['uds']['total'] for d in pdf_successful) / len(pdf_successful)
        upstage_avg_uds = sum(d['uds']['total'] for d in upstage_successful) / len(upstage_successful)

        quality_improvement = ((upstage_avg_quality - pdf_avg_quality) / pdf_avg_quality * 100) if pdf_avg_quality > 0 else 0
        uds_improvement = ((upstage_avg_uds - pdf_avg_uds) / pdf_avg_uds * 100) if pdf_avg_uds > 0 else 0

        print(f"  품질 점수: {quality_improvement:+.1f}%")
        print(f"  UDS 해석력: {uds_improvement:+.1f}%")

        if quality_improvement > 10 or uds_improvement > 10:
            print(f"\n  ✅ Upstage가 pdfplumber 대비 유의미한 개선을 보입니다!")
            print(f"  🎯 보험약관 학습에 Upstage 사용을 권장합니다.")
        else:
            print(f"\n  ⚠️  개선 효과가 미미합니다. 문서 특성을 확인해주세요.")


async def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("🔬 보험약관 추출 방식 비교 테스트")
    print("="*80)
    print("\n기존 방식 (pdfplumber) vs Upstage Document Parse")
    print("평가 항목: 처리 시간, 텍스트 품질, UDS 해석력, 섹션 분석, 표 추출\n")

    # 1. 샘플 문서 가져오기
    documents = await get_sample_documents(limit=5)

    if not documents:
        print("❌ 테스트할 문서를 찾을 수 없습니다.")
        return

    print(f"\n✅ {len(documents)}개 문서로 테스트를 시작합니다.\n")

    # 2. 각 문서별 비교
    all_comparisons = []

    for i, doc in enumerate(documents, 1):
        print(f"\n\n{'#'*80}")
        print(f"테스트 진행: {i}/{len(documents)}")
        print(f"{'#'*80}")

        comparison = await compare_extraction_methods(doc)
        all_comparisons.append(comparison)

        # 잠시 대기 (API rate limit 고려)
        if i < len(documents):
            await asyncio.sleep(2)

    # 3. 요약 테이블 출력
    print_summary_table(all_comparisons)

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
