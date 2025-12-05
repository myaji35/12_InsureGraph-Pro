"""
PDF Download, Text Extraction, and LLM-Based Entity Extraction Worker

71개의 완료된 crawler_documents에서 PDF를 다운로드하고, 텍스트를 추출한 후,
Claude API 기반 LLM 엔티티 추출기를 사용하여 풍부한 엔티티와 관계를 추출합니다.
"""
import sys
import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pdfplumber
from loguru import logger
from sqlalchemy import text as sql_text

from app.core.database import AsyncSessionLocal
from app.services.llm_entity_extractor import LLMEntityExtractor

# PDF 저장 경로
PDF_DIR = Path(__file__).parent / "data" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)


class CrawlerDocumentEntityExtractor:
    """crawler_documents 테이블의 PDF에서 LLM 기반 엔티티를 추출하는 워커"""

    def __init__(self):
        """LLM 추출기 초기화"""
        self.llm_extractor = LLMEntityExtractor()

    async def run(self, limit: Optional[int] = None):
        """메인 실행 함수"""
        logger.info("=" * 80)
        logger.info("📚 Crawler Document LLM Entity Extractor Worker Started")
        logger.info("=" * 80)

        # 1. 완료된 문서 조회 (crawler_documents 테이블)
        async with AsyncSessionLocal() as db:
            query_str = """
                SELECT id, title, insurer, category, product_type, pdf_url
                FROM crawler_documents
                WHERE status = 'completed'
                ORDER BY created_at DESC
            """
            if limit:
                query_str += f" LIMIT {limit}"

            result = await db.execute(sql_text(query_str))
            documents = result.fetchall()

        logger.info(f"📄 Found {len(documents)} completed documents")

        # 2. 각 문서 처리
        total_entities = 0
        total_relationships = 0
        processed_count = 0
        failed_count = 0

        for doc in documents:
            doc_id, title, insurer, category, product_type, pdf_url = doc
            doc_id = str(doc_id)

            try:
                logger.info(f"\n{'=' * 80}")
                logger.info(f"📄 Processing: {title[:50]}...")
                logger.info(f"   보험사: {insurer}, 카테고리: {category}")

                # Step 1: PDF 다운로드
                pdf_path = await self.download_pdf(doc_id, pdf_url, title)
                if not pdf_path:
                    logger.error(f"Failed to download PDF for {doc_id}")
                    failed_count += 1
                    continue

                # Step 2: 텍스트 추출
                text = await self.extract_text_from_pdf(pdf_path)
                if not text or len(text) < 500:
                    logger.warning(f"Insufficient text extracted: {len(text)} chars")
                    failed_count += 1
                    continue

                logger.info(f"✅ Extracted {len(text):,} characters")

                # Step 3: LLM 기반 엔티티 및 관계 추출 (청크 단위 처리)
                chunks = self._chunk_text(text, chunk_size=4000)
                logger.info(f"   📄 Split into {len(chunks)} chunks for LLM processing")

                entities, relationships = self.llm_extractor.extract_from_chunks(
                    chunks=chunks,
                    insurer=insurer,
                    product_type=product_type,
                    document_id=doc_id
                )

                # Step 5: 데이터베이스에 저장
                saved_entities, saved_relationships = await self.save_entities(
                    doc_id, entities, relationships
                )

                total_entities += saved_entities
                total_relationships += saved_relationships
                processed_count += 1

                logger.info(f"✅ Saved {saved_entities} entities, {saved_relationships} relationships")

            except Exception as e:
                logger.error(f"❌ Error processing {doc_id}: {e}", exc_info=True)
                failed_count += 1

        # 3. 최종 통계
        logger.info(f"\n{'=' * 80}")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Total Documents: {len(documents)}")
        logger.info(f"   Processed: {processed_count}")
        logger.info(f"   Failed: {failed_count}")
        logger.info(f"   Total Entities: {total_entities}")
        logger.info(f"   Total Relationships: {total_relationships}")
        logger.info(f"{'=' * 80}")

    async def download_pdf(self, doc_id: str, pdf_url: str, title: str) -> Optional[Path]:
        """PDF 다운로드"""
        try:
            # 파일명 생성
            safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title[:50])
            pdf_filename = f"{doc_id}_{safe_filename}.pdf"
            pdf_path = PDF_DIR / pdf_filename

            # 이미 다운로드된 경우 스킵
            if pdf_path.exists():
                logger.info(f"   PDF already exists: {pdf_filename}")
                return pdf_path

            # PDF 다운로드
            logger.info(f"   Downloading PDF from {pdf_url[:60]}...")
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            # 파일 저장
            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"   ✅ Downloaded: {len(response.content):,} bytes")
            return pdf_path

        except Exception as e:
            logger.error(f"   ❌ Download failed: {e}")
            return None

    async def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """PDF에서 텍스트 추출"""
        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)
            return full_text

        except Exception as e:
            logger.error(f"   ❌ Text extraction failed: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> List[str]:
        """
        긴 텍스트를 청크로 분할 (LLM 컨텍스트 제한 대응)

        Args:
            text: 분할할 텍스트
            chunk_size: 청크 크기 (문자 수)

        Returns:
            청크 리스트
        """
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # 청크 추출
            chunk = text[current_pos:current_pos + chunk_size]
            chunks.append(chunk)
            current_pos += chunk_size

        return chunks

    async def save_entities(
        self,
        doc_id: str,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> tuple[int, int]:
        """엔티티와 관계를 데이터베이스에 저장"""
        try:
            async with AsyncSessionLocal() as db:
                # 기존 엔티티 삭제
                await db.execute(
                    sql_text("DELETE FROM knowledge_entities WHERE document_id = :doc_id"),
                    {"doc_id": doc_id}
                )

                # 엔티티 저장
                entity_count = 0
                for entity in entities:
                    await db.execute(sql_text("""
                        INSERT INTO knowledge_entities (
                            entity_id, label, type, description, source_text,
                            document_id, insurer, product_type, created_at
                        ) VALUES (
                            :entity_id, :label, :type, :description, :source_text,
                            :document_id, :insurer, :product_type, :created_at
                        )
                    """), entity)
                    entity_count += 1

                # 관계 저장
                relationship_count = 0
                for rel in relationships:
                    try:
                        await db.execute(sql_text("""
                            INSERT INTO knowledge_relationships (
                                source_entity_id, target_entity_id, type, description, created_at
                            ) VALUES (
                                :source_entity_id, :target_entity_id, :type, :description, :created_at
                            )
                        """), rel)
                        relationship_count += 1
                    except Exception:
                        pass  # 중복 관계는 무시

                await db.commit()

                return entity_count, relationship_count

        except Exception as e:
            logger.error(f"   ❌ Save failed: {e}", exc_info=True)
            return 0, 0


async def main():
    """메인 함수"""
    import sys

    # 명령줄 인자로 limit 받기
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5  # 기본 5개

    extractor = CrawlerDocumentEntityExtractor()
    await extractor.run(limit=limit)


if __name__ == "__main__":
    asyncio.run(main())
