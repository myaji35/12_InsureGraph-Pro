"""
PDF Text Extractor Service

PyMuPDF를 사용하여 PDF 파일에서 텍스트를 추출하는 서비스
"""
from typing import List, Dict, Optional
from pathlib import Path
import fitz  # PyMuPDF
from loguru import logger


class PDFPage:
    """단일 PDF 페이지 정보"""

    def __init__(
        self,
        page_num: int,
        text: str,
        width: float,
        height: float,
        char_count: int,
    ):
        self.page_num = page_num
        self.text = text
        self.width = width
        self.height = height
        self.char_count = char_count

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "page_num": self.page_num,
            "text": self.text,
            "width": self.width,
            "height": self.height,
            "char_count": self.char_count,
        }


class PDFExtractionResult:
    """PDF 추출 결과"""

    def __init__(
        self,
        total_pages: int,
        total_chars: int,
        pages: List[PDFPage],
        full_text: str,
        metadata: Dict,
    ):
        self.total_pages = total_pages
        self.total_chars = total_chars
        self.pages = pages
        self.full_text = full_text
        self.metadata = metadata

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "total_pages": self.total_pages,
            "total_chars": self.total_chars,
            "pages": [page.to_dict() for page in self.pages],
            "full_text": self.full_text,
            "metadata": self.metadata,
        }


class PDFTextExtractor:
    """PyMuPDF를 사용한 PDF 텍스트 추출기"""

    def __init__(self):
        """Initialize extractor"""
        pass

    def extract_text_from_file(
        self,
        pdf_path,
        max_pages=None,
    ):
        """
        PDF 파일에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로
            max_pages: 최대 추출 페이지 수 (None이면 전체)

        Returns:
            PDFExtractionResult: 추출 결과
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting text from PDF: {pdf_path.name}")

        try:
            doc = fitz.open(pdf_path)

            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "mod_date": doc.metadata.get("modDate", ""),
            }

            total_pages = len(doc)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

            pages = []
            full_text_parts = []
            total_chars = 0

            for page_num in range(pages_to_process):
                page = doc[page_num]
                text = page.get_text()
                char_count = len(text)
                total_chars += char_count

                rect = page.rect
                width = rect.width
                height = rect.height

                pdf_page = PDFPage(
                    page_num=page_num + 1,
                    text=text,
                    width=width,
                    height=height,
                    char_count=char_count,
                )

                pages.append(pdf_page)
                full_text_parts.append(text)

                logger.debug(
                    f"Page {page_num + 1}/{pages_to_process}: "
                    f"{char_count} chars, {width:.1f}x{height:.1f} pts"
                )

            doc.close()
            full_text = "\n\n".join(full_text_parts)

            result = PDFExtractionResult(
                total_pages=total_pages,
                total_chars=total_chars,
                pages=pages,
                full_text=full_text,
                metadata=metadata,
            )

            logger.info(
                f"Extracted {total_chars} characters from {pages_to_process}/{total_pages} pages"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise


_pdf_extractor = None


def get_pdf_extractor():
    """PDF 추출기 싱글톤 인스턴스 가져오기"""
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFTextExtractor()
    return _pdf_extractor
