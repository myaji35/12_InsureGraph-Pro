"""
Hybrid Document Processor

pdfplumber(무료)와 Upstage(유료)를 문서 특성에 따라 자동으로 선택하는 하이브리드 프로세서

전략:
1. simple: 파일 크기 기반 단순 선택
2. smart: 샘플링 + 복잡도 분석 (권장)
3. progressive: pdfplumber 시도 → 품질 검증 → 필요시 Upstage
4. ml: 머신러닝 기반 예측 (향후 구현)
"""
from typing import Dict, Any, Optional
from loguru import logger
import re

from app.services.streaming_pdf_processor import StreamingPDFProcessor
from app.services.upstage_document_parser import UpstageDocumentParser


class HybridDocumentProcessor:
    """하이브리드 PDF 추출 프로세서"""

    def __init__(
        self,
        strategy: str = "smart",
        complexity_threshold: int = 70,
        quality_threshold: float = 0.7,
        file_size_threshold_mb: float = 5.0
    ):
        """
        Initialize Hybrid Document Processor

        Args:
            strategy: 전략 선택 (simple, smart, progressive, ml)
            complexity_threshold: 복잡도 임계값 (0-100, 이상이면 Upstage)
            quality_threshold: 품질 임계값 (0.0-1.0, 미만이면 Upstage)
            file_size_threshold_mb: 파일 크기 임계값 (MB, simple 전략용)
        """
        self.strategy = strategy
        self.complexity_threshold = complexity_threshold
        self.quality_threshold = quality_threshold
        self.file_size_threshold = file_size_threshold_mb * 1024 * 1024

        self.pdfplumber_processor = StreamingPDFProcessor()
        self.upstage_parser = UpstageDocumentParser()

        # 통계 수집
        self.stats = {
            'total_docs': 0,
            'pdfplumber_used': 0,
            'upstage_used': 0,
            'total_pages': 0,
            'cost_saved': 0.0,
            'avg_complexity': 0.0,
            'avg_quality': 0.0
        }

        logger.info(
            f"하이브리드 프로세서 초기화: strategy={strategy}, "
            f"complexity_threshold={complexity_threshold}, "
            f"quality_threshold={quality_threshold}"
        )

    async def process_document(
        self,
        pdf_url: str,
        file_size: Optional[int] = None,
        force_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문서 처리 (하이브리드 방식)

        Args:
            pdf_url: PDF URL
            file_size: 파일 크기 (bytes, 선택)
            force_method: 강제 방법 지정 (pdfplumber, upstage)

        Returns:
            {
                'text': '추출된 텍스트',
                'total_pages': 페이지 수,
                'method': 'pdfplumber' or 'upstage',
                'hybrid_decision': 'pdfplumber' or 'upstage',
                'decision_reason': '선택 이유',
                'complexity_score': 복잡도 점수 (선택),
                'quality_score': 품질 점수 (선택),
                ...
            }
        """
        self.stats['total_docs'] += 1

        # 강제 방법 지정 시
        if force_method:
            logger.info(f"강제 방법 지정: {force_method}")
            return await self._extract_forced(pdf_url, force_method)

        # 전략별 처리
        if self.strategy == "simple":
            result = await self._extract_simple(pdf_url, file_size)
        elif self.strategy == "smart":
            result = await self._extract_smart(pdf_url)
        elif self.strategy == "progressive":
            result = await self._extract_progressive(pdf_url)
        elif self.strategy == "ml":
            result = await self._extract_ml(pdf_url)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        # 통계 업데이트
        self._update_stats(result)

        return result

    async def _extract_forced(
        self,
        pdf_url: str,
        method: str
    ) -> Dict[str, Any]:
        """강제 방법 지정"""

        if method == "upstage":
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True,
                smart_chunking=True
            )
        elif method == "pdfplumber":
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=False
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        result['hybrid_decision'] = method
        result['decision_reason'] = 'forced'

        return result

    async def _extract_simple(
        self,
        pdf_url: str,
        file_size: Optional[int]
    ) -> Dict[str, Any]:
        """
        전략 1: 파일 크기 기반 단순 선택

        5MB 이상 → Upstage
        5MB 미만 → pdfplumber
        """
        # 파일 크기 확인
        if file_size is None:
            file_size = await self.pdfplumber_processor._get_file_size(pdf_url)

        file_size_mb = file_size / 1024 / 1024

        if file_size > self.file_size_threshold:
            logger.info(
                f"[Simple] 파일 크기 {file_size_mb:.1f}MB > "
                f"{self.file_size_threshold/1024/1024:.1f}MB → Upstage"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'file_size={file_size_mb:.1f}MB'
        else:
            logger.info(
                f"[Simple] 파일 크기 {file_size_mb:.1f}MB <= "
                f"{self.file_size_threshold/1024/1024:.1f}MB → pdfplumber"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=False
            )
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'file_size={file_size_mb:.1f}MB'

        return result

    async def _extract_smart(self, pdf_url: str) -> Dict[str, Any]:
        """
        전략 2: 샘플링 + 복잡도 분석 (권장)

        1. 첫 2페이지 샘플링
        2. 복잡도 점수 계산
        3. 임계값 기준으로 선택
        """
        logger.info("[Smart] 샘플링 기반 복잡도 평가 시작")

        # 1. 첫 2페이지 샘플링
        try:
            sample_result = await self._extract_sample_pages(pdf_url, num_pages=2)
            sample_text = sample_result['text']
        except Exception as e:
            logger.warning(f"샘플링 실패: {e}, Upstage로 폴백")
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = 'sampling_failed'
            return result

        # 2. 복잡도 계산
        complexity = self._calculate_complexity(sample_text)

        logger.info(f"[Smart] 복잡도 점수: {complexity}/100")

        # 3. 복잡도에 따라 선택
        if complexity >= self.complexity_threshold:
            logger.info(
                f"[Smart] 복잡도 {complexity} >= {self.complexity_threshold} → Upstage"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True,
                smart_chunking=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'complexity={complexity}'
        else:
            logger.info(
                f"[Smart] 복잡도 {complexity} < {self.complexity_threshold} → pdfplumber"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=False
            )
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'complexity={complexity}'

        result['complexity_score'] = complexity

        return result

    async def _extract_progressive(self, pdf_url: str) -> Dict[str, Any]:
        """
        전략 3: 점진적 업그레이드

        1. pdfplumber로 시도
        2. 품질 검증
        3. 품질 낮으면 Upstage로 재처리
        """
        logger.info("[Progressive] 1단계: pdfplumber로 시도")

        # 1단계: pdfplumber 시도
        result = await self.pdfplumber_processor.process_pdf_streaming(
            pdf_url,
            use_upstage=False
        )

        # 2단계: 품질 검증
        quality = self._calculate_quality_score(result['text'])
        overall_quality = quality['overall_score']

        logger.info(f"[Progressive] 품질 점수: {overall_quality:.3f}")

        # 3단계: 품질이 낮으면 Upstage로 재처리
        if overall_quality < self.quality_threshold:
            logger.warning(
                f"[Progressive] 품질 {overall_quality:.3f} < {self.quality_threshold} "
                f"→ Upstage로 재처리"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True,
                smart_chunking=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'quality={overall_quality:.3f}'
            result['retry_from'] = 'pdfplumber'
        else:
            logger.info(
                f"[Progressive] 품질 {overall_quality:.3f} >= {self.quality_threshold} "
                f"→ pdfplumber 유지"
            )
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'quality={overall_quality:.3f}'

        result['quality_score_initial'] = overall_quality

        return result

    async def _extract_ml(self, pdf_url: str) -> Dict[str, Any]:
        """전략 4: ML 기반 (향후 구현)"""

        logger.warning("[ML] ML 모델 미구현, smart 전략으로 폴백")
        return await self._extract_smart(pdf_url)

    async def _extract_sample_pages(
        self,
        pdf_url: str,
        num_pages: int = 2
    ) -> Dict[str, Any]:
        """첫 N페이지 샘플링 (pdfplumber 사용)"""

        import httpx
        import io
        import pdfplumber

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content

        pdf_file = io.BytesIO(pdf_bytes)

        sample_text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages[:num_pages]):
                text = page.extract_text()
                if text:
                    sample_text += text + "\n"

        return {
            'text': sample_text,
            'pages_sampled': num_pages
        }

    def _calculate_complexity(self, sample_text: str) -> int:
        """
        복잡도 점수 계산 (0-100)

        점수가 높을수록 Upstage 사용 권장
        """
        if not sample_text:
            return 100  # 추출 실패 = 매우 복잡

        score = 0

        # 1. 한글 비율 (낮으면 OCR 품질 문제)
        korean_chars = sum(1 for c in sample_text if ord('가') <= ord(c) <= ord('힣'))
        korean_ratio = korean_chars / len(sample_text) if sample_text else 0

        if korean_ratio < 0.2:
            score += 35  # 한글 거의 없음 → OCR 필요
        elif korean_ratio < 0.4:
            score += 20  # 한글 적음

        # 2. 표 패턴 감지
        table_indicators = ['┌', '┐', '└', '┘', '│', '─', '┼', '┬', '┴', '├', '┤']
        table_count = sum(sample_text.count(char) for char in table_indicators)

        if table_count > 50:
            score += 25  # 표가 매우 많음
        elif table_count > 20:
            score += 15  # 표가 많음

        # 3. 조항 구조 인식
        articles = len(re.findall(r'제\d+조', sample_text))
        chapters = len(re.findall(r'제\d+장', sample_text))

        if articles < 2 and chapters < 1:
            score += 20  # 구조 인식 실패 → Upstage 필요

        # 4. 특수문자 비율
        special_chars = sum(1 for c in sample_text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(sample_text) if sample_text else 0

        if special_ratio > 0.4:
            score += 15  # 특수문자 많음 (레이아웃 깨짐)
        elif special_ratio > 0.3:
            score += 10

        # 5. 텍스트 밀도
        lines = [line for line in sample_text.split('\n') if line.strip()]
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

        if avg_line_length < 10:
            score += 10  # 줄이 너무 짧음 (레이아웃 문제)

        return min(score, 100)

    def _calculate_quality_score(self, text: str) -> Dict[str, float]:
        """품질 점수 계산 (0.0-1.0)"""

        if not text:
            return {
                'korean_ratio': 0.0,
                'structure_score': 0.0,
                'overall_score': 0.0
            }

        # 한글 비율
        korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
        korean_ratio = korean_chars / len(text) if text else 0

        # 구조 점수
        articles = len(re.findall(r'제\d+조', text))
        chapters = len(re.findall(r'제\d+장', text))
        structure_score = min((chapters * 2 + articles) / 50, 1.0)

        # 종합 점수
        overall = korean_ratio * 0.6 + structure_score * 0.4

        return {
            'korean_ratio': round(korean_ratio, 3),
            'structure_score': round(structure_score, 3),
            'overall_score': round(overall, 3)
        }

    def _update_stats(self, result: Dict[str, Any]):
        """통계 업데이트"""

        decision = result.get('hybrid_decision', 'unknown')
        pages = result.get('total_pages', 0)

        self.stats['total_pages'] += pages

        if decision == 'pdfplumber':
            self.stats['pdfplumber_used'] += 1
            # pdfplumber는 무료이므로 비용 절감
            # 평균 페이지당 $0.005 절감 가정
            self.stats['cost_saved'] += pages * 0.005

        elif decision == 'upstage':
            self.stats['upstage_used'] += 1

        # 복잡도 평균
        if 'complexity_score' in result:
            complexity = result['complexity_score']
            total = self.stats['total_docs']
            current_avg = self.stats['avg_complexity']
            self.stats['avg_complexity'] = (current_avg * (total - 1) + complexity) / total

        # 품질 평균
        if 'quality_score' in result:
            quality = result['quality_score']
            total = self.stats['total_docs']
            current_avg = self.stats['avg_quality']
            self.stats['avg_quality'] = (current_avg * (total - 1) + quality) / total

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""

        total = self.stats['total_docs']
        pdfplumber_ratio = (self.stats['pdfplumber_used'] / total * 100) if total > 0 else 0
        upstage_ratio = (self.stats['upstage_used'] / total * 100) if total > 0 else 0

        return {
            'total_documents': total,
            'total_pages': self.stats['total_pages'],
            'pdfplumber_used': self.stats['pdfplumber_used'],
            'pdfplumber_ratio': f"{pdfplumber_ratio:.1f}%",
            'upstage_used': self.stats['upstage_used'],
            'upstage_ratio': f"{upstage_ratio:.1f}%",
            'estimated_cost_saved': f"${self.stats['cost_saved']:.2f}",
            'avg_complexity': round(self.stats['avg_complexity'], 1),
            'avg_quality': round(self.stats['avg_quality'], 3),
            'strategy': self.strategy,
            'complexity_threshold': self.complexity_threshold,
            'quality_threshold': self.quality_threshold
        }

    def reset_stats(self):
        """통계 초기화"""

        self.stats = {
            'total_docs': 0,
            'pdfplumber_used': 0,
            'upstage_used': 0,
            'total_pages': 0,
            'cost_saved': 0.0,
            'avg_complexity': 0.0,
            'avg_quality': 0.0
        }

        logger.info("통계 초기화 완료")


# 사용 예시
async def example_usage():
    """하이브리드 프로세서 사용 예시"""

    # 1. 프로세서 생성
    processor = HybridDocumentProcessor(
        strategy="smart",           # 샘플링 기반 (권장)
        complexity_threshold=70,    # 70점 이상이면 Upstage
        quality_threshold=0.7       # 품질 0.7 미만이면 Upstage
    )

    # 2. 문서 처리
    pdf_urls = [
        "https://example.com/simple.pdf",
        "https://example.com/complex.pdf",
    ]

    for pdf_url in pdf_urls:
        result = await processor.process_document(pdf_url)

        print(f"\n문서: {pdf_url}")
        print(f"  선택: {result['hybrid_decision']}")
        print(f"  이유: {result['decision_reason']}")
        print(f"  페이지: {result['total_pages']}")
        print(f"  텍스트: {len(result['text']):,}자")

        if 'complexity_score' in result:
            print(f"  복잡도: {result['complexity_score']}/100")

    # 3. 통계 확인
    stats = processor.get_stats()
    print("\n" + "="*60)
    print("통계:")
    print(f"  총 문서: {stats['total_documents']}")
    print(f"  총 페이지: {stats['total_pages']}")
    print(f"  pdfplumber: {stats['pdfplumber_used']} ({stats['pdfplumber_ratio']})")
    print(f"  Upstage: {stats['upstage_used']} ({stats['upstage_ratio']})")
    print(f"  예상 절감 비용: {stats['estimated_cost_saved']}")
    print(f"  평균 복잡도: {stats['avg_complexity']}/100")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
