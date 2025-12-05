"""
자동 문서 학습 워커

새로 크롤링된 문서(pending 상태)를 감지하여 자동으로 그래프 학습을 시작합니다.
- 5개씩 배치로 처리
- 처리 중인 문서가 없을 때만 새 배치 시작
- 30초마다 체크
"""
import asyncio
import signal
import sys
from datetime import datetime
from loguru import logger

from app.services.parallel_document_processor import ParallelDocumentProcessor
from app.core.database import AsyncSessionLocal
from sqlalchemy import text


class AutoLearningWorker:
    """자동 학습 워커"""

    def __init__(
        self,
        max_concurrent: int = 5,
        batch_size: int = 10,
        check_interval: int = 30
    ):
        """
        Args:
            max_concurrent: 동시 처리할 문서 수
            batch_size: 한 번에 처리할 배치 크기
            check_interval: 체크 간격 (초)
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.check_interval = check_interval
        self.processor = ParallelDocumentProcessor(max_concurrent=max_concurrent)
        self.is_running = True
        self.total_processed = 0

        # Graceful shutdown 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """종료 시그널 처리"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.is_running = False

    async def get_processing_count(self) -> int:
        """현재 처리 중인 문서 수 조회"""
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT COUNT(*) as count
                FROM crawler_documents
                WHERE status = 'processing'
            """)
            result = await db.execute(query)
            row = result.fetchone()
            return row[0] if row else 0

    async def get_pending_count(self) -> int:
        """대기 중인 문서 수 조회"""
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT COUNT(*) as count
                FROM crawler_documents
                WHERE status = 'pending'
            """)
            result = await db.execute(query)
            row = result.fetchone()
            return row[0] if row else 0

    async def run(self):
        """워커 실행"""
        logger.info("=" * 80)
        logger.info("🚀 Auto Learning Worker Started")
        logger.info(f"  - Max Concurrent: {self.max_concurrent}")
        logger.info(f"  - Batch Size: {self.batch_size}")
        logger.info(f"  - Check Interval: {self.check_interval}s")
        logger.info("=" * 80)

        while self.is_running:
            try:
                # 현재 처리 중인 문서 수 확인
                processing_count = await self.get_processing_count()
                pending_count = await self.get_pending_count()

                logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"Processing: {processing_count}, Pending: {pending_count}, "
                          f"Total Processed: {self.total_processed}")

                # 처리 중인 문서가 없고, 대기 중인 문서가 있으면 새 배치 시작
                if processing_count == 0 and pending_count > 0:
                    logger.info(f"🎯 Starting new batch: {self.batch_size} documents")

                    result = await self.processor.process_pending_documents(
                        limit=self.batch_size
                    )

                    self.total_processed += result["success"]

                    logger.info(f"✅ Batch completed: {result['success']} success, "
                              f"{result['failed']} failed out of {result['total']} total")
                    logger.info(f"📊 Total processed so far: {self.total_processed}")

                elif processing_count > 0:
                    logger.info(f"⏳ Waiting for current batch to complete ({processing_count} documents processing)...")

                else:
                    logger.info("💤 No pending documents. Waiting for new documents...")

                # 다음 체크까지 대기
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Worker error: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

        logger.info("=" * 80)
        logger.info(f"🛑 Auto Learning Worker Stopped. Total processed: {self.total_processed}")
        logger.info("=" * 80)


async def main():
    """메인 함수"""
    # 커맨드 라인 인자 파싱
    max_concurrent = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    check_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    worker = AutoLearningWorker(
        max_concurrent=max_concurrent,
        batch_size=batch_size,
        check_interval=check_interval
    )

    await worker.run()


if __name__ == "__main__":
    # 사용 예:
    # python worker_auto_learner.py 5 10 30
    # (5개 동시, 10개 배치, 30초 간격)
    asyncio.run(main())
