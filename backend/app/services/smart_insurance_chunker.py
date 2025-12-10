"""
Smart Insurance Document Chunker
보험 약관 특화 스마트 청킹 시스템 (테이블 보존)

Unstructured.io 개념 기반, pdfplumber 구현
"""
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import pdfplumber


class SmartInsuranceChunker:
    """보험 약관 특화 스마트 청킹 (테이블 보존)"""

    def __init__(
        self,
        max_chars: int = 1500,
        target_chars: int = 1200,
        min_chars: int = 200
    ):
        """
        Initialize Smart Chunker

        Args:
            max_chars: 청크 최대 크기
            target_chars: 청크 목표 크기
            min_chars: 청크 최소 크기 (이보다 작으면 병합)
        """
        self.max_chars = max_chars
        self.target_chars = target_chars
        self.min_chars = min_chars

    def parse_and_chunk(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        PDF 파싱 + 청킹 (표 보존)

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 출력 디렉토리 (선택)

        Returns:
            List[Dict]: 청크 리스트
        """
        logger.info(f"📄 PDF 파싱 중: {pdf_path}")

        # PDF 파싱 (페이지별)
        elements = self._extract_elements(pdf_path)

        logger.info(f"✅ {len(elements)}개 요소 추출 완료")

        # 요소 타입별 통계
        element_types = {}
        for elem in elements:
            elem_type = elem['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        logger.info(f"📊 요소 구성: {element_types}")

        # 제목 기반 청킹 (표 보존)
        chunks = self._chunk_by_structure(elements)

        logger.info(f"✅ {len(chunks)}개 청크 생성")

        # 저장 (선택)
        if output_dir:
            self._save_chunks(chunks, output_dir)

        return chunks

    def _extract_elements(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDF에서 요소 추출 (텍스트 + 표)

        Returns:
            List[Dict]: 요소 리스트
                - type: 'title', 'text', 'table', 'list'
                - content: 내용
                - page: 페이지 번호
                - metadata: 추가 정보
        """
        elements = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 1. 표 추출
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue

                        # 표를 텍스트로 변환
                        table_text = self._table_to_text(table)

                        elements.append({
                            'type': 'table',
                            'content': table_text,
                            'page': page_num,
                            'metadata': {
                                'table_index': table_idx,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0
                            }
                        })

                # 2. 텍스트 추출
                text = page.extract_text()
                if not text:
                    continue

                # 텍스트를 구조화된 요소로 분할
                text_elements = self._parse_text_structure(text, page_num)
                elements.extend(text_elements)

        # 페이지 순서대로 정렬
        elements.sort(key=lambda x: (x['page'], x.get('order', 0)))

        return elements

    def _table_to_text(self, table: List[List[str]]) -> str:
        """표를 텍스트로 변환 (마크다운 스타일)"""
        if not table:
            return ""

        lines = []

        # 헤더 (첫 번째 행)
        header = table[0]
        lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")

        # 데이터 행
        for row in table[1:]:
            lines.append("| " + " | ".join(str(cell or "") for cell in row) + " |")

        return "\n".join(lines)

    def _parse_text_structure(
        self,
        text: str,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """
        텍스트를 구조화된 요소로 분할

        보험 약관 구조:
        - 제N장 (Chapter)
        - 제N조 (Article)
        - 일반 텍스트
        """
        elements = []
        lines = text.split('\n')

        current_section = []
        current_type = 'text'
        order = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 장 패턴 감지
            if self._is_chapter(line):
                # 이전 섹션 저장
                if current_section:
                    elements.append({
                        'type': current_type,
                        'content': '\n'.join(current_section),
                        'page': page_num,
                        'order': order,
                        'metadata': {}
                    })
                    order += 1

                # 새 장 시작
                current_section = [line]
                current_type = 'chapter'

            # 조 패턴 감지
            elif self._is_article(line):
                # 이전 섹션 저장
                if current_section:
                    elements.append({
                        'type': current_type,
                        'content': '\n'.join(current_section),
                        'page': page_num,
                        'order': order,
                        'metadata': {}
                    })
                    order += 1

                # 새 조 시작
                current_section = [line]
                current_type = 'article'

            # 리스트 항목 감지
            elif self._is_list_item(line):
                if current_type != 'list':
                    # 이전 섹션 저장
                    if current_section:
                        elements.append({
                            'type': current_type,
                            'content': '\n'.join(current_section),
                            'page': page_num,
                            'order': order,
                            'metadata': {}
                        })
                        order += 1

                    current_section = [line]
                    current_type = 'list'
                else:
                    current_section.append(line)

            # 일반 텍스트
            else:
                current_section.append(line)

        # 마지막 섹션 저장
        if current_section:
            elements.append({
                'type': current_type,
                'content': '\n'.join(current_section),
                'page': page_num,
                'order': order,
                'metadata': {}
            })

        return elements

    def _is_chapter(self, line: str) -> bool:
        """장 패턴 감지: 제1장, 제2장 등"""
        return bool(re.match(r'^제\s*\d+\s*장', line))

    def _is_article(self, line: str) -> bool:
        """조 패턴 감지: 제1조, 제2조 등"""
        return bool(re.match(r'^제\s*\d+\s*조', line))

    def _is_list_item(self, line: str) -> bool:
        """리스트 항목 감지: 1., 가., ① 등"""
        patterns = [
            r'^\d+\.',  # 1., 2., 3.
            r'^[가-힣]\.',  # 가., 나., 다.
            r'^[①-⑳]',  # ①, ②, ③
            r'^-\s',  # - 항목
            r'^\*\s',  # * 항목
        ]
        return any(re.match(pattern, line) for pattern in patterns)

    def _chunk_by_structure(
        self,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        구조 기반 청킹 (제목 기반, 표 보존)

        전략:
        1. 표는 항상 독립 청크
        2. 장/조 단위로 청킹
        3. 크기 초과 시 분할
        4. 작은 청크는 병합
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for elem in elements:
            elem_length = len(elem['content'])

            # 표는 항상 독립 청크
            if elem['type'] == 'table':
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk))
                    current_chunk = []
                    current_length = 0

                # 표 청크 추가
                chunks.append(self._create_chunk([elem]))
                continue

            # 장/조 제목은 새 청크 시작
            if elem['type'] in ['chapter', 'article']:
                # 현재 청크가 목표 크기 이상이면 저장
                if current_length >= self.target_chars:
                    chunks.append(self._create_chunk(current_chunk))
                    current_chunk = []
                    current_length = 0

            # 청크에 추가
            current_chunk.append(elem)
            current_length += elem_length

            # 최대 크기 초과 시 분할
            if current_length >= self.max_chars:
                chunks.append(self._create_chunk(current_chunk))
                current_chunk = []
                current_length = 0

        # 마지막 청크 저장
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk))

        # 작은 청크 병합
        chunks = self._merge_small_chunks(chunks)

        return chunks

    def _create_chunk(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """요소들로부터 청크 생성"""
        if not elements:
            return None

        # 텍스트 결합
        text = '\n\n'.join(elem['content'] for elem in elements)

        # 메타데이터 수집
        types = [elem['type'] for elem in elements]
        pages = [elem['page'] for elem in elements]

        return {
            'text': text,
            'metadata': {
                'types': types,
                'page_start': min(pages),
                'page_end': max(pages),
                'is_table': 'table' in types,
                'has_chapter': 'chapter' in types,
                'has_article': 'article' in types,
                'length': len(text),
                'element_count': len(elements)
            }
        }

    def _merge_small_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """작은 청크를 이전 청크에 병합"""
        if not chunks:
            return chunks

        merged = [chunks[0]]

        for chunk in chunks[1:]:
            chunk_length = chunk['metadata']['length']

            # 작은 청크는 이전 청크에 병합
            if chunk_length < self.min_chars and not chunk['metadata']['is_table']:
                prev = merged[-1]
                prev['text'] += '\n\n' + chunk['text']
                prev['metadata']['length'] += chunk_length
                prev['metadata']['page_end'] = chunk['metadata']['page_end']
                prev['metadata']['element_count'] += chunk['metadata']['element_count']
            else:
                merged.append(chunk)

        return merged

    def _save_chunks(self, chunks: List[Dict[str, Any]], output_dir: str):
        """청크를 파일로 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        chunk_metadata = []

        for i, chunk in enumerate(chunks):
            # 텍스트 파일 저장
            text_file = output_path / f"chunk_{i:04d}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                # 헤더 정보
                f.write(f"[Chunk {i}]\n")
                f.write(f"Pages: {chunk['metadata']['page_start']}-{chunk['metadata']['page_end']}\n")
                f.write(f"Type: {', '.join(set(chunk['metadata']['types']))}\n")
                f.write(f"Length: {chunk['metadata']['length']} chars\n")
                f.write("\n" + "="*80 + "\n\n")

                # 내용
                f.write(chunk['text'])

            # 메타데이터 수집
            chunk_metadata.append({
                'chunk_id': i,
                'file': f"chunk_{i:04d}.txt",
                **chunk['metadata']
            })

        # 메타데이터 저장
        metadata_file = output_path / "chunks_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_metadata, f, ensure_ascii=False, indent=2)

        # 통계 저장
        stats = self._calculate_stats(chunks)
        stats_file = output_path / "chunks_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 저장 완료: {output_dir}")
        logger.info(f"   - 텍스트 청크: {len(chunks)}개")
        logger.info(f"   - 표 청크: {stats['table_chunks']}개")
        logger.info(f"   - 평균 크기: {stats['avg_length']:.0f} chars")

    def _calculate_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """청크 통계 계산"""
        if not chunks:
            return {}

        lengths = [chunk['metadata']['length'] for chunk in chunks]
        table_chunks = sum(1 for chunk in chunks if chunk['metadata']['is_table'])

        return {
            'total_chunks': len(chunks),
            'table_chunks': table_chunks,
            'text_chunks': len(chunks) - table_chunks,
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'total_length': sum(lengths)
        }


# 사용 예시
async def example_usage():
    """Smart Chunker 사용 예시"""

    chunker = SmartInsuranceChunker(
        max_chars=1500,
        target_chars=1200,
        min_chars=200
    )

    # PDF 파싱 + 청킹
    chunks = chunker.parse_and_chunk(
        pdf_path="sample_insurance.pdf",
        output_dir="graphrag_chunks/"
    )

    # 청크 확인
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i} ---")
        print(f"Pages: {chunk['metadata']['page_start']}-{chunk['metadata']['page_end']}")
        print(f"Type: {chunk['metadata']['types']}")
        print(f"Length: {chunk['metadata']['length']} chars")
        print(f"Is Table: {chunk['metadata']['is_table']}")
        print(f"Preview: {chunk['text'][:100]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
