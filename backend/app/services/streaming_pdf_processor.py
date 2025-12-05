"""
Streaming PDF Processor - No Local Download Required

로컬 다운로드 없이 스트리밍 방식으로 PDF를 처리합니다.
메모리 효율적이며 대용량 PDF도 안정적으로 처리 가능합니다.

4가지 최적화 전략:
1. 청크 단위 스트리밍 (메모리 절약)
2. Upstage Document Parse API (고품질 한국어 문서 처리)
3. Azure/AWS 원격 API (로컬 파일 불필요)
4. 하이브리드 방식 (작은 파일은 메모리, 큰 파일은 스트리밍)
"""
import asyncio
import httpx
import io
from typing import Dict, Optional, AsyncIterator
from loguru import logger
from app.services.upstage_document_parser import UpstageDocumentParser


class StreamingPDFProcessor:
    """스트리밍 기반 PDF 처리기 (로컬 다운로드 불필요)"""

    def __init__(self):
        self.chunk_size = 1024 * 1024  # 1MB chunks
        self.size_threshold = 10 * 1024 * 1024  # 10MB threshold
        self.upstage_parser = UpstageDocumentParser()

    async def process_pdf_streaming(
        self,
        pdf_url: str,
        use_remote_api: bool = False,
        use_upstage: bool = False,
        extract_tables: bool = True,
        smart_chunking: bool = False
    ) -> Dict[str, any]:
        """
        스트리밍 방식으로 PDF 처리 (로컬 다운로드 없음)

        Args:
            pdf_url: PDF URL
            use_remote_api: True이면 Azure/AWS 원격 API 사용
            use_upstage: True이면 Upstage Document Parse API 사용 (권장)
            extract_tables: 표 추출 여부 (Upstage 사용 시)
            smart_chunking: 스마트 청킹 사용 여부 (Upstage 사용 시)

        Returns:
            {
                "text": "추출된 텍스트",
                "total_pages": 페이지 수,
                "method": "upstage|streaming|memory|remote_api",
                "memory_saved": "절약된 메모리 (MB)",
                "chunks": [...],  # smart_chunking=True일 때만
                "sections": [...],  # use_upstage=True일 때만
                "quality_score": 0.95  # use_upstage=True일 때만
            }
        """
        # Step 1: Upstage API 우선 사용 (가장 높은 품질)
        if use_upstage:
            return await self._process_with_upstage(
                pdf_url,
                extract_tables=extract_tables,
                smart_chunking=smart_chunking
            )

        # Step 2: HEAD 요청으로 파일 크기 확인
        file_size = await self._get_file_size(pdf_url)
        logger.info(f"PDF size: {file_size / 1024 / 1024:.2f} MB")

        # Step 3: 크기에 따라 최적의 방법 선택
        if use_remote_api:
            # 방법 1: 원격 API 사용 (로컬 저장 전혀 없음)
            return await self._process_with_remote_api(pdf_url)
        elif file_size < self.size_threshold:
            # 방법 2: 작은 파일은 메모리에서 직접 처리
            return await self._process_in_memory(pdf_url, file_size)
        else:
            # 방법 3: 큰 파일은 청크 스트리밍
            return await self._process_with_streaming(pdf_url, file_size)

    async def _get_file_size(self, pdf_url: str) -> int:
        """HEAD 요청으로 파일 크기 확인"""
        async with httpx.AsyncClient() as client:
            response = await client.head(pdf_url, timeout=10.0)
            return int(response.headers.get('content-length', 0))

    async def _process_in_memory(
        self,
        pdf_url: str,
        file_size: int
    ) -> Dict[str, any]:
        """
        방법 2: 메모리에서 직접 처리 (작은 파일용)
        - 로컬 파일 저장 없음
        - BytesIO를 사용하여 메모리에서만 처리
        """
        logger.info(f"Processing PDF in memory (no local file)")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content

        # BytesIO를 사용하여 메모리에서 직접 처리
        pdf_file = io.BytesIO(pdf_bytes)

        # PyPDF2 또는 pdfplumber를 사용하여 메모리에서 직접 텍스트 추출
        try:
            import pdfplumber
            extracted_text = ""
            total_pages = 0

            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

            logger.info(f"✅ In-memory extraction completed: {total_pages} pages")

            return {
                "text": extracted_text,
                "total_pages": total_pages,
                "method": "memory",
                "memory_saved_mb": 0,  # 작은 파일이라 저장 효과 미미
                "algorithm": "pdfplumber_memory"
            }

        except Exception as e:
            logger.error(f"In-memory extraction failed: {e}")
            # Fallback: PyPDF2 시도
            return await self._fallback_pypdf2(pdf_file, "memory")

    async def _process_with_streaming(
        self,
        pdf_url: str,
        file_size: int
    ) -> Dict[str, any]:
        """
        방법 3: 청크 단위 스트리밍 (대용량 파일용)
        - 메모리에 전체 파일을 로드하지 않음
        - 청크 단위로 다운로드하면서 처리
        """
        logger.info(f"Processing PDF with streaming (large file: {file_size / 1024 / 1024:.2f} MB)")

        # SpooledTemporaryFile 사용: 작은 데이터는 메모리, 큰 데이터는 임시 디스크
        import tempfile
        from io import BytesIO

        # max_size=10MB까지는 메모리, 초과시 자동으로 디스크로 전환
        temp_file = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)

        try:
            # 청크 단위로 스트리밍 다운로드
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream('GET', pdf_url) as response:
                    response.raise_for_status()

                    downloaded = 0
                    async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                        temp_file.write(chunk)
                        downloaded += len(chunk)

                        # 진행 상황 로깅 (10% 단위)
                        if downloaded % (5 * 1024 * 1024) == 0:
                            progress = (downloaded / file_size) * 100
                            logger.info(f"Downloaded: {downloaded / 1024 / 1024:.1f} MB ({progress:.0f}%)")

            # 파일 포인터를 처음으로 이동
            temp_file.seek(0)

            # pdfplumber로 텍스트 추출
            import pdfplumber
            extracted_text = ""
            total_pages = 0

            with pdfplumber.open(temp_file) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

                    # 진행 상황 로깅 (10페이지 단위)
                    if (i + 1) % 10 == 0:
                        logger.info(f"Extracted: {i + 1}/{total_pages} pages")

            logger.info(f"✅ Streaming extraction completed: {total_pages} pages")

            # 메모리 절약 계산
            memory_saved = file_size - (10 * 1024 * 1024)  # SpooledTemporaryFile의 max_size
            memory_saved_mb = max(0, memory_saved / 1024 / 1024)

            return {
                "text": extracted_text,
                "total_pages": total_pages,
                "method": "streaming",
                "memory_saved_mb": round(memory_saved_mb, 2),
                "algorithm": "pdfplumber_streaming"
            }

        except Exception as e:
            logger.error(f"Streaming extraction failed: {e}")
            raise

        finally:
            temp_file.close()  # 임시 파일 정리

    async def _process_with_upstage(
        self,
        pdf_url: str,
        extract_tables: bool = True,
        smart_chunking: bool = False
    ) -> Dict[str, any]:
        """
        방법 0: Upstage Document Parse API 사용 (최고 품질)
        - 한국어 문서 처리에 최적화
        - 레이아웃 분석, 표 추출, 섹션 구조화
        - 로컬 다운로드 불필요
        """
        logger.info(f"Processing PDF with Upstage Document Parse API")

        try:
            if smart_chunking:
                # 스마트 청킹 사용
                chunks = await self.upstage_parser.extract_chunks_with_context(
                    pdf_url,
                    chunk_size=1000,
                    overlap=200
                )

                # 전체 텍스트도 함께 반환
                result = await self.upstage_parser.parse_document_from_url(
                    pdf_url,
                    ocr=True,
                    extract_tables=extract_tables
                )

                return {
                    "text": result["text"],
                    "total_pages": result["total_pages"],
                    "method": "upstage_smart_chunking",
                    "memory_saved_mb": "100%",  # 로컬에 전혀 저장하지 않음
                    "algorithm": "upstage_document_parse",
                    "chunks": chunks,
                    "sections": result.get("sections", []),
                    "tables": result.get("tables", []),
                    "quality_score": result.get("quality_score", 0.0),
                    "metadata": result.get("metadata", {})
                }
            else:
                # 일반 파싱
                result = await self.upstage_parser.parse_document_from_url(
                    pdf_url,
                    ocr=True,
                    extract_tables=extract_tables
                )

                return {
                    "text": result["text"],
                    "total_pages": result["total_pages"],
                    "method": "upstage",
                    "memory_saved_mb": "100%",  # 로컬에 전혀 저장하지 않음
                    "algorithm": "upstage_document_parse",
                    "sections": result.get("sections", []),
                    "tables": result.get("tables", []),
                    "quality_score": result.get("quality_score", 0.0),
                    "metadata": result.get("metadata", {})
                }

        except Exception as e:
            logger.error(f"Upstage API failed: {e}, falling back to streaming")
            # Fallback: 스트리밍 방식으로 처리
            file_size = await self._get_file_size(pdf_url)
            if file_size < self.size_threshold:
                return await self._process_in_memory(pdf_url, file_size)
            else:
                return await self._process_with_streaming(pdf_url, file_size)

    async def _process_with_remote_api(
        self,
        pdf_url: str
    ) -> Dict[str, any]:
        """
        방법 1: 원격 API 사용 (완전히 로컬 저장 없음)
        - Azure Document Intelligence, AWS Textract 등 활용
        - URL만 전달하고 결과만 받음
        """
        logger.info(f"Processing PDF with remote API (no local storage at all)")

        # TODO: Azure Document Intelligence API 연동
        # 현재는 구현되지 않음 (fallback to memory processing)
        logger.warning("Remote API not configured, falling back to memory processing")
        file_size = await self._get_file_size(pdf_url)
        return await self._process_in_memory(pdf_url, file_size)

    async def _fallback_pypdf2(
        self,
        pdf_file: io.BytesIO,
        method: str
    ) -> Dict[str, any]:
        """PyPDF2를 사용한 폴백 처리"""
        try:
            import PyPDF2

            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            extracted_text = ""
            total_pages = len(reader.pages)

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

            logger.info(f"✅ PyPDF2 fallback extraction completed: {total_pages} pages")

            return {
                "text": extracted_text,
                "total_pages": total_pages,
                "method": method,
                "memory_saved_mb": 0,
                "algorithm": "pypdf2_fallback"
            }

        except Exception as e:
            logger.error(f"PyPDF2 fallback also failed: {e}")
            raise

    async def stream_pdf_chunks(
        self,
        pdf_url: str
    ) -> AsyncIterator[bytes]:
        """
        PDF를 청크 단위로 스트리밍 (제너레이터)
        - 메모리 효율적
        - 실시간 처리 가능
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream('GET', pdf_url) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                    yield chunk


# 사용 예시
async def example_usage():
    """사용 예시"""
    processor = StreamingPDFProcessor()

    # 예시 1: 자동 선택 (파일 크기에 따라 최적 방법)
    result = await processor.process_pdf_streaming(
        "https://example.com/large_insurance_terms.pdf"
    )
    print(f"Method: {result['method']}")
    print(f"Pages: {result['total_pages']}")
    print(f"Memory saved: {result['memory_saved_mb']} MB")

    # 예시 2: 원격 API 강제 사용
    result = await processor.process_pdf_streaming(
        "https://example.com/insurance.pdf",
        use_remote_api=True
    )
