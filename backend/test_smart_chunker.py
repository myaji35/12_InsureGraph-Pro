"""
Smart Insurance Chunker 테스트 스크립트
"""
from app.services.smart_insurance_chunker import SmartInsuranceChunker
from pathlib import Path
import json


def test_chunker():
    """청킹 테스트"""

    # 샘플 PDF 경로 확인
    sample_pdfs = list(Path("data").glob("*.pdf")) if Path("data").exists() else []

    if not sample_pdfs:
        print("⚠️  샘플 PDF 파일이 없습니다.")
        print("   data/ 디렉토리에 보험 약관 PDF를 추가해주세요.")
        return

    print(f"📁 발견된 PDF: {len(sample_pdfs)}개")

    # 첫 번째 PDF로 테스트
    pdf_path = sample_pdfs[0]
    print(f"\n📄 테스트 대상: {pdf_path.name}")

    # Chunker 초기화
    chunker = SmartInsuranceChunker(
        max_chars=1500,
        target_chars=1200,
        min_chars=200
    )

    # 청킹 실행
    output_dir = "test_chunks"
    chunks = chunker.parse_and_chunk(
        pdf_path=str(pdf_path),
        output_dir=output_dir
    )

    print(f"\n✅ 청킹 완료!")
    print(f"   총 {len(chunks)}개 청크 생성")

    # 통계 로드
    stats_file = Path(output_dir) / "chunks_stats.json"
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

        print(f"\n📊 통계:")
        print(f"   - 전체 청크: {stats['total_chunks']}개")
        print(f"   - 표 청크: {stats['table_chunks']}개")
        print(f"   - 텍스트 청크: {stats['text_chunks']}개")
        print(f"   - 평균 크기: {stats['avg_length']:.0f} chars")
        print(f"   - 최소 크기: {stats['min_length']} chars")
        print(f"   - 최대 크기: {stats['max_length']} chars")

    # 샘플 청크 출력
    print(f"\n📝 샘플 청크 (처음 3개):")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n{'='*80}")
        print(f"Chunk {i}:")
        print(f"  Pages: {chunk['metadata']['page_start']}-{chunk['metadata']['page_end']}")
        print(f"  Type: {', '.join(set(chunk['metadata']['types']))}")
        print(f"  Length: {chunk['metadata']['length']} chars")
        print(f"  Is Table: {chunk['metadata']['is_table']}")
        print(f"  Preview:")
        print(f"  {chunk['text'][:200]}...")

    print(f"\n💾 출력 디렉토리: {output_dir}/")


def test_with_sample_text():
    """샘플 텍스트로 구조 인식 테스트"""

    sample_text = """
제1장 보험금의 지급

제1조 (보험금의 지급사유)
회사는 피보험자가 보험기간 중 다음 각 호의 어느 하나에 해당하는 경우 보험금을 지급합니다.

1. 암으로 진단확정된 경우
2. 뇌출혈로 진단확정된 경우
3. 급성심근경색증으로 진단확정된 경우

제2조 (보험금의 지급제한)
회사는 다음 각 호의 경우 보험금을 지급하지 않습니다.

가. 피보험자의 고의
나. 전쟁, 외국의 무력행사, 혁명, 내란, 사변, 폭동
"""

    chunker = SmartInsuranceChunker()

    # 구조 분석 테스트
    elements = chunker._parse_text_structure(sample_text, page_num=1)

    print(f"\n📄 구조 분석 테스트:")
    print(f"   추출된 요소: {len(elements)}개\n")

    for elem in elements:
        print(f"   - [{elem['type']}] {elem['content'][:50]}...")


if __name__ == "__main__":
    print("🧪 Smart Insurance Chunker 테스트\n")

    # 구조 인식 테스트
    test_with_sample_text()

    # 실제 PDF 테스트
    print("\n" + "="*80 + "\n")
    test_chunker()
