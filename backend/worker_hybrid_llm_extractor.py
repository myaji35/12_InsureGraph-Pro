"""
Hybrid LLM Entity Extractor - Targeted Processing for Specific Documents

메트라이프 1개 + 삼성화재 1개 문서를 LLM으로 처리하는 타겟 워커
예산: $11 (문서당 ~$9, 총 2개)
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
PDF_DIR = Path(__file__).parent / "data" / "pdfs_llm"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# 타겟 문서 IDs
TARGET_DOCS = [
    "7e39d5e1-b652-4d2a-aacb-a437a10dba72",  # 메트라이프
    "2a92d88d-3279-4039-9d31-6796af9501f4"   # 삼성화재
]


class HybridLLMExtractor:
    """특정 문서만 LLM 처리하는 하이브리드 추출기"""

    def __init__(self):
        """LLM 추출기 초기화"""
        self.llm_extractor = LLMEntityExtractor()

    async def run(self):
        """메인 실행 함수"""
        logger.info("=" * 80)
        logger.info("🎯 Hybrid LLM Entity Extractor - Targeted Processing")
        logger.info(f"📋 Target Documents: {len(TARGET_DOCS)}")
        logger.info(f"💰 Budget: ~$11 (2 documents × $5-6 each)")
        logger.info("=" * 80)

        # 1. 타겟 문서 조회
        async with AsyncSessionLocal() as db:
            query_str = f"""
                SELECT id, title, insurer, category, product_type, pdf_url
                FROM crawler_documents
                WHERE id IN ('{TARGET_DOCS[0]}', '{TARGET_DOCS[1]}')
                ORDER BY insurer
            """
            result = await db.execute(sql_text(query_str))
            documents = result.fetchall()

        logger.info(f"📄 Found {len(documents)} target documents")

        if len(documents) != 2:
            logger.error(f"❌ Expected 2 documents, found {len(documents)}")
            return

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
                logger.info(f"📄 Processing: {title[:70]}...")
                logger.info(f"   보험사: {insurer}")
                logger.info(f"   카테고리: {category}")
                logger.info(f"   Document ID: {doc_id}")

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

                # Step 3: LLM 기반 엔티티 및 관계 추출 (청크 단위)
                chunks = self._chunk_text(text, chunk_size=4000)
                logger.info(f"   📄 Split into {len(chunks)} chunks for LLM processing")
                logger.info(f"   ⏱️  Estimated time: {len(chunks) * 2} minutes")
                logger.info(f"   💰 Estimated cost: ${len(chunks) * 0.15:.2f}")

                entities, relationships = self.llm_extractor.extract_from_chunks(
                    chunks=chunks,
                    insurer=insurer,
                    product_type=product_type or "약관",
                    document_id=doc_id
                )

                # Step 4: 데이터베이스에 저장
                saved_entities, saved_relationships = await self.save_entities(
                    doc_id, entities, relationships
                )

                total_entities += saved_entities
                total_relationships += saved_relationships
                processed_count += 1

                logger.info(f"✅ Saved {saved_entities} entities, {saved_relationships} relationships")
                logger.info(f"   📊 Relationship ratio: {saved_relationships / saved_entities if saved_entities else 0:.2f}")

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
        logger.info(f"   Overall Ratio: {total_relationships / total_entities if total_entities else 0:.2f}")
        logger.info(f"=" * 80)

        # 4. Neo4j 비교 통계 조회
        await self.show_comparison_stats()

    async def download_pdf(self, doc_id: str, pdf_url: str, title: str) -> Optional[Path]:
        """PDF 다운로드"""
        try:
            # 파일명 생성
            safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title[:50])
            pdf_filename = f"{doc_id}_{safe_filename}.pdf"
            pdf_path = PDF_DIR / pdf_filename

            # 이미 다운로드된 경우 스킵
            if pdf_path.exists():
                logger.info(f"   ✅ PDF already exists: {pdf_filename}")
                return pdf_path

            # PDF 다운로드
            logger.info(f"   ⬇️  Downloading PDF...")
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
                logger.info(f"   📄 Extracting text from {len(pdf.pages)} pages...")
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    if page_num % 10 == 0:
                        logger.info(f"      Processed {page_num}/{len(pdf.pages)} pages")

            full_text = "\n\n".join(text_parts)
            return full_text

        except Exception as e:
            logger.error(f"   ❌ Text extraction failed: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> List[str]:
        """
        긴 텍스트를 청크로 분할 (LLM 컨텍스트 제한 대응)
        """
        chunks = []
        current_pos = 0

        while current_pos < len(text):
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

    async def show_comparison_stats(self):
        """처리 전후 통계 비교"""
        try:
            async with AsyncSessionLocal() as db:
                # 전체 통계
                total_entities_query = "SELECT COUNT(*) FROM knowledge_entities"
                total_rels_query = "SELECT COUNT(*) FROM knowledge_relationships"

                result = await db.execute(sql_text(total_entities_query))
                total_entities = result.scalar()

                result = await db.execute(sql_text(total_rels_query))
                total_rels = result.scalar()

                # LLM 처리 문서의 통계
                llm_entities_query = f"""
                    SELECT COUNT(*) FROM knowledge_entities
                    WHERE document_id IN ('{TARGET_DOCS[0]}', '{TARGET_DOCS[1]}')
                """
                llm_rels_query = f"""
                    SELECT COUNT(*) FROM knowledge_relationships r
                    JOIN knowledge_entities e ON r.source_entity_id = e.entity_id
                    WHERE e.document_id IN ('{TARGET_DOCS[0]}', '{TARGET_DOCS[1]}')
                """

                result = await db.execute(sql_text(llm_entities_query))
                llm_entities = result.scalar()

                result = await db.execute(sql_text(llm_rels_query))
                llm_rels = result.scalar()

                logger.info(f"\n{'=' * 80}")
                logger.info(f"📊 Database Comparison Statistics:")
                logger.info(f"")
                logger.info(f"   전체 그래프:")
                logger.info(f"   - Entities: {total_entities:,}")
                logger.info(f"   - Relationships: {total_rels:,}")
                logger.info(f"   - Ratio: {total_rels / total_entities if total_entities else 0:.2f}")
                logger.info(f"")
                logger.info(f"   LLM 처리 문서 (2개):")
                logger.info(f"   - Entities: {llm_entities:,}")
                logger.info(f"   - Relationships: {llm_rels:,}")
                logger.info(f"   - Ratio: {llm_rels / llm_entities if llm_entities else 0:.2f}")
                logger.info(f"")
                logger.info(f"   🎯 LLM 처리 효과:")
                if llm_entities > 0:
                    overall_ratio = total_rels / total_entities if total_entities else 0
                    llm_ratio = llm_rels / llm_entities
                    improvement = ((llm_ratio - overall_ratio) / overall_ratio * 100) if overall_ratio > 0 else 0
                    logger.info(f"   - Relationship density improvement: {improvement:.1f}%")
                logger.info(f"=" * 80)

        except Exception as e:
            logger.error(f"Failed to show comparison stats: {e}")


async def main():
    """메인 함수"""
    extractor = HybridLLMExtractor()
    await extractor.run()


if __name__ == "__main__":
    asyncio.run(main())
