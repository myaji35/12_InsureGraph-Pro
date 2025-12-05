"""
병렬 문서 처리 최적화 스크립트

SmartInsuranceLearner를 활용한 대량 문서 병렬 학습
- 여러 문서를 동시에 처리하여 처리 시간 단축
- 전략별 통계 수집 및 분석
"""
import asyncio
from typing import List, Dict
from loguru import logger
from sqlalchemy import select
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.models.crawler_document import CrawlerDocument
from app.services.learning.smart_learner import SmartInsuranceLearner


class ParallelLearningOptimizer:
    """병렬 학습 최적화 실행기"""

    def __init__(self, max_concurrent: int = 3):
        """
        Args:
            max_concurrent: 동시 처리할 최대 문서 수
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.smart_learner = SmartInsuranceLearner()

        # 통계
        self.stats = {
            "total_documents": 0,
            "successful": 0,
            "failed": 0,
            "strategies_used": {
                "template": 0,
                "incremental": 0,
                "chunking": 0,
                "full": 0
            },
            "total_cost_saving": 0.0,
            "start_time": None,
            "end_time": None
        }

    async def get_pending_documents(self, limit: int = 100) -> List[CrawlerDocument]:
        """학습 대기 중인 문서 조회"""
        async with AsyncSessionLocal() as session:
            # text_extracted 상태이지만 graph_stored가 아닌 문서들
            result = await session.execute(
                select(CrawlerDocument)
                .where(
                    CrawlerDocument.processing_step == 'text_extracted',
                    CrawlerDocument.extracted_text.isnot(None),
                    CrawlerDocument.insurer.isnot(None)
                )
                .limit(limit)
            )
            documents = result.scalars().all()

        logger.info(f"Found {len(documents)} pending documents for learning")
        return documents

    async def process_single_document(
        self,
        document: CrawlerDocument
    ) -> Dict:
        """단일 문서 학습"""

        async with self.semaphore:
            doc_id = str(document.id)
            logger.info(f"[{doc_id[:8]}] Processing document: {document.url}")

            try:
                # 모의 학습 콜백 (실제로는 RelationExtractor 등 사용)
                async def mock_learning_callback(text_chunk: str) -> Dict:
                    # TODO: 실제 엔티티/관계 추출 로직
                    await asyncio.sleep(0.1)  # 시뮬레이션
                    return {
                        "entities": [],
                        "relationships": [],
                        "chunk_length": len(text_chunk)
                    }

                # 스마트 학습 실행
                result = await self.smart_learner.learn_document(
                    document_id=doc_id,
                    text=document.extracted_text,
                    insurer=document.insurer or "Unknown",
                    product_type=document.product_type or "일반",
                    full_learning_callback=mock_learning_callback
                )

                # 통계 업데이트
                strategy = result.get("strategy", "unknown")
                if strategy in self.stats["strategies_used"]:
                    self.stats["strategies_used"][strategy] += 1

                cost_saving = result.get("cost_saving", 0)
                self.stats["total_cost_saving"] += cost_saving

                logger.info(
                    f"[{doc_id[:8]}] ✅ Success - Strategy: {strategy}, "
                    f"Cost saving: {result.get('cost_saving_percent', '0%')}"
                )

                return {
                    "document_id": doc_id,
                    "status": "success",
                    "strategy": strategy,
                    "cost_saving": cost_saving,
                    "url": document.url
                }

            except Exception as e:
                logger.error(f"[{doc_id[:8]}] ❌ Failed: {e}")
                return {
                    "document_id": doc_id,
                    "status": "failed",
                    "error": str(e),
                    "url": document.url
                }

    async def process_documents_in_parallel(
        self,
        documents: List[CrawlerDocument]
    ) -> List[Dict]:
        """문서들을 병렬로 처리"""

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Starting parallel processing of {len(documents)} documents")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"{'=' * 80}\n")

        self.stats["total_documents"] = len(documents)
        self.stats["start_time"] = datetime.now()

        # 병렬 처리
        tasks = [
            self.process_single_document(doc)
            for doc in documents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        self.stats["end_time"] = datetime.now()

        # 통계 계산
        for result in results:
            if isinstance(result, Exception):
                self.stats["failed"] += 1
            elif result.get("status") == "success":
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1

        return results

    def print_summary(self, results: List[Dict]):
        """처리 결과 요약 출력"""

        logger.info("\n" + "=" * 80)
        logger.info("Parallel Learning Summary")
        logger.info("=" * 80)

        # 시간 통계
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            logger.info(f"\n[Processing Time]")
            logger.info(f"  Start: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  End: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            logger.info(f"  Average per document: {duration/self.stats['total_documents']:.1f} seconds")

        # 처리 통계
        logger.info(f"\n[Processing Statistics]")
        logger.info(f"  Total documents: {self.stats['total_documents']}")
        logger.info(f"  Successful: {self.stats['successful']}")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  Success rate: {self.stats['successful']/self.stats['total_documents']:.1%}")

        # 전략별 통계
        logger.info(f"\n[Strategy Distribution]")
        for strategy, count in self.stats["strategies_used"].items():
            percentage = (count / self.stats['successful'] * 100) if self.stats['successful'] > 0 else 0
            logger.info(f"  {strategy.capitalize()}: {count} ({percentage:.1f}%)")

        # 비용 절감
        avg_cost_saving = (
            self.stats['total_cost_saving'] / self.stats['successful']
            if self.stats['successful'] > 0 else 0
        )
        logger.info(f"\n[Cost Savings]")
        logger.info(f"  Total cost saving: {self.stats['total_cost_saving']:.2f}")
        logger.info(f"  Average per document: {avg_cost_saving:.1%}")

        # 실패한 문서들
        failed_docs = [r for r in results if r.get("status") == "failed"]
        if failed_docs:
            logger.info(f"\n[Failed Documents] ({len(failed_docs)})")
            for i, doc in enumerate(failed_docs[:10], 1):  # 최대 10개만 표시
                logger.info(f"  {i}. {doc.get('url', 'unknown')} - {doc.get('error', 'unknown')}")
            if len(failed_docs) > 10:
                logger.info(f"  ... and {len(failed_docs) - 10} more")

        # SmartInsuranceLearner 전체 통계
        learner_stats = self.smart_learner.get_statistics()
        logger.info(f"\n[SmartInsuranceLearner Overall Statistics]")
        logger.info(f"  {learner_stats}")

        logger.info("\n" + "=" * 80)

    async def optimize(self, limit: int = 100) -> Dict:
        """병렬 학습 최적화 실행"""

        logger.info("Starting Parallel Learning Optimization")

        # 대기 문서 조회
        documents = await self.get_pending_documents(limit)

        if not documents:
            logger.warning("No pending documents found")
            return {
                "status": "no_documents",
                "message": "No documents to process"
            }

        # 병렬 처리
        results = await self.process_documents_in_parallel(documents)

        # 요약 출력
        self.print_summary(results)

        # 정리
        await self.smart_learner.cleanup()

        return {
            "status": "completed",
            "total_documents": self.stats["total_documents"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "strategies_used": self.stats["strategies_used"],
            "total_cost_saving": self.stats["total_cost_saving"],
            "duration_seconds": (
                (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
                if self.stats["start_time"] and self.stats["end_time"] else 0
            )
        }


async def main():
    """메인 실행"""

    import argparse

    parser = argparse.ArgumentParser(description="병렬 문서 학습 최적화")
    parser.add_argument("--limit", type=int, default=100, help="처리할 최대 문서 수")
    parser.add_argument("--concurrent", type=int, default=3, help="동시 처리 문서 수")

    args = parser.parse_args()

    optimizer = ParallelLearningOptimizer(max_concurrent=args.concurrent)

    try:
        result = await optimizer.optimize(limit=args.limit)
        logger.info(f"\n✅ Optimization completed: {result}")

    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
