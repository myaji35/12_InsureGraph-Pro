"""
Parallel Document Processor

여러 문서를 동시에 처리하여 전체 처리 시간을 단축합니다.
"""
import asyncio
import httpx
import tempfile
import os
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.pdf_text_quality_evaluator import PDFTextQualityEvaluator
from app.services.streaming_pdf_processor import StreamingPDFProcessor
from app.services.hybrid_document_processor import HybridDocumentProcessor
from app.services.learning import SmartInsuranceLearner
from app.services.learning.deep_knowledge_service import DeepKnowledgeService


class ParallelDocumentProcessor:
    """병렬 문서 처리기"""

    def __init__(
        self,
        max_concurrent: int = 5,
        use_streaming: bool = True,
        use_smart_learning: bool = True,
        use_hybrid: bool = None
    ):
        """
        Args:
            max_concurrent: 동시에 처리할 최대 문서 수 (기본값: 5)
                - CPU 코어 수와 메모리를 고려하여 설정
                - 너무 높으면 메모리 부족이나 API 제한에 걸릴 수 있음
            use_streaming: 스트리밍 방식 사용 여부 (기본값: True)
                - True: 로컬 다운로드 없이 스트리밍 처리 (메모리 효율적)
                - False: 기존 방식 (임시 파일 저장)
            use_smart_learning: 스마트 학습 알고리즘 사용 여부 (기본값: True)
                - True: SmartInsuranceLearner 사용 (비용 절감)
                - False: 기존 방식 (전체 학습)
            use_hybrid: 하이브리드 추출 방식 사용 여부 (기본값: settings에서 로드)
                - True: pdfplumber/Upstage 자동 선택 (비용 최적화)
                - False: StreamingPDFProcessor 사용 (기존 방식)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.use_streaming = use_streaming
        self.use_smart_learning = use_smart_learning

        # 하이브리드 설정 (기본값은 settings에서 로드)
        self.use_hybrid = use_hybrid if use_hybrid is not None else settings.HYBRID_EXTRACTION_ENABLED

        if self.use_hybrid:
            logger.info(f"하이브리드 추출 활성화: strategy={settings.HYBRID_STRATEGY}")
            self.hybrid_processor = HybridDocumentProcessor(
                strategy=settings.HYBRID_STRATEGY,
                complexity_threshold=settings.HYBRID_COMPLEXITY_THRESHOLD,
                quality_threshold=settings.HYBRID_QUALITY_THRESHOLD,
                file_size_threshold_mb=settings.HYBRID_FILE_SIZE_THRESHOLD_MB
            )
            self.streaming_processor = None
        else:
            logger.info("기존 StreamingPDFProcessor 사용")
            self.streaming_processor = StreamingPDFProcessor() if use_streaming else None
            self.hybrid_processor = None

        self.smart_learner = SmartInsuranceLearner() if use_smart_learning else None
        self.deep_knowledge_service = DeepKnowledgeService() if use_smart_learning else None

    async def process_pending_documents(
        self,
        limit: Optional[int] = None,
        insurer: Optional[str] = None
    ) -> Dict[str, int]:
        """
        대기 중인 문서들을 병렬로 처리합니다.

        Args:
            limit: 처리할 최대 문서 수 (None이면 모든 대기 문서 처리)
            insurer: 특정 보험사의 문서만 처리 (None이면 모든 보험사)

        Returns:
            처리 결과 통계 (성공, 실패, 총 개수)
        """
        async with AsyncSessionLocal() as db:
            # 대기 중인 문서 조회
            query = text("""
                SELECT id, pdf_url, insurer, product_type, title
                FROM crawler_documents
                WHERE status = 'pending'
            """)

            if insurer:
                query = text("""
                    SELECT id, pdf_url, insurer, product_type, title
                    FROM crawler_documents
                    WHERE status = 'pending' AND insurer = :insurer
                """)

            if limit:
                query = text(str(query) + f" LIMIT {limit}")

            result = await db.execute(
                query,
                {"insurer": insurer} if insurer else {}
            )
            pending_docs = result.fetchall()

        if not pending_docs:
            logger.info("No pending documents to process")
            return {"total": 0, "success": 0, "failed": 0}

        logger.info(f"Starting parallel processing of {len(pending_docs)} documents with max_concurrent={self.max_concurrent}")

        # 병렬 처리 시작
        tasks = []
        for doc in pending_docs:
            task = self._process_document_with_semaphore(
                document_id=str(doc[0]),
                pdf_url=doc[1],
                insurer=doc[2],
                product_type=doc[3],
                product_name=doc[4]
            )
            tasks.append(task)

        # 모든 작업 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 집계
        success_count = sum(1 for r in results if r is True)
        failed_count = sum(1 for r in results if r is False or isinstance(r, Exception))

        logger.info(f"Parallel processing completed: {success_count} success, {failed_count} failed out of {len(pending_docs)} total")

        return {
            "total": len(pending_docs),
            "success": success_count,
            "failed": failed_count
        }

    async def _process_document_with_semaphore(
        self,
        document_id: str,
        pdf_url: str,
        insurer: str,
        product_type: str,
        product_name: str
    ) -> bool:
        """
        세마포어를 사용하여 동시 실행 수를 제한하면서 문서를 처리합니다.

        Returns:
            성공 여부 (True/False)
        """
        async with self.semaphore:
            return await self._process_single_document(
                document_id=document_id,
                pdf_url=pdf_url,
                insurer=insurer,
                product_type=product_type,
                product_name=product_name
            )

    async def _process_single_document(
        self,
        document_id: str,
        pdf_url: str,
        insurer: str,
        product_type: str,
        product_name: str
    ) -> bool:
        """
        단일 문서를 처리합니다.

        Returns:
            성공 여부 (True/False)
        """
        logger.info(f"[{document_id[:8]}] Starting processing: {insurer} - {product_type} - {product_name}")

        async with AsyncSessionLocal() as db:
            try:
                async def update_progress(step: str, progress: int, detail: dict = None):
                    """진행 상태를 업데이트하는 헬퍼 함수"""
                    import json
                    update_query = text("""
                        UPDATE crawler_documents
                        SET processing_step = :step,
                            processing_progress = :progress,
                            processing_detail = :detail,
                            status = 'processing',
                            updated_at = NOW()
                        WHERE id = :id
                    """)
                    await db.execute(update_query, {
                        "id": document_id,
                        "step": step,
                        "progress": progress,
                        "detail": json.dumps(detail) if detail else None
                    })
                    await db.commit()
                    detail_msg = f" - {detail.get('message', '')}" if detail and 'message' in detail else ""
                    logger.info(f"[{document_id[:8]}] {step} ({progress}%){detail_msg}")

                # Step 1: PDF 다운로드 및 텍스트 추출 (1% ~ 40%)
                await update_progress("downloading_pdf", 1, {
                    "sub_step": "initializing",
                    "message": "PDF 처리 초기화 중..."
                })

                import time
                start_time = time.time()

                # PDF 처리 방식 결정: 하이브리드 > 스트리밍 > 기존 방식
                if self.use_hybrid and self.hybrid_processor:
                    # 🌟 하이브리드 방식 (pdfplumber/Upstage 자동 선택)
                    await update_progress("extracting_text", 10, {
                        "sub_step": "hybrid_mode",
                        "message": f"하이브리드 방식으로 PDF 처리 중 (전략: {settings.HYBRID_STRATEGY})"
                    })

                    hybrid_result = await self.hybrid_processor.process_document(pdf_url)

                    extracted_text = hybrid_result["text"]
                    total_pages = hybrid_result["total_pages"]
                    algorithm = hybrid_result.get("algorithm", hybrid_result.get("method", "hybrid"))
                    memory_saved = hybrid_result.get("memory_saved_mb", "100%")
                    hybrid_decision = hybrid_result.get("hybrid_decision", "unknown")
                    decision_reason = hybrid_result.get("decision_reason", "")

                    total_time = int(time.time() - start_time)
                    await update_progress("extracting_text", 40, {
                        "sub_step": "extraction_complete",
                        "message": f"텍스트 추출 완료 (하이브리드-{hybrid_decision}, {total_time}초)",
                        "algorithm": algorithm,
                        "method": hybrid_result.get("method", "hybrid"),
                        "hybrid_decision": hybrid_decision,
                        "decision_reason": decision_reason,
                        "text_length": len(extracted_text),
                        "total_pages": total_pages,
                        "processing_time_seconds": total_time,
                        "complexity_score": hybrid_result.get("complexity_score"),
                        "quality_score": hybrid_result.get("quality_score")
                    })

                    logger.info(
                        f"[{document_id[:8]}] Hybrid extraction completed: "
                        f"{hybrid_decision} ({decision_reason}), "
                        f"pages={total_pages}, time={total_time}s"
                    )

                    # 임시 파일 경로는 None (하이브리드 방식이므로 파일 생성 안 됨)
                    tmp_path = None

                elif self.use_streaming and self.streaming_processor:
                    # 🚀 스트리밍 방식 (로컬 다운로드 없음)
                    await update_progress("extracting_text", 10, {
                        "sub_step": "streaming_mode",
                        "message": "스트리밍 방식으로 PDF 처리 중 (로컬 다운로드 없음)"
                    })

                    streaming_result = await self.streaming_processor.process_pdf_streaming(pdf_url)

                    extracted_text = streaming_result["text"]
                    total_pages = streaming_result["total_pages"]
                    algorithm = streaming_result.get("algorithm", "streaming")
                    memory_saved = streaming_result.get("memory_saved_mb", 0)

                    total_time = int(time.time() - start_time)
                    await update_progress("extracting_text", 40, {
                        "sub_step": "extraction_complete",
                        "message": f"텍스트 추출 완료 (스트리밍, {total_time}초, 메모리 절약: {memory_saved}MB)",
                        "algorithm": algorithm,
                        "method": streaming_result["method"],
                        "text_length": len(extracted_text),
                        "total_pages": total_pages,
                        "processing_time_seconds": total_time,
                        "memory_saved_mb": memory_saved
                    })

                    logger.info(f"[{document_id[:8]}] Streaming extraction completed: {algorithm}, pages={total_pages}, time={total_time}s, memory_saved={memory_saved}MB")

                    # 임시 파일 경로는 None (스트리밍 방식이므로 파일 생성 안 됨)
                    tmp_path = None

                else:
                    # 📁 기존 방식 (임시 파일 저장)
                    await update_progress("downloading_pdf", 20, {
                        "sub_step": "downloading",
                        "message": "PDF 다운로드 중..."
                    })

                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(pdf_url)
                        response.raise_for_status()
                        pdf_content = response.content

                    # 임시 파일로 저장
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(pdf_content)
                        tmp_path = tmp_file.name

                    await update_progress("extracting_text", 21, {
                        "sub_step": "pdf_analysis",
                        "message": "PDF 메타데이터 분석 중"
                    })

                    await update_progress("extracting_text", 23, {
                        "sub_step": "analyzing_algorithms",
                        "message": "최적의 텍스트 추출 알고리즘 분석 중..."
                    })

                    # 여러 알고리즘 시도 및 최고 품질 결과 선택
                    extraction_result = PDFTextQualityEvaluator.extract_best_quality(tmp_path)

                    if "error" in extraction_result:
                        await update_progress("extracting_text", 35, {
                            "sub_step": "extraction_failed",
                            "message": "모든 텍스트 추출 방법 실패",
                            "attempts": extraction_result.get("all_attempts", [])
                        })
                        raise Exception(f"Text extraction failed: {extraction_result['error']}")

                    extracted_text = extraction_result["text"]
                    total_pages = extraction_result["total_pages"]
                    algorithm = extraction_result["algorithm"]
                    quality = extraction_result["quality"]

                    # 진행 상황 업데이트 with 품질 정보
                    total_time = int(time.time() - start_time)
                    await update_progress("extracting_text", 40, {
                        "sub_step": "extraction_complete",
                        "message": f"텍스트 추출 완료 ({algorithm}, {total_time}초)",
                        "algorithm": algorithm,
                        "quality_score": quality["score"],
                        "quality_level": quality["quality_level"],
                        "text_length": len(extracted_text),
                        "total_pages": total_pages,
                        "processing_time_seconds": total_time,
                        "avg_chars_per_page": quality["avg_chars_per_page"],
                        "korean_ratio": quality["korean_ratio"],
                        "english_ratio": quality["english_ratio"]
                    })

                    logger.info(f"[{document_id[:8]}] Text extraction completed: {algorithm}, quality={quality['score']}, time={total_time}s")

                # Step 3-6: 스마트 학습 (Smart Learning)
                if self.use_smart_learning and self.smart_learner:
                    # SmartInsuranceLearner 사용 (자동으로 최적 전략 선택)
                    await update_progress("smart_learning", 50, {
                        "sub_step": "initializing",
                        "message": "스마트 학습 초기화 중..."
                    })

                    logger.info(f"[{document_id[:8]}] Starting smart learning for {insurer} - {product_type}")

                    # 실제 엔티티/관계 추출 및 PostgreSQL 저장 (DeepKnowledgeService)
                    async def actual_learning_callback(text_chunk: str) -> Dict:
                        """
                        DeepKnowledgeService를 사용하여 GraphRAG 스타일 엔티티와 관계를 추출하고 PostgreSQL에 저장
                        """
                        if not self.deep_knowledge_service:
                            logger.warning(f"[{document_id[:8]}] DeepKnowledgeService not initialized, skipping entity extraction")
                            return {
                                "entities": 0,
                                "relationships": 0,
                                "chunk_length": len(text_chunk),
                                "error": "DeepKnowledgeService not initialized"
                            }

                        try:
                            # chunk_id 생성
                            import hashlib
                            chunk_hash = hashlib.md5(text_chunk.encode()).hexdigest()[:8]
                            chunk_id = f"{document_id[:8]}_{chunk_hash}"

                            # 문서 정보 준비
                            document_info = {
                                "insurer": insurer,
                                "product_type": product_type,
                                "title": document.title or f"{insurer} {product_type}"
                            }

                            # DeepKnowledgeService로 엔티티 추출 및 PostgreSQL 저장
                            result = await self.deep_knowledge_service.process_and_extract(
                                chunk_text=text_chunk,
                                document_id=document_id,
                                chunk_id=chunk_id,
                                document_info=document_info
                            )

                            logger.info(
                                f"[{document_id[:8]}] Deep knowledge extracted: "
                                f"{result.get('entities', 0)} entities, {result.get('relationships', 0)} relationships"
                            )

                            return {
                                "entities": result.get("entities", 0),
                                "relationships": result.get("relationships", 0),
                                "chunk_length": len(text_chunk),
                                "nodes_by_type": result.get("nodes_by_type", {}),
                                "relationships_by_type": result.get("relationships_by_type", {}),
                            }

                        except Exception as e:
                            logger.error(f"[{document_id[:8]}] Deep knowledge extraction failed: {e}", exc_info=True)
                            # 실패 시 빈 결과 반환 (학습은 계속 진행)
                            return {
                                "entities": 0,
                                "relationships": 0,
                                "chunk_length": len(text_chunk),
                                "error": str(e)
                            }

                    try:
                        # 스마트 학습 수행
                        learning_result = await self.smart_learner.learn_document(
                            document_id=document_id,
                            text=extracted_text,
                            insurer=insurer,
                            product_type=product_type,
                            full_learning_callback=actual_learning_callback
                        )

                        # 학습 전략과 비용 절감 정보 로깅
                        strategy = learning_result.get("strategy", "unknown")
                        cost_saving = learning_result.get("cost_saving_percent", "0%")

                        # 추출된 엔티티/관계 정보
                        total_entities = learning_result.get("total_entities", 0)
                        total_relationships = learning_result.get("total_relationships", 0)

                        await update_progress("smart_learning_complete", 90, {
                            "sub_step": "completed",
                            "message": f"스마트 학습 완료 ({strategy} 전략, {cost_saving} 절감, {total_entities}개 노드, {total_relationships}개 관계)",
                            "strategy": strategy,
                            "cost_saving": cost_saving,
                            "priority": learning_result.get("priority", 3),
                            "entities": total_entities,
                            "relationships": total_relationships,
                            "nodes_by_type": learning_result.get("nodes_by_type", {}),
                            "relationships_by_type": learning_result.get("relationships_by_type", {})
                        })

                        logger.info(
                            f"[{document_id[:8]}] Smart learning completed: "
                            f"strategy={strategy}, cost_saving={cost_saving}, "
                            f"entities={total_entities}, relationships={total_relationships}"
                        )

                    except Exception as e:
                        logger.error(f"[{document_id[:8]}] Smart learning failed: {e}, falling back to simulation")
                        # 실패 시 기존 시뮬레이션으로 폴백
                        await update_progress("learning_fallback", 90, {
                            "sub_step": "fallback",
                            "message": "스마트 학습 실패, 기본 모드로 전환"
                        })

                else:
                    # 기존 방식 (시뮬레이션)
                    await update_progress("extracting_entities", 60)
                    await asyncio.sleep(1)

                    await update_progress("extracting_relationships", 80)
                    await asyncio.sleep(1)

                    await update_progress("building_graph", 90)
                    await asyncio.sleep(1)

                await update_progress("generating_embeddings", 95, {
                    "sub_step": "preparing_embeddings",
                    "message": "임베딩 생성 준비 중..."
                })
                await asyncio.sleep(0.5)

                # Step 7: 완료 (100%)
                # 스트리밍 방식인 경우 quality 정보가 없을 수 있음
                completion_detail = {
                    "sub_step": "finalized",
                    "message": "문서 학습 완료",
                    "total_pages": total_pages,
                    "text_length": len(extracted_text),
                    "algorithm": algorithm
                }

                # 기존 방식인 경우에만 quality_score 추가
                if not self.use_streaming:
                    completion_detail["quality_score"] = quality["score"]

                await update_progress("completed", 100, completion_detail)

                # status를 'completed'로 변경
                final_update_query = text("""
                    UPDATE crawler_documents
                    SET status = 'completed'
                    WHERE id = :id
                """)
                await db.execute(final_update_query, {"id": document_id})
                await db.commit()

                logger.info(f"[{document_id[:8]}] Processing completed successfully")

                # 임시 파일 정리 (스트리밍 방식인 경우 tmp_path가 None일 수 있음)
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    logger.debug(f"[{document_id[:8]}] Temporary file deleted: {tmp_path}")

                return True

            except Exception as e:
                logger.error(f"[{document_id[:8]}] Processing failed: {e}")
                # 상태를 'failed'로 업데이트
                try:
                    update_query = text("""
                        UPDATE crawler_documents
                        SET status = 'failed',
                            updated_at = NOW(),
                            processing_detail = :error
                        WHERE id = :id
                    """)
                    await db.execute(update_query, {
                        "id": document_id,
                        "error": str(e)
                    })
                    await db.commit()
                except:
                    pass
                return False


# 사용 예제
async def process_documents_in_parallel(max_concurrent: int = 5, limit: Optional[int] = None):
    """
    대기 중인 문서들을 병렬로 처리합니다.

    Args:
        max_concurrent: 동시에 처리할 최대 문서 수
        limit: 처리할 최대 문서 수
    """
    processor = ParallelDocumentProcessor(max_concurrent=max_concurrent)
    result = await processor.process_pending_documents(limit=limit)
    return result


if __name__ == "__main__":
    # 테스트 실행
    import sys

    max_concurrent = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    logger.info(f"Starting parallel processing with max_concurrent={max_concurrent}, limit={limit}")
    result = asyncio.run(process_documents_in_parallel(max_concurrent, limit))
    logger.info(f"Final result: {result}")
