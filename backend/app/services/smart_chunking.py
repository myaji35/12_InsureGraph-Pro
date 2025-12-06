"""
Smart Chunking - 보험약관 문맥 유지하며 청킹하기

문제: 단순히 1000자씩 자르면 문맥 손실
해결: 조항 단위(제N조), 문장 단위로 스마트하게 자르기
"""
import re
from typing import List, Tuple
from loguru import logger


class SmartChunker:
    """보험약관을 의미 단위로 청킹"""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 200,
        overlap: int = 100
    ):
        """
        Args:
            max_chunk_size: 최대 청크 크기
            min_chunk_size: 최소 청크 크기
            overlap: 청크간 겹침 크기 (문맥 유지)
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, document_id: str = None) -> List[dict]:
        """
        텍스트를 스마트하게 청킹

        Returns:
            List of chunks with metadata
        """
        if not text or len(text) < self.min_chunk_size:
            return [{
                "text": text,
                "chunk_index": 0,
                "total_chunks": 1,
                "document_id": document_id,
                "chunk_type": "full_document"
            }]

        # 1. 조항 단위로 분리 시도
        chunks = self._chunk_by_articles(text)

        # 2. 조항이 없으면 문장 단위로 분리
        if not chunks or len(chunks) == 1:
            chunks = self._chunk_by_sentences(text)

        # 3. 메타데이터 추가
        result = []
        for idx, chunk_text in enumerate(chunks):
            result.append({
                "text": chunk_text,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "document_id": document_id,
                "chunk_type": self._detect_chunk_type(chunk_text),
                "start_char": text.find(chunk_text),
                "end_char": text.find(chunk_text) + len(chunk_text)
            })

        logger.info(f"Smart chunking: {len(text)} chars → {len(result)} chunks")
        return result

    def _chunk_by_articles(self, text: str) -> List[str]:
        """조항 단위로 청킹 (제N조, 제N장 etc.)"""

        # 조항 패턴: 제N조, 제N장, 제N절
        article_pattern = r'(제\s*\d+\s*[조장절])'

        # 조항 위치 찾기
        matches = list(re.finditer(article_pattern, text))

        if not matches or len(matches) < 2:
            # 조항이 너무 적으면 조항 기반 청킹 포기
            return []

        chunks = []
        for i in range(len(matches)):
            # 현재 조항 시작
            start = matches[i].start()

            # 다음 조항 시작 (마지막이면 텍스트 끝)
            end = matches[i+1].start() if i+1 < len(matches) else len(text)

            article_text = text[start:end].strip()

            # 조항이 너무 크면 분할
            if len(article_text) > self.max_chunk_size:
                # 큰 조항을 문장 단위로 분할
                sub_chunks = self._chunk_by_sentences(article_text)
                chunks.extend(sub_chunks)
            else:
                chunks.append(article_text)

        # Overlap 추가 (문맥 유지)
        chunks = self._add_overlap(chunks, text)

        return chunks

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """문장 단위로 청킹"""

        # 문장 종결 패턴: . ! ? 등
        sentence_pattern = r'([^.!?]+[.!?]+)'

        sentences = re.findall(sentence_pattern, text)

        if not sentences:
            # 문장 구분이 안되면 단순 분할
            return self._chunk_by_size(text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # 현재 청크에 문장 추가 시 크기 확인
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 새 청크 시작
                current_chunk = sentence

        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_by_size(self, text: str) -> List[str]:
        """단순 크기 기반 청킹 (최후의 수단)"""
        chunks = []

        for i in range(0, len(text), self.max_chunk_size - self.overlap):
            chunk = text[i:i + self.max_chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks

    def _add_overlap(self, chunks: List[str], full_text: str) -> List[str]:
        """청크간 겹침 추가 (문맥 유지)"""
        if len(chunks) <= 1 or self.overlap == 0:
            return chunks

        overlapped_chunks = [chunks[0]]  # 첫 청크는 그대로

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]

            # 이전 청크의 마지막 N글자를 현재 청크 앞에 추가
            overlap_text = prev_chunk[-self.overlap:] if len(prev_chunk) >= self.overlap else prev_chunk

            overlapped_chunk = overlap_text + "\n...\n" + current_chunk
            overlapped_chunks.append(overlapped_chunk)

        return overlapped_chunks

    def _detect_chunk_type(self, chunk_text: str) -> str:
        """청크 타입 감지"""
        if re.search(r'제\s*\d+\s*조', chunk_text):
            return "article"
        elif re.search(r'제\s*\d+\s*장', chunk_text):
            return "chapter"
        elif re.search(r'제\s*\d+\s*절', chunk_text):
            return "section"
        else:
            return "paragraph"


# 전역 인스턴스
_smart_chunker = None

def get_smart_chunker(
    max_chunk_size: int = 1000,
    min_chunk_size: int = 200,
    overlap: int = 100
) -> SmartChunker:
    """스마트 청킹 인스턴스 가져오기"""
    global _smart_chunker
    if _smart_chunker is None:
        _smart_chunker = SmartChunker(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            overlap=overlap
        )
    return _smart_chunker


def chunk_document(
    text: str,
    document_id: str = None,
    max_chunk_size: int = 1000
) -> List[dict]:
    """
    문서를 스마트하게 청킹 (간단한 인터페이스)

    Args:
        text: 원본 텍스트
        document_id: 문서 ID
        max_chunk_size: 최대 청크 크기

    Returns:
        List of chunk dictionaries
    """
    chunker = get_smart_chunker(max_chunk_size=max_chunk_size)
    return chunker.chunk_text(text, document_id=document_id)
