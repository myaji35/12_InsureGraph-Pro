"""
Query Embedder

사용자 질문을 벡터로 변환합니다.
"""
import time
from typing import List, Dict, Optional
from loguru import logger

from app.models.vector_search import EmbeddingRequest, EmbeddingResponse
from app.services.graph.embedding_service import (
    EmbeddingService,
    OpenAIEmbeddingService,
    UpstageEmbeddingService,
    MockEmbeddingService,
)


class QueryEmbedder:
    """
    쿼리 임베딩 생성기

    사용자 질문을 벡터로 변환하여 유사도 검색에 사용합니다.
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        cache_enabled: bool = True,
    ):
        """
        Args:
            embedding_service: 임베딩 서비스 (기본값: OpenAI)
            cache_enabled: 캐시 사용 여부
        """
        self.embedding_service = embedding_service or OpenAIEmbeddingService()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, List[float]] = {}

    async def embed_query(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        질문을 임베딩 벡터로 변환합니다.

        Args:
            request: 임베딩 요청

        Returns:
            임베딩 응답
        """
        start_time = time.time()
        cached = False

        # 캐시 확인
        cache_key = request.cache_key or request.text
        if self.cache_enabled and cache_key in self._cache:
            embedding = self._cache[cache_key]
            cached = True
            logger.debug(f"Using cached embedding for: {cache_key[:50]}...")
        else:
            # 임베딩 생성
            embedding = await self.embedding_service.embed_text(request.text)

            # 정규화
            if request.normalize:
                embedding = self._normalize_vector(embedding)

            # 캐시 저장
            if self.cache_enabled:
                self._cache[cache_key] = embedding

        generation_time_ms = (time.time() - start_time) * 1000

        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
            model=request.model,
            generation_time_ms=generation_time_ms,
            cached=cached,
        )

    async def embed_batch(
        self, texts: List[str], model: str = "openai", normalize: bool = True
    ) -> List[List[float]]:
        """
        여러 질문을 일괄 임베딩합니다.

        Args:
            texts: 텍스트 리스트
            model: 모델 이름
            normalize: 정규화 여부

        Returns:
            임베딩 벡터 리스트
        """
        embeddings = []

        for text in texts:
            request = EmbeddingRequest(text=text, model=model, normalize=normalize)
            response = await self.embed_query(request)
            embeddings.append(response.embedding)

        return embeddings

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        벡터를 L2 정규화합니다.

        Args:
            vector: 입력 벡터

        Returns:
            정규화된 벡터
        """
        magnitude = sum(x * x for x in vector) ** 0.5

        if magnitude == 0:
            return vector

        return [x / magnitude for x in vector]

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("Embedding cache cleared")

    def get_cache_size(self) -> int:
        """캐시 크기 반환"""
        return len(self._cache)

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        코사인 유사도 계산

        Args:
            vec1: 벡터 1
            vec2: 벡터 2

        Returns:
            코사인 유사도 (0~1)
        """
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}"
            )

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """
        유클리드 거리 계산

        Args:
            vec1: 벡터 1
            vec2: 벡터 2

        Returns:
            유클리드 거리
        """
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}"
            )

        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5


class QueryPreprocessor:
    """
    쿼리 전처리기

    임베딩 전에 질문을 전처리합니다.
    """

    @staticmethod
    def preprocess(query: str) -> str:
        """
        질문 전처리

        Args:
            query: 원본 질문

        Returns:
            전처리된 질문
        """
        # 공백 정리
        query = " ".join(query.split())

        # 소문자 변환 (선택적)
        # query = query.lower()

        # 특수문자 제거 (선택적)
        # query = re.sub(r'[^\w\s가-힣]', '', query)

        return query

    @staticmethod
    def expand_query(query: str, entities: List[str]) -> str:
        """
        쿼리 확장 (엔티티 추가)

        Args:
            query: 원본 질문
            entities: 추출된 엔티티

        Returns:
            확장된 질문
        """
        if not entities:
            return query

        # 엔티티를 질문에 추가
        expanded = query + " " + " ".join(entities)
        return expanded

    @staticmethod
    def generate_variations(query: str) -> List[str]:
        """
        쿼리 변형 생성

        Args:
            query: 원본 질문

        Returns:
            변형된 질문 리스트
        """
        variations = [query]

        # 종결어미 변형
        if query.endswith("?"):
            variations.append(query[:-1])

        # 존댓말/반말 변형 (간단한 예시)
        if "하나요" in query:
            variations.append(query.replace("하나요", "해"))
        if "인가요" in query:
            variations.append(query.replace("인가요", "인지"))

        return variations


class MultilingualQueryEmbedder(QueryEmbedder):
    """
    다국어 쿼리 임베딩 생성기

    언어별로 다른 임베딩 모델을 사용할 수 있습니다.
    """

    def __init__(
        self,
        korean_service: Optional[EmbeddingService] = None,
        english_service: Optional[EmbeddingService] = None,
        cache_enabled: bool = True,
    ):
        """
        Args:
            korean_service: 한국어 임베딩 서비스
            english_service: 영어 임베딩 서비스
            cache_enabled: 캐시 사용 여부
        """
        super().__init__(korean_service, cache_enabled)
        self.korean_service = korean_service or OpenAIEmbeddingService()
        self.english_service = english_service or OpenAIEmbeddingService()

    async def embed_query(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        언어를 감지하여 적절한 임베딩 서비스 사용

        Args:
            request: 임베딩 요청

        Returns:
            임베딩 응답
        """
        # 언어 감지
        language = self._detect_language(request.text)

        # 언어별 서비스 선택
        if language == "ko":
            self.embedding_service = self.korean_service
        else:
            self.embedding_service = self.english_service

        logger.debug(f"Detected language: {language}")

        return await super().embed_query(request)

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        간단한 언어 감지

        Args:
            text: 텍스트

        Returns:
            언어 코드 (ko/en)
        """
        # 한글 문자 비율로 판단
        korean_chars = sum(1 for c in text if "가" <= c <= "힣")
        total_chars = len([c for c in text if c.isalpha()])

        if total_chars == 0:
            return "ko"  # 기본값

        korean_ratio = korean_chars / total_chars

        return "ko" if korean_ratio > 0.3 else "en"
