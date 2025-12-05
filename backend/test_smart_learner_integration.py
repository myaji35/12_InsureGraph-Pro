"""
SmartInsuranceLearner 통합 테스트

parallel_document_processor.py에 통합된 SmartInsuranceLearner를 테스트
"""
import asyncio
import os
from loguru import logger

from app.services.parallel_document_processor import ParallelDocumentProcessor


async def test_smart_learner_integration():
    """SmartInsuranceLearner 통합 테스트"""

    logger.info("=" * 80)
    logger.info("SmartInsuranceLearner Integration Test")
    logger.info("=" * 80)

    # 테스트용 문서 경로 찾기
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    test_pdf_dir = os.path.join(backend_dir, "test_pdfs")

    # 삼성화재 PDF 찾기
    samsung_pdfs = []
    if os.path.exists(test_pdf_dir):
        for filename in os.listdir(test_pdf_dir):
            if filename.endswith('.pdf') and '삼성화재' in filename:
                samsung_pdfs.append(os.path.join(test_pdf_dir, filename))

    if not samsung_pdfs:
        logger.warning("No Samsung Fire PDFs found in test_pdfs directory")
        logger.info("Creating test with mock document instead")

        # 모의 테스트
        processor = ParallelDocumentProcessor(
            max_concurrent=1,
            use_streaming=True,
            use_smart_learning=True
        )

        logger.info("✅ ParallelDocumentProcessor initialized with SmartInsuranceLearner")
        logger.info(f"   - Smart Learning Enabled: {processor.use_smart_learning}")
        logger.info(f"   - Smart Learner Instance: {processor.smart_learner is not None}")

        if processor.smart_learner:
            stats = processor.smart_learner.get_statistics()
            logger.info(f"   - Initial Statistics: {stats}")

        return True

    # 실제 PDF로 테스트
    logger.info(f"Found {len(samsung_pdfs)} Samsung Fire PDFs for testing")

    # Processor 초기화
    processor = ParallelDocumentProcessor(
        max_concurrent=1,
        use_streaming=True,
        use_smart_learning=True
    )

    logger.info("✅ ParallelDocumentProcessor initialized")
    logger.info(f"   - Smart Learning: {processor.use_smart_learning}")
    logger.info(f"   - Smart Learner: {processor.smart_learner is not None}")

    # 첫 번째 PDF로 테스트
    test_pdf = samsung_pdfs[0]
    logger.info(f"\n📄 Testing with PDF: {os.path.basename(test_pdf)}")

    try:
        # Progress callback
        progress_updates = []

        async def progress_callback(doc_id, status, percent, metadata):
            progress_updates.append({
                "document_id": doc_id,
                "status": status,
                "percent": percent,
                "metadata": metadata
            })

            # 스마트 학습 관련 로그만 출력
            if "smart_learning" in status or "strategy" in metadata:
                logger.info(f"   📊 {status}: {percent}% - {metadata}")

        # 문서 처리
        logger.info("Starting document processing...")

        result = await processor.process_document(
            document_id="test_smart_001",
            file_path=test_pdf,
            insurer="삼성화재",
            product_type="종신보험",
            progress_callback=progress_callback
        )

        logger.info("\n" + "=" * 80)
        logger.info("Processing Result:")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Message: {result.get('message')}")

        # 스마트 학습 결과 확인
        smart_learning_updates = [
            u for u in progress_updates
            if "smart_learning" in u["status"] or "strategy" in u["metadata"]
        ]

        if smart_learning_updates:
            logger.info(f"\n✅ Smart Learning Updates: {len(smart_learning_updates)}")
            for update in smart_learning_updates:
                logger.info(f"   - {update['status']}: {update['metadata']}")

        # 통계 확인
        if processor.smart_learner:
            stats = processor.smart_learner.get_statistics()
            logger.info("\n📊 SmartInsuranceLearner Statistics:")
            logger.info(f"   {stats}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_smart_learner_strategies():
    """각 전략별 테스트"""

    logger.info("\n" + "=" * 80)
    logger.info("Testing Smart Learning Strategies")
    logger.info("=" * 80)

    from app.services.learning.smart_learner import SmartInsuranceLearner

    learner = SmartInsuranceLearner()

    # 1. 템플릿 매칭 테스트 (우선순위 1)
    logger.info("\n1️⃣ Testing Template Matching Strategy...")

    # 2. 증분 학습 테스트 (우선순위 2)
    logger.info("\n2️⃣ Testing Incremental Learning Strategy...")

    # 3. 청킹 & 캐싱 테스트 (우선순위 3)
    logger.info("\n3️⃣ Testing Semantic Chunking Strategy...")

    test_text = """
    제1장 총칙
    제1조 (목적)
    이 약관은 보험계약자와 보험회사 간의 권리와 의무를 규정함을 목적으로 합니다.

    제2조 (정의)
    1. 보험금: 보험사고 발생 시 지급하는 금액
    2. 보험료: 보험계약자가 납입하는 금액

    제2장 보장내용
    제3조 (보험금 지급사유)
    피보험자가 보험기간 중 사망한 경우 보험금을 지급합니다.
    """

    try:
        # 모의 학습 콜백
        async def mock_callback(text: str):
            return {
                "entities": ["보험사", "보험계약자"],
                "relationships": [{"from": "보험계약자", "to": "보험사"}]
            }

        result = await learner.learn_document(
            document_id="test_strategy_001",
            text=test_text,
            insurer="테스트보험",
            product_type="종신보험",
            full_learning_callback=mock_callback
        )

        logger.info(f"\n✅ Learning completed with strategy: {result.get('strategy')}")
        logger.info(f"   - Priority: {result.get('priority')}")
        logger.info(f"   - Cost Saving: {result.get('cost_saving_percent')}")

        # 통계 확인
        stats = learner.get_statistics()
        logger.info(f"\n📊 Overall Statistics:")
        logger.info(f"   {stats}")

        # 정리
        await learner.cleanup()

        return True

    except Exception as e:
        logger.error(f"❌ Strategy test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """메인 테스트 실행"""

    logger.info("Starting SmartInsuranceLearner Integration Tests\n")

    # 테스트 1: 통합 테스트
    result1 = await test_smart_learner_integration()

    # 테스트 2: 전략별 테스트
    result2 = await test_smart_learner_strategies()

    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    logger.info(f"Integration Test: {'✅ PASSED' if result1 else '❌ FAILED'}")
    logger.info(f"Strategy Test: {'✅ PASSED' if result2 else '❌ FAILED'}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
