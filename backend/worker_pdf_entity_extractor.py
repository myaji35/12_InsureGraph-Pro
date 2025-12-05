"""
PDF Download, Text Extraction, and Entity Extraction Worker

71개의 완료된 문서에서 PDF를 다운로드하고, 텍스트를 추출한 후,
Claude API를 사용하여 10가지 엔티티를 추출합니다.
"""
import sys
import os
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pdfplumber
from loguru import logger
from anthropic import Anthropic
from sqlalchemy import text as sql_text

from app.core.database import AsyncSessionLocal
from app.core.config import settings

# PDF 저장 경로
PDF_DIR = Path(__file__).parent / "data" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)


class PDFEntityExtractor:
    """PDF 다운로드, 텍스트 추출, 엔티티 추출을 수행하는 워커"""

    def __init__(self):
        """초기화"""
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def run(self, limit: Optional[int] = None):
        """메인 실행 함수"""
        logger.info("=" * 80)
        logger.info("📚 PDF Entity Extractor Worker Started")
        logger.info("=" * 80)

        # 1. 완료된 문서 조회
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

                # Step 3: Claude API로 엔티티 추출
                entities, relationships = await self.extract_entities_with_claude(
                    text, doc_id, title, insurer, product_type
                )

                # Step 4: 데이터베이스에 저장
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
        logger.info(f"={'=' * 80}")

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

    async def extract_entities_with_claude(
        self,
        text: str,
        doc_id: str,
        title: str,
        insurer: str,
        product_type: str
    ) -> tuple[List[Dict], List[Dict]]:
        """Claude API를 사용하여 엔티티 추출"""
        try:
            # 텍스트가 너무 길면 앞부분만 사용 (Claude API 토큰 제한)
            max_chars = 50000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[텍스트가 잘렸습니다...]"

            prompt = f"""다음은 {insurer}의 {product_type} 보험약관 문서입니다.

문서 제목: {title}

보험약관 내용:
{text}

위 보험약관에서 다음 10가지 타입의 엔티티를 추출해주세요:

1. coverage_item (보장항목): 보험에서 보장하는 항목
2. benefit_amount (보험금액): 지급되는 보험금 금액
3. payment_condition (지급조건): 보험금 지급 조건
4. exclusion (면책사항): 보장하지 않는 사항
5. deductible (자기부담금): 본인이 부담해야 하는 금액
6. rider (특약): 추가 특약
7. eligibility (가입조건): 가입 가능한 조건
8. article (약관조항): 약관 조항 번호
9. term (보험용어): 보험 관련 용어
10. period (기간): 보험 관련 기간

JSON 형식으로 응답해주세요:
{{
  "entities": [
    {{
      "label": "엔티티 이름",
      "type": "엔티티 타입",
      "description": "엔티티 설명 (1-2문장)",
      "source_text": "엔티티가 발견된 원문 (최대 200자)"
    }}
  ]
}}

최대 50개의 엔티티를 추출하되, 가장 중요한 것들만 선택해주세요.
"""

            logger.info(f"   🤖 Calling Claude API...")

            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 응답 파싱
            response_text = message.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # JSON 파싱
            import json
            # JSON 블록 추출 (```json ... ``` 제거)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_text = response_text[json_start:json_end]

            result = json.loads(json_text)
            raw_entities = result.get('entities', [])

            # 엔티티 포맷 변환
            entities = []
            for ent in raw_entities:
                entity = {
                    "entity_id": str(uuid.uuid4()),
                    "label": ent.get("label", "").strip()[:200],
                    "type": ent.get("type", "term"),
                    "description": ent.get("description", "").strip()[:500],
                    "source_text": ent.get("source_text", "").strip()[:200],
                    "document_id": doc_id,
                    "insurer": insurer,
                    "product_type": product_type,
                    "created_at": datetime.utcnow()
                }
                entities.append(entity)

            logger.info(f"   ✅ Extracted {len(entities)} entities from Claude API")

            # 간단한 관계 생성 (같은 문서 내 엔티티끼리 연결)
            relationships = []
            coverage_items = [e for e in entities if e['type'] == 'coverage_item']
            benefit_amounts = [e for e in entities if e['type'] == 'benefit_amount']

            # coverage_item <-> benefit_amount 관계
            for cov in coverage_items[:5]:  # 최대 5개만
                for amt in benefit_amounts[:3]:  # 각각 3개씩만
                    relationships.append({
                        "source_entity_id": cov["entity_id"],
                        "target_entity_id": amt["entity_id"],
                        "type": "has_amount",
                        "description": f"{cov['label']}의 보험금액은 {amt['label']}입니다",
                        "created_at": datetime.utcnow()
                    })

            return entities, relationships

        except Exception as e:
            logger.error(f"   ❌ Claude API extraction failed: {repr(e)}")
            return [], []

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

    extractor = PDFEntityExtractor()
    await extractor.run(limit=limit)


if __name__ == "__main__":
    asyncio.run(main())
