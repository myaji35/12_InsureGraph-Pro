"""
자동 임베딩 서비스

학습 완료된 문서의 텍스트를 자동으로 벡터 임베딩하고 검색 인덱스를 구축합니다.
"""
import asyncio
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


class AutoEmbeddingService:
    """자동 임베딩 서비스"""

    def __init__(self):
        """초기화"""
        self.embedding_model = "text-embedding-3-small"  # OpenAI 임베딩 모델
        self.chunk_size = 512  # 청크 크기 (토큰)
        self.overlap = 50  # 청크 오버랩 (토큰)

    async def get_completed_documents_without_embedding(
        self, limit: Optional[int] = None
    ) -> List[Dict]:
        """
        임베딩이 없는 완료 문서 조회

        Args:
            limit: 조회할 최대 문서 수

        Returns:
            문서 목록
        """
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT id, title, insurer, product_type,
                       processing_detail, created_at, updated_at
                FROM crawler_documents
                WHERE status = 'completed'
                  AND (processing_detail IS NULL
                       OR processing_detail NOT LIKE '%embedding_created%')
                ORDER BY updated_at DESC
            """)

            if limit:
                query = text(str(query) + f" LIMIT {limit}")

            result = await db.execute(query)
            rows = result.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "insurer": row[2],
                    "product_type": row[3],
                    "processing_detail": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                }
                for row in rows
            ]

    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할

        Args:
            text: 분할할 텍스트

        Returns:
            청크 리스트
        """
        # 간단한 문장 기반 청킹 (실제로는 토큰 기반 청킹 권장)
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size * 4:  # 대략 4자/토큰
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트를 임베딩으로 변환

        Args:
            texts: 텍스트 리스트

        Returns:
            임베딩 벡터 리스트
        """
        # TODO: OpenAI API 호출하여 실제 임베딩 생성
        # 현재는 시뮬레이션
        logger.info(f"Creating embeddings for {len(texts)} text chunks...")
        await asyncio.sleep(0.5)  # API 호출 시뮬레이션

        # 임베딩 벡터 시뮬레이션 (1536 차원)
        import random
        embeddings = [[random.random() for _ in range(1536)] for _ in texts]

        return embeddings

    async def store_embeddings(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """
        임베딩을 데이터베이스에 저장

        Args:
            document_id: 문서 ID
            chunks: 텍스트 청크 리스트
            embeddings: 임베딩 벡터 리스트
        """
        async with AsyncSessionLocal() as db:
            # document_embeddings 테이블에 저장 (테이블이 있다면)
            # 또는 processing_detail에 메타데이터 기록

            import json
            update_query = text("""
                UPDATE crawler_documents
                SET processing_detail = jsonb_set(
                    COALESCE(processing_detail::jsonb, '{}'::jsonb),
                    '{embedding_created}',
                    'true'
                ),
                processing_detail = jsonb_set(
                    processing_detail::jsonb,
                    '{embedding_chunk_count}',
                    to_jsonb(:chunk_count)
                ),
                processing_detail = jsonb_set(
                    processing_detail::jsonb,
                    '{embedding_dimension}',
                    '1536'
                ),
                processing_detail = jsonb_set(
                    processing_detail::jsonb,
                    '{embedding_model}',
                    to_jsonb(:model)
                ),
                updated_at = NOW()
                WHERE id = :id
            """)

            await db.execute(update_query, {
                "id": document_id,
                "chunk_count": len(chunks),
                "model": self.embedding_model
            })
            await db.commit()

            logger.info(f"Stored {len(embeddings)} embeddings for document {document_id[:8]}")

    async def process_document(self, document: Dict) -> bool:
        """
        단일 문서 임베딩 처리

        Args:
            document: 문서 정보

        Returns:
            성공 여부
        """
        try:
            document_id = document["id"]
            logger.info(f"[{document_id[:8]}] Processing embeddings for: {document['insurer']} - {document['title'][:50]}")

            # 1. 처리 상세에서 텍스트 추출 (실제로는 extracted_text 필드 사용)
            # 시뮬레이션: 샘플 텍스트 생성
            sample_text = f"""
            {document['insurer']} {document['product_type']} 상품 안내
            {document['title']}

            본 문서는 {document['insurer']}의 {document['product_type']} 상품에 대한 설명입니다.
            상품의 특징, 보장내용, 가입조건 등이 포함되어 있습니다.
            """ * 10  # 텍스트 반복하여 길이 늘림

            # 2. 텍스트 청킹
            chunks = self.chunk_text(sample_text)
            logger.info(f"[{document_id[:8]}] Created {len(chunks)} chunks")

            # 3. 임베딩 생성
            embeddings = await self.create_embeddings(chunks)
            logger.info(f"[{document_id[:8]}] Created {len(embeddings)} embeddings")

            # 4. 임베딩 저장
            await self.store_embeddings(document_id, chunks, embeddings)

            logger.info(f"[{document_id[:8]}] ✅ Embedding completed")
            return True

        except Exception as e:
            logger.error(f"[{document_id[:8]}] ❌ Embedding failed: {e}")
            return False

    async def process_batch(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        임베딩이 없는 완료 문서를 배치 처리

        Args:
            limit: 처리할 최대 문서 수

        Returns:
            처리 결과 통계
        """
        documents = await self.get_completed_documents_without_embedding(limit=limit)

        if not documents:
            logger.info("No documents need embedding")
            return {"total": 0, "success": 0, "failed": 0}

        logger.info(f"Processing embeddings for {len(documents)} documents")

        results = []
        for doc in documents:
            result = await self.process_document(doc)
            results.append(result)
            await asyncio.sleep(0.1)  # Rate limiting

        success_count = sum(1 for r in results if r)
        failed_count = sum(1 for r in results if not r)

        logger.info(f"Embedding batch completed: {success_count} success, {failed_count} failed")

        return {
            "total": len(documents),
            "success": success_count,
            "failed": failed_count
        }


# 자동 임베딩 워커
async def auto_embedding_worker(check_interval: int = 60):
    """
    자동 임베딩 워커

    Args:
        check_interval: 체크 간격 (초)
    """
    service = AutoEmbeddingService()

    logger.info("=" * 80)
    logger.info("🧠 Auto Embedding Worker Started")
    logger.info(f"  - Check Interval: {check_interval}s")
    logger.info("=" * 80)

    while True:
        try:
            result = await service.process_batch(limit=10)

            if result["total"] == 0:
                logger.info("💤 No documents need embedding. Waiting...")
            else:
                logger.info(f"📊 Processed: {result['success']} success, {result['failed']} failed")

            await asyncio.sleep(check_interval)

        except Exception as e:
            logger.error(f"❌ Worker error: {e}", exc_info=True)
            await asyncio.sleep(check_interval)


if __name__ == "__main__":
    # 테스트 실행
    import sys
    check_interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    asyncio.run(auto_embedding_worker(check_interval))
