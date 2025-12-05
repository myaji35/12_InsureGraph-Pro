"""
Upstage Document Parse API Integration

보험약관 같은 복잡한 한국어 문서 처리에 최적화된 Upstage Document Parse API를 활용합니다.

주요 기능:
1. 고품질 한국어 텍스트 추출
2. 레이아웃 분석 및 구조화
3. 표, 이미지 인식
4. 계층적 섹션 분석
"""
import httpx
from typing import Dict, List, Optional, Any
from loguru import logger
from app.core.config import settings


class UpstageDocumentParser:
    """Upstage Document Parse API를 사용한 고품질 문서 파싱"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Upstage Document Parser

        Args:
            api_key: Upstage API key (기본값: settings.UPSTAGE_API_KEY)
        """
        self.api_key = api_key or settings.UPSTAGE_API_KEY
        self.base_url = "https://api.upstage.ai/v1/document-ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        self.timeout = 300.0  # 5분 (대용량 문서 처리 시간 고려)

    async def parse_document_from_url(
        self,
        document_url: str,
        ocr: bool = True,
        extract_tables: bool = True,
        extract_images: bool = False,
        coordinates: bool = False,
    ) -> Dict[str, Any]:
        """
        URL로부터 문서를 파싱 (로컬 다운로드 불필요)

        Args:
            document_url: 문서 URL (PDF, DOCX, PPTX 등 지원)
            ocr: OCR 사용 여부 (이미지 기반 PDF 처리)
            extract_tables: 표 추출 여부
            extract_images: 이미지 추출 여부
            coordinates: 텍스트 좌표 정보 포함 여부

        Returns:
            {
                "text": "전체 텍스트",
                "pages": [...],  # 페이지별 정보
                "tables": [...],  # 추출된 표
                "sections": [...],  # 계층적 섹션 구조
                "metadata": {...},
                "quality_score": 0.95
            }
        """
        logger.info(f"Parsing document from URL with Upstage API: {document_url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Upstage Document Parse API 호출
                data = {
                    "document": document_url,
                    "ocr": "force" if ocr else "auto",
                }

                # 옵션 추가
                if extract_tables:
                    data["output_formats"] = "text,html"
                if coordinates:
                    data["coordinates"] = True

                response = await client.post(
                    f"{self.base_url}/document-parse",
                    headers=self.headers,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

            # 응답 파싱 및 정규화
            parsed_result = self._normalize_response(result)

            logger.info(
                f"✅ Upstage parsing completed: "
                f"{parsed_result['total_pages']} pages, "
                f"quality={parsed_result['quality_score']:.2f}"
            )

            return parsed_result

        except httpx.HTTPStatusError as e:
            logger.error(f"Upstage API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Upstage parsing failed: {e}")
            raise

    async def parse_document_from_file(
        self,
        file_path: str,
        ocr: bool = True,
        extract_tables: bool = True,
    ) -> Dict[str, Any]:
        """
        로컬 파일로부터 문서를 파싱

        Args:
            file_path: 로컬 파일 경로
            ocr: OCR 사용 여부
            extract_tables: 표 추출 여부

        Returns:
            파싱 결과 딕셔너리
        """
        logger.info(f"Parsing document from file with Upstage API: {file_path}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 파일 업로드
                with open(file_path, "rb") as f:
                    files = {"document": f}
                    data = {
                        "ocr": "force" if ocr else "auto",
                    }

                    if extract_tables:
                        data["output_formats"] = "text,html"

                    response = await client.post(
                        f"{self.base_url}/document-parse",
                        headers=self.headers,
                        files=files,
                        data=data,
                    )
                    response.raise_for_status()
                    result = response.json()

            # 응답 파싱 및 정규화
            parsed_result = self._normalize_response(result)

            logger.info(
                f"✅ Upstage parsing completed: "
                f"{parsed_result['total_pages']} pages"
            )

            return parsed_result

        except Exception as e:
            logger.error(f"Upstage parsing from file failed: {e}")
            raise

    def _normalize_response(self, raw_response: Dict) -> Dict[str, Any]:
        """
        Upstage API 응답을 표준 포맷으로 정규화

        Args:
            raw_response: Upstage API 원본 응답

        Returns:
            정규화된 응답 딕셔너리
        """
        # Upstage API 응답 구조에 맞게 파싱
        # API 문서: https://developers.upstage.ai/docs/apis/document-parse

        pages = raw_response.get("content", {}).get("pages", [])

        # 전체 텍스트 추출
        full_text = ""
        page_texts = []

        for page in pages:
            page_text = page.get("text", "")
            page_texts.append(page_text)
            full_text += page_text + "\n\n"

        # 표 추출
        tables = []
        for page in pages:
            page_tables = page.get("tables", [])
            for table in page_tables:
                tables.append({
                    "page": page.get("page", 0),
                    "html": table.get("html", ""),
                    "text": table.get("text", ""),
                })

        # 섹션 구조 추출 (제목 기반 계층화)
        sections = self._extract_sections(pages)

        # 품질 점수 계산
        quality_score = self._calculate_quality_score(full_text, pages)

        return {
            "text": full_text.strip(),
            "total_pages": len(pages),
            "pages": page_texts,
            "tables": tables,
            "sections": sections,
            "metadata": {
                "total_characters": len(full_text),
                "total_tables": len(tables),
                "has_ocr": any(page.get("ocr_used", False) for page in pages),
            },
            "quality_score": quality_score,
            "method": "upstage_document_parse",
            "raw_response": raw_response,  # 디버깅용
        }

    def _extract_sections(self, pages: List[Dict]) -> List[Dict]:
        """
        페이지들로부터 계층적 섹션 구조 추출

        보험약관의 특성:
        - 제1장, 제2장 등의 장 구조
        - 제1조, 제2조 등의 조항 구조
        - 각 조항 내 항, 호 구조
        """
        sections = []
        current_chapter = None
        current_article = None

        import re

        for page_idx, page in enumerate(pages):
            text = page.get("text", "")
            lines = text.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 장 패턴: "제1장", "제2장" 등
                chapter_match = re.match(r"제(\d+)장\s*(.+)", line)
                if chapter_match:
                    current_chapter = {
                        "type": "chapter",
                        "number": int(chapter_match.group(1)),
                        "title": chapter_match.group(2).strip(),
                        "page": page_idx + 1,
                        "articles": []
                    }
                    sections.append(current_chapter)
                    continue

                # 조 패턴: "제1조", "제2조" 등
                article_match = re.match(r"제(\d+)조\s*\((.+?)\)", line)
                if article_match:
                    current_article = {
                        "type": "article",
                        "number": int(article_match.group(1)),
                        "title": article_match.group(2).strip(),
                        "page": page_idx + 1,
                        "content": ""
                    }

                    if current_chapter:
                        current_chapter["articles"].append(current_article)
                    else:
                        sections.append(current_article)
                    continue

                # 일반 내용 (현재 조항에 추가)
                if current_article:
                    current_article["content"] += line + "\n"

        return sections

    def _calculate_quality_score(self, text: str, pages: List[Dict]) -> float:
        """
        추출된 텍스트의 품질 점수 계산

        기준:
        - 한글 비율 (보험약관은 한글이 많아야 함)
        - 특수문자 비율 (너무 많으면 추출 실패)
        - 평균 줄 길이 (너무 짧으면 레이아웃 깨짐)
        """
        if not text:
            return 0.0

        # 한글 비율 계산
        korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
        korean_ratio = korean_chars / len(text) if text else 0

        # 특수문자 비율 계산
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0

        # 줄 평균 길이 계산
        lines = [line for line in text.split("\n") if line.strip()]
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

        # 점수 계산 (가중치 적용)
        score = 0.0
        score += min(korean_ratio * 2, 0.5)  # 한글 비율 (최대 0.5)
        score += max(0.3 - special_ratio, 0)  # 특수문자가 적을수록 좋음 (최대 0.3)
        score += min(avg_line_length / 100, 0.2)  # 적절한 줄 길이 (최대 0.2)

        return min(score, 1.0)

    async def extract_chunks_with_context(
        self,
        document_url: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        문서를 청크로 분할하되, 섹션 구조를 고려한 스마트 청킹

        Args:
            document_url: 문서 URL
            chunk_size: 청크 크기 (문자 수)
            overlap: 청크 간 중복 (문자 수)

        Returns:
            청크 리스트, 각 청크는 메타데이터 포함
        """
        # 1. 문서 파싱
        parsed = await self.parse_document_from_url(document_url)

        # 2. 섹션 기반 청킹
        chunks = []
        sections = parsed.get("sections", [])

        if sections:
            # 섹션이 있으면 섹션 단위로 청킹
            for section in sections:
                if section["type"] == "chapter":
                    # 장 단위로 청킹
                    for article in section.get("articles", []):
                        content = article.get("content", "")
                        if len(content) > chunk_size:
                            # 큰 조항은 더 작게 분할
                            sub_chunks = self._split_text(content, chunk_size, overlap)
                            for i, sub_chunk in enumerate(sub_chunks):
                                chunks.append({
                                    "text": sub_chunk,
                                    "metadata": {
                                        "chapter": section["number"],
                                        "chapter_title": section["title"],
                                        "article": article["number"],
                                        "article_title": article["title"],
                                        "sub_chunk": i + 1,
                                        "page": article["page"],
                                    }
                                })
                        else:
                            chunks.append({
                                "text": content,
                                "metadata": {
                                    "chapter": section["number"],
                                    "chapter_title": section["title"],
                                    "article": article["number"],
                                    "article_title": article["title"],
                                    "page": article["page"],
                                }
                            })
        else:
            # 섹션이 없으면 일반 텍스트 청킹
            text = parsed.get("text", "")
            text_chunks = self._split_text(text, chunk_size, overlap)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "chunk_index": i,
                    }
                })

        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks

    def _split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        텍스트를 청크로 분할 (오버랩 포함)
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks


# 사용 예시
async def example_usage():
    """Upstage Document Parser 사용 예시"""
    parser = UpstageDocumentParser()

    # 예시 1: URL로부터 문서 파싱
    result = await parser.parse_document_from_url(
        "https://example.com/insurance_policy.pdf",
        ocr=True,
        extract_tables=True,
    )

    print(f"총 페이지: {result['total_pages']}")
    print(f"품질 점수: {result['quality_score']:.2f}")
    print(f"추출된 섹션: {len(result['sections'])}개")
    print(f"추출된 표: {len(result['tables'])}개")

    # 예시 2: 스마트 청킹
    chunks = await parser.extract_chunks_with_context(
        "https://example.com/insurance_policy.pdf",
        chunk_size=1000,
        overlap=200,
    )

    for i, chunk in enumerate(chunks[:3]):  # 처음 3개만 출력
        print(f"\n--- Chunk {i+1} ---")
        print(f"메타데이터: {chunk['metadata']}")
        print(f"텍스트 미리보기: {chunk['text'][:100]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
