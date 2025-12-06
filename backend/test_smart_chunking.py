#!/usr/bin/env python3
"""
스마트 청킹 테스트
"""
from app.services.smart_chunking import chunk_document

# 샘플 보험약관 텍스트
sample_text = """
제1조 (목적)
이 약관은 보험계약자와 보험회사 간의 권리와 의무를 규정함을 목적으로 합니다.
보험가입자는 본 약관을 숙지하고 계약을 체결하여야 합니다.

제2조 (보험금의 지급사유)
회사는 피보험자가 보험기간 중 질병으로 인하여 사망한 경우에는 보험수익자에게 보험가입금액 전액을 지급합니다.
단, 다음 각 호의 어느 하나에 해당하는 경우에는 보험금을 지급하지 않습니다.
1. 피보험자가 고의로 자신을 해친 경우
2. 보험수익자가 고의로 피보험자를 해친 경우

제3조 (보험금 지급에 관한 세부규정)
회사는 보험금 지급사유가 발생한 것을 안 날부터 3영업일 이내에 보험금을 지급하기 위하여 보험금 청구서류를 접수하고 심사합니다.
보험금 청구서류는 다음 각 호와 같습니다.
1. 보험금 청구서
2. 사망진단서
3. 주민등록등본

제4조 (보험료의 납입)
계약자는 제1회 보험료를 계약일에, 제2회 이후의 보험료는 계약일의 월단위 해당일에 납입하여야 합니다.
보험료를 납입하지 않으면 계약은 해지될 수 있습니다.
"""

print("=" * 60)
print("🧪 스마트 청킹 테스트")
print("=" * 60)

# 스마트 청킹 실행
chunks = chunk_document(
    text=sample_text,
    document_id="test_doc_001",
    max_chunk_size=400  # 테스트용으로 작게 설정
)

print(f"\n📊 총 {len(chunks)}개 청크 생성됨\n")

for i, chunk in enumerate(chunks, 1):
    print(f"📌 Chunk {i}/{len(chunks)}")
    print(f"  타입: {chunk['chunk_type']}")
    print(f"  크기: {len(chunk['text'])} 글자")
    print(f"  텍스트 미리보기:")
    preview = chunk['text'][:150].replace('\n', ' ')
    print(f"  '{preview}...'")
    print()

print("=" * 60)
print("✅ 테스트 완료")
print("=" * 60)
print("\n💡 주요 특징:")
print("  1. 조항(제N조) 단위로 청킹")
print("  2. 조항이 너무 크면 문장 단위로 분할")
print("  3. 청크간 겹침(overlap)으로 문맥 유지")
print("  4. 각 청크에 메타데이터 포함")
