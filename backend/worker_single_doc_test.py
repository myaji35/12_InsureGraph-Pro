"""
Single Document LLM Test - Process smallest document with Opus

메트라이프 변액연금보험 약관 1개 문서만 LLM 처리하여:
1. 비용 측정
2. 결과 품질 확인
3. 규칙 기반과 비교
"""
import sys
import os
import asyncio
from typing import Optional
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

# 타겟 문서 ID (가장 작은 1.1MB 문서)
TARGET_DOC_ID = "4ee5193e-f404-4c3c-a191-dbcb91bbdf83"


class SingleDocumentTester:
    """단일 문서 LLM 테스트"""

    def __init__(self):
        """LLM 추출기 초기화"""
        self.llm_extractor = LLMEntityExtractor()

    async def run(self):
        """메인 실행 함수"""
        logger.info("=" * 80)
        logger.info("📄 Single Document LLM Test with Opus")
        logger.info(f"🎯 Target Document: {TARGET_DOC_ID}")
        logger.info("=" * 80)

        # 1. 문서 조회
        async with AsyncSessionLocal() as db:
            query_str = f"""
                SELECT id, title, insurer, category, product_type, pdf_url
                FROM crawler_documents
                WHERE id = '{TARGET_DOC_ID}' AND status = 'completed'
            """
            result = await db.execute(sql_text(query_str))
            doc = result.fetchone()

        if not doc:
            logger.error(f"❌ Document not found: {TARGET_DOC_ID}")
            return

        doc_id, title, insurer, category, product_type, pdf_url = doc
        doc_id = str(doc_id)

        logger.info(f"✅ Found document:")
        logger.info(f"   제목: {title}")
        logger.info(f"   보험사: {insurer}")
        logger.info(f"   카테고리: {category}")
        logger.info("")

        try:
            # Step 1: PDF 다운로드
            pdf_path = await self.download_pdf(doc_id, pdf_url, title)
            if not pdf_path:
                logger.error(f"Failed to download PDF")
                return

            # Step 2: 텍스트 추출
            text = await self.extract_text_from_pdf(pdf_path)
            if not text or len(text) < 500:
                logger.warning(f"Insufficient text extracted: {len(text)} chars")
                return

            logger.info(f"✅ Extracted {len(text):,} characters")

            # Step 3: 청크 분할
            chunks = self._chunk_text(text, chunk_size=4000)
            logger.info(f"📄 Split into {len(chunks)} chunks")

            # 예상 비용 및 시간 계산
            estimated_time_minutes = len(chunks) * 2
            estimated_cost = len(chunks) * 0.15

            logger.info(f"⏱️  Estimated time: {estimated_time_minutes} minutes ({estimated_time_minutes/60:.1f} hours)")
            logger.info(f"💰 Estimated cost: ${estimated_cost:.2f}")
            logger.info("")

            # Step 4: LLM 추출
            logger.info("🚀 Starting LLM extraction...")
            entities, relationships = self.llm_extractor.extract_from_chunks(
                chunks=chunks,
                insurer=insurer,
                product_type=product_type or "연금보험",
                document_id=doc_id
            )

            # Step 5: 데이터베이스에 저장
            saved_entities, saved_relationships = await self.save_entities(
                doc_id, entities, relationships
            )

            # Step 6: 결과 출력
            logger.info(f"\n{'=' * 80}")
            logger.info(f"✅ LLM Extraction Complete!")
            logger.info(f"{'=' * 80}")
            logger.info(f"📊 Results:")
            logger.info(f"   Entities: {saved_entities}")
            logger.info(f"   Relationships: {saved_relationships}")
            logger.info(f"   Ratio: {saved_relationships / saved_entities if saved_entities else 0:.2f}")
            logger.info(f"{'=' * 80}")

            # Step 7: 데이터베이스 통계 비교
            await self.show_comparison_stats(doc_id)

        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)

    async def download_pdf(self, doc_id: str, pdf_url: str, title: str) -> Optional[Path]:
        """PDF 다운로드"""
        try:
            safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title[:50])
            pdf_filename = f"{doc_id}_{safe_filename}.pdf"
            pdf_path = PDF_DIR / pdf_filename

            if pdf_path.exists():
                logger.info(f"✅ PDF already exists")
                return pdf_path

            logger.info(f"⬇️  Downloading PDF...")
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded: {len(response.content):,} bytes")
            return pdf_path

        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None

    async def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """PDF에서 텍스트 추출"""
        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"📄 Extracting text from {len(pdf.pages)} pages...")
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    if page_num % 10 == 0:
                        logger.info(f"   Processed {page_num}/{len(pdf.pages)} pages")

            full_text = "\n\n".join(text_parts)
            return full_text

        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> list:
        """텍스트를 청크로 분할"""
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            chunk = text[current_pos:current_pos + chunk_size]
            chunks.append(chunk)
            current_pos += chunk_size

        return chunks

    async def save_entities(self, doc_id: str, entities: list, relationships: list) -> tuple[int, int]:
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
            logger.error(f"❌ Save failed: {e}", exc_info=True)
            return 0, 0

    async def show_comparison_stats(self, doc_id: str):
        """처리된 문서의 통계 출력"""
        try:
            async with AsyncSessionLocal() as db:
                # 전체 통계
                total_entities_query = "SELECT COUNT(*) FROM knowledge_entities"
                total_rels_query = "SELECT COUNT(*) FROM knowledge_relationships"

                result = await db.execute(sql_text(total_entities_query))
                total_entities = result.scalar()

                result = await db.execute(sql_text(total_rels_query))
                total_rels = result.scalar()

                # 이 문서의 통계
                doc_entities_query = f"""
                    SELECT COUNT(*) FROM knowledge_entities
                    WHERE document_id = '{doc_id}'
                """
                doc_rels_query = f"""
                    SELECT COUNT(*) FROM knowledge_relationships r
                    JOIN knowledge_entities e ON r.source_entity_id = e.entity_id
                    WHERE e.document_id = '{doc_id}'
                """

                result = await db.execute(sql_text(doc_entities_query))
                doc_entities = result.scalar()

                result = await db.execute(sql_text(doc_rels_query))
                doc_rels = result.scalar()

                logger.info(f"\n{'=' * 80}")
                logger.info(f"📊 Database Statistics:")
                logger.info(f"")
                logger.info(f"   전체 그래프:")
                logger.info(f"   - Entities: {total_entities:,}")
                logger.info(f"   - Relationships: {total_rels:,}")
                logger.info(f"   - Ratio: {total_rels / total_entities if total_entities else 0:.2f}")
                logger.info(f"")
                logger.info(f"   이 문서 (LLM 처리):")
                logger.info(f"   - Entities: {doc_entities:,}")
                logger.info(f"   - Relationships: {doc_rels:,}")
                logger.info(f"   - Ratio: {doc_rels / doc_entities if doc_entities else 0:.2f}")
                logger.info(f"{'=' * 80}")

        except Exception as e:
            logger.error(f"Failed to show comparison stats: {e}")


async def main():
    """메인 함수"""
    tester = SingleDocumentTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
