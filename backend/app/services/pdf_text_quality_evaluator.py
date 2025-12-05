"""
PDF Text Extraction Quality Evaluator

여러 PDF 텍스트 추출 라이브러리를 시도하고 품질을 평가하여 최적의 결과를 선택합니다.
"""
import re
from typing import Dict, Tuple
from loguru import logger


class PDFTextQualityEvaluator:
    """PDF 텍스트 추출 품질 평가기"""

    @staticmethod
    def calculate_quality_score(text: str, total_pages: int) -> Dict[str, any]:
        """
        추출된 텍스트의 품질 점수를 계산합니다.

        Returns:
            Dict with:
                - score: 0-100 품질 점수
                - text_length: 텍스트 길이
                - avg_chars_per_page: 페이지당 평균 문자 수
                - korean_ratio: 한글 비율 (%)
                - english_ratio: 영문 비율 (%)
                - special_char_ratio: 특수문자 비율 (%)
                - empty_page_ratio: 빈 페이지 비율 (%)
                - has_broken_chars: 깨진 문자 감지
        """
        if not text or len(text.strip()) < 10:
            return {
                "score": 0,
                "text_length": 0,
                "avg_chars_per_page": 0,
                "korean_ratio": 0,
                "english_ratio": 0,
                "special_char_ratio": 0,
                "empty_page_ratio": 100,
                "has_broken_chars": False,
                "quality_level": "very_poor"
            }

        text_length = len(text)
        avg_chars_per_page = text_length / total_pages if total_pages > 0 else 0

        # 문자 유형별 개수 계산
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        digits = len(re.findall(r'[0-9]', text))
        spaces = len(re.findall(r'\s', text))
        special_chars = len(re.findall(r'[^\w\s가-힣]', text))

        total_chars = text_length
        korean_ratio = (korean_chars / total_chars * 100) if total_chars > 0 else 0
        english_ratio = (english_chars / total_chars * 100) if total_chars > 0 else 0
        special_char_ratio = (special_chars / total_chars * 100) if total_chars > 0 else 0

        # 깨진 문자 감지 (연속된 특수문자, 이상한 패턴)
        broken_char_patterns = [
            r'[■□○●◎◇◆△▲▽▼]{3,}',  # 연속된 특수 기호
            r'[\x00-\x1F]{2,}',  # 제어 문자
            r'[�]{1,}',  # 깨진 문자 기호
        ]
        has_broken_chars = any(re.search(pattern, text) for pattern in broken_char_patterns)

        # 빈 페이지 비율 추정 (페이지당 문자 수가 50자 미만인 경우)
        lines = text.split('\n')
        pages_estimate = max(1, total_pages)
        lines_per_page = len(lines) / pages_estimate
        empty_page_ratio = 0
        if avg_chars_per_page < 50:
            empty_page_ratio = (1 - avg_chars_per_page / 50) * 100

        # 품질 점수 계산 (0-100)
        score = 0

        # 1. 텍스트 길이 점수 (0-40점)
        if avg_chars_per_page >= 500:
            score += 40
        elif avg_chars_per_page >= 200:
            score += 30
        elif avg_chars_per_page >= 100:
            score += 20
        elif avg_chars_per_page >= 50:
            score += 10

        # 2. 문자 비율 점수 (0-30점)
        meaningful_ratio = korean_ratio + english_ratio
        if meaningful_ratio >= 70:
            score += 30
        elif meaningful_ratio >= 50:
            score += 20
        elif meaningful_ratio >= 30:
            score += 10

        # 3. 특수문자 비율 (0-20점) - 너무 많으면 감점
        if special_char_ratio < 10:
            score += 20
        elif special_char_ratio < 20:
            score += 15
        elif special_char_ratio < 30:
            score += 10
        elif special_char_ratio < 50:
            score += 5

        # 4. 깨진 문자 없음 (0-10점)
        if not has_broken_chars:
            score += 10

        # 품질 레벨 결정
        if score >= 80:
            quality_level = "excellent"
        elif score >= 60:
            quality_level = "good"
        elif score >= 40:
            quality_level = "fair"
        elif score >= 20:
            quality_level = "poor"
        else:
            quality_level = "very_poor"

        return {
            "score": round(score, 1),
            "text_length": text_length,
            "avg_chars_per_page": round(avg_chars_per_page, 1),
            "korean_ratio": round(korean_ratio, 1),
            "english_ratio": round(english_ratio, 1),
            "special_char_ratio": round(special_char_ratio, 1),
            "empty_page_ratio": round(empty_page_ratio, 1),
            "has_broken_chars": has_broken_chars,
            "quality_level": quality_level
        }

    @staticmethod
    def extract_with_pypdf2(pdf_path: str) -> Tuple[str, int]:
        """PyPDF2로 텍스트 추출"""
        import PyPDF2

        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)

                extracted_text = ""
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    extracted_text += page_text + "\n"

                return extracted_text, total_pages
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return "", 0

    @staticmethod
    def extract_with_pdfplumber(pdf_path: str) -> Tuple[str, int]:
        """pdfplumber로 텍스트 추출 (레이아웃 보존)"""
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                extracted_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

                return extracted_text, total_pages
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return "", 0

    @staticmethod
    def extract_with_pymupdf(pdf_path: str) -> Tuple[str, int]:
        """PyMuPDF (fitz)로 텍스트 추출 (빠르고 정확)"""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            extracted_text = ""
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                extracted_text += page_text + "\n"

            doc.close()
            return extracted_text, total_pages
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return "", 0

    @classmethod
    def extract_best_quality(cls, pdf_path: str) -> Dict[str, any]:
        """
        여러 알고리즘을 시도하고 가장 품질이 좋은 결과를 반환합니다.

        Returns:
            Dict with:
                - text: 추출된 텍스트
                - total_pages: 총 페이지 수
                - algorithm: 사용된 알고리즘
                - quality: 품질 평가 결과
                - all_attempts: 모든 시도 결과 (디버깅용)
        """
        algorithms = [
            ("PyPDF2", cls.extract_with_pypdf2),
            ("pdfplumber", cls.extract_with_pdfplumber),
            ("PyMuPDF", cls.extract_with_pymupdf),
        ]

        all_attempts = []
        best_result = None
        best_score = -1

        for algorithm_name, extract_func in algorithms:
            logger.info(f"Trying {algorithm_name} for text extraction...")

            try:
                text, total_pages = extract_func(pdf_path)

                if total_pages == 0:
                    logger.warning(f"{algorithm_name} returned 0 pages")
                    continue

                quality = cls.calculate_quality_score(text, total_pages)

                attempt = {
                    "algorithm": algorithm_name,
                    "text_length": quality["text_length"],
                    "quality_score": quality["score"],
                    "quality_level": quality["quality_level"]
                }
                all_attempts.append(attempt)

                logger.info(f"{algorithm_name}: score={quality['score']}, length={quality['text_length']}, level={quality['quality_level']}")

                # 최고 점수 결과 선택
                if quality["score"] > best_score:
                    best_score = quality["score"]
                    best_result = {
                        "text": text,
                        "total_pages": total_pages,
                        "algorithm": algorithm_name,
                        "quality": quality
                    }

                # Excellent 품질이면 더 시도하지 않음
                if quality["quality_level"] == "excellent":
                    logger.info(f"{algorithm_name} achieved excellent quality, stopping")
                    break

            except Exception as e:
                logger.error(f"{algorithm_name} failed: {e}")
                all_attempts.append({
                    "algorithm": algorithm_name,
                    "error": str(e)
                })

        if best_result:
            best_result["all_attempts"] = all_attempts
            logger.info(f"Best algorithm: {best_result['algorithm']} with score {best_result['quality']['score']}")
            return best_result
        else:
            logger.error("All extraction algorithms failed")
            return {
                "text": "",
                "total_pages": 0,
                "algorithm": "none",
                "quality": cls.calculate_quality_score("", 0),
                "all_attempts": all_attempts,
                "error": "All extraction methods failed"
            }
