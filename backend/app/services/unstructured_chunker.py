"""
Unstructured.io 기반 보험 약관 고급 청킹 시스템

Features:
- Document layout analysis (제목, 본문, 표, 리스트 구분)
- Semantic chunking (의미 단위로 청킹)
- Table structure preservation (표 구조 완벽 보존)
- Hierarchy preservation (장-절-조 계층 구조 유지)
- Metadata extraction (페이지, 좌표, 폰트 정보)
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.chunking.title import chunk_by_title
    from unstructured.staging.base import elements_to_json
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    logger.warning("Unstructured.io not available - install with: pip install unstructured[pdf]")


class UnstructuredInsuranceChunker:
    """
    Unstructured.io 기반 보험 약관 전문 청킹 시스템

    보험 약관의 특수한 구조를 이해하고 최적의 청크를 생성합니다:
    - 제N장 (Chapter): 대분류
    - 제N조 (Article): 중분류
    - ①②③ (Paragraph): 소분류
    - 표 (Table): 독립 청크로 보존
    """

    # 보험 약관 패턴
    CHAPTER_PATTERN = re.compile(r'^제\s*[0-9]+\s*장')  # 제1장, 제 1 장
    ARTICLE_PATTERN = re.compile(r'^제\s*[0-9]+\s*조')  # 제1조, 제 1 조
    PARAGRAPH_PATTERN = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]')  # 항 번호
    LIST_PATTERN = re.compile(r'^\d+\.|^[가-힣]\.|^[-•]')  # 1. 가. - •

    def __init__(
        self,
        strategy: str = "hi_res",  # hi_res, fast, ocr_only
        max_characters: int = 1500,
        new_after_n_chars: int = 1200,
        combine_text_under_n_chars: int = 200,
        overlap: int = 100,
    ):
        """
        Initialize Unstructured Insurance Chunker

        Args:
            strategy: PDF 파싱 전략
                - hi_res: 고해상도 분석 (느림, 정확)
                - fast: 빠른 분석 (빠름, 적당)
                - ocr_only: OCR만 사용 (이미지 PDF)
            max_characters: 청크 최대 크기
            new_after_n_chars: 이 크기 이후 새 청크 생성
            combine_text_under_n_chars: 이보다 작은 청크는 병합
            overlap: 청크 간 중복 문자 수 (컨텍스트 보존)
        """
        if not UNSTRUCTURED_AVAILABLE:
            raise ImportError(
                "Unstructured.io가 설치되지 않았습니다.\n"
                "설치: pip install unstructured[pdf] unstructured-inference pdf2image"
            )

        self.strategy = strategy
        self.max_characters = max_characters
        self.new_after_n_chars = new_after_n_chars
        self.combine_text_under_n_chars = combine_text_under_n_chars
        self.overlap = overlap

        logger.info(
            f"UnstructuredInsuranceChunker initialized: "
            f"strategy={strategy}, max_chars={max_characters}"
        )

    def parse_and_chunk(
        self,
        pdf_path: str,
        extract_images: bool = False,
        infer_table_structure: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        PDF 파싱 + 청킹 (Unstructured.io)

        Args:
            pdf_path: PDF 파일 경로
            extract_images: 이미지 추출 여부
            infer_table_structure: 표 구조 추론 여부

        Returns:
            List[Dict]: 청크 리스트
                - chunk_id: 청크 ID
                - type: 요소 타입 (Title, NarrativeText, Table, etc.)
                - content: 청크 내용
                - metadata: 메타데이터 (페이지, 좌표, 계층 등)
        """
        logger.info(f"📄 Parsing PDF with Unstructured.io: {pdf_path}")
        logger.info(f"   Strategy: {self.strategy}, Extract images: {extract_images}")

        # 1. PDF 파싱 (Unstructured.io)
        elements = partition_pdf(
            filename=pdf_path,
            strategy=self.strategy,
            infer_table_structure=infer_table_structure,
            extract_images_in_pdf=extract_images,
            # 고급 옵션
            include_page_breaks=True,
            languages=["kor", "eng"],  # 한국어 + 영어
        )

        logger.info(f"✅ Extracted {len(elements)} elements")

        # 요소 타입별 통계
        element_types = {}
        for elem in elements:
            elem_type = type(elem).__name__
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        logger.info(f"📊 Element types: {element_types}")

        # 2. 보험 약관 구조 분석 및 메타데이터 추가
        enriched_elements = self._enrich_insurance_structure(elements)

        # 3. 의미 기반 청킹 (제목 기준)
        chunks = chunk_by_title(
            elements=enriched_elements,
            max_characters=self.max_characters,
            new_after_n_chars=self.new_after_n_chars,
            combine_text_under_n_chars=self.combine_text_under_n_chars,
            overlap=self.overlap,
        )

        logger.info(f"✅ Created {len(chunks)} semantic chunks")

        # 4. 청크를 딕셔너리로 변환
        result_chunks = []
        for idx, chunk in enumerate(chunks):
            chunk_dict = self._element_to_dict(chunk, chunk_id=f"chunk_{idx}")
            result_chunks.append(chunk_dict)

        logger.info(f"📦 Final chunk count: {len(result_chunks)}")

        return result_chunks

    def _enrich_insurance_structure(self, elements: List[Any]) -> List[Any]:
        """
        보험 약관의 계층 구조를 분석하여 메타데이터 추가

        계층:
        - level_0: 제N장 (Chapter)
        - level_1: 제N조 (Article)
        - level_2: ①②③ (Paragraph)
        - level_3: 1.가.- (List item)
        """
        current_chapter = None
        current_article = None
        current_paragraph = None

        for elem in elements:
            text = str(elem).strip()

            # 장 감지
            if self.CHAPTER_PATTERN.match(text):
                current_chapter = text
                current_article = None
                current_paragraph = None
                elem.metadata.category = "chapter"
                elem.metadata.hierarchy_level = 0
                elem.metadata.chapter = current_chapter

            # 조 감지
            elif self.ARTICLE_PATTERN.match(text):
                current_article = text
                current_paragraph = None
                elem.metadata.category = "article"
                elem.metadata.hierarchy_level = 1
                elem.metadata.chapter = current_chapter
                elem.metadata.article = current_article

            # 항 감지
            elif self.PARAGRAPH_PATTERN.match(text):
                current_paragraph = text[:2]  # ① 부분만
                elem.metadata.category = "paragraph"
                elem.metadata.hierarchy_level = 2
                elem.metadata.chapter = current_chapter
                elem.metadata.article = current_article
                elem.metadata.paragraph = current_paragraph

            # 리스트 감지
            elif self.LIST_PATTERN.match(text):
                elem.metadata.category = "list_item"
                elem.metadata.hierarchy_level = 3
                elem.metadata.chapter = current_chapter
                elem.metadata.article = current_article
                elem.metadata.paragraph = current_paragraph

            # 일반 텍스트
            else:
                # 컨텍스트 상속
                elem.metadata.chapter = current_chapter
                elem.metadata.article = current_article
                elem.metadata.paragraph = current_paragraph

        return elements

    def _element_to_dict(self, element: Any, chunk_id: str) -> Dict[str, Any]:
        """
        Unstructured element를 딕셔너리로 변환

        Returns:
            Dict with:
                - chunk_id: 청크 ID
                - type: 요소 타입
                - content: 내용
                - metadata: 페이지, 좌표, 계층 정보
        """
        # 기본 정보
        chunk = {
            "chunk_id": chunk_id,
            "type": type(element).__name__,
            "content": str(element),
        }

        # 메타데이터 추출
        metadata = {}
        if hasattr(element, "metadata"):
            meta = element.metadata

            # 페이지 정보
            if hasattr(meta, "page_number"):
                metadata["page"] = meta.page_number

            # 좌표 정보 (바운딩 박스)
            if hasattr(meta, "coordinates"):
                coords = meta.coordinates
                if coords:
                    metadata["coordinates"] = {
                        "points": coords.points if hasattr(coords, "points") else None,
                        "system": coords.system if hasattr(coords, "system") else None,
                    }

            # 보험 약관 계층 정보
            if hasattr(meta, "category"):
                metadata["category"] = meta.category
            if hasattr(meta, "hierarchy_level"):
                metadata["hierarchy_level"] = meta.hierarchy_level
            if hasattr(meta, "chapter"):
                metadata["chapter"] = meta.chapter
            if hasattr(meta, "article"):
                metadata["article"] = meta.article
            if hasattr(meta, "paragraph"):
                metadata["paragraph"] = meta.paragraph

            # 기타 메타데이터
            if hasattr(meta, "filename"):
                metadata["filename"] = meta.filename
            if hasattr(meta, "file_directory"):
                metadata["file_directory"] = meta.file_directory
            if hasattr(meta, "languages"):
                metadata["languages"] = meta.languages

        chunk["metadata"] = metadata

        return chunk

    def analyze_document_structure(self, pdf_path: str) -> Dict[str, Any]:
        """
        문서 구조 분석 (청킹 전 미리보기)

        Returns:
            Dict with:
                - total_pages: 총 페이지 수
                - element_count: 요소 수
                - element_types: 요소 타입별 개수
                - chapters: 장 목록
                - articles: 조 목록
                - tables: 표 개수
        """
        logger.info(f"📊 Analyzing document structure: {pdf_path}")

        # PDF 파싱
        elements = partition_pdf(
            filename=pdf_path,
            strategy="fast",  # 빠른 분석
            infer_table_structure=True,
            languages=["kor", "eng"],
        )

        # 통계 수집
        element_types = {}
        chapters = []
        articles = []
        tables = 0
        pages = set()

        for elem in elements:
            # 요소 타입
            elem_type = type(elem).__name__
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

            # 페이지
            if hasattr(elem.metadata, "page_number"):
                pages.add(elem.metadata.page_number)

            # 내용 분석
            text = str(elem).strip()

            if self.CHAPTER_PATTERN.match(text):
                chapters.append(text)
            elif self.ARTICLE_PATTERN.match(text):
                articles.append(text)
            elif elem_type == "Table":
                tables += 1

        analysis = {
            "total_pages": len(pages),
            "element_count": len(elements),
            "element_types": element_types,
            "chapters": chapters,
            "articles": articles,
            "tables": tables,
        }

        logger.info(f"✅ Analysis complete:")
        logger.info(f"   Pages: {analysis['total_pages']}")
        logger.info(f"   Elements: {analysis['element_count']}")
        logger.info(f"   Chapters: {len(chapters)}")
        logger.info(f"   Articles: {len(articles)}")
        logger.info(f"   Tables: {tables}")

        return analysis


# Singleton instance
_chunker: Optional[UnstructuredInsuranceChunker] = None


def get_unstructured_chunker(
    strategy: str = "hi_res",
    **kwargs
) -> UnstructuredInsuranceChunker:
    """Get or create singleton chunker instance"""
    global _chunker
    if _chunker is None:
        _chunker = UnstructuredInsuranceChunker(strategy=strategy, **kwargs)
    return _chunker


if __name__ == "__main__":
    # 테스트
    import sys

    if len(sys.argv) < 2:
        print("Usage: python unstructured_chunker.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print("=" * 70)
    print("🧪 Unstructured Insurance Chunker Test")
    print("=" * 70)

    # 청킹
    chunker = get_unstructured_chunker(strategy="fast")

    # 문서 구조 분석
    print("\n📊 Document Structure Analysis:")
    analysis = chunker.analyze_document_structure(pdf_path)

    # 청킹 실행
    print("\n📦 Chunking:")
    chunks = chunker.parse_and_chunk(pdf_path)

    # 결과 출력
    print(f"\n✅ Created {len(chunks)} chunks")
    print("\n첫 3개 청크:")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Type: {chunk['type']}")
        print(f"Content: {chunk['content'][:200]}...")
        print(f"Metadata: {chunk['metadata']}")

    print("\n" + "=" * 70)
