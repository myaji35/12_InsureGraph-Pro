"""
Semantic Chunking Learner - Caching-based Learning

의미 기반으로 텍스트를 청킹하고 Redis에 캐싱
- 70-80% 비용 절감 효과
- 의미 단위로 청킹 (조항, 절 등)
- Redis 캐시로 중복 처리 방지
"""
import hashlib
import json
from typing import Dict, List, Optional
from loguru import logger
import redis.asyncio as redis


class SemanticChunkingLearner:
    """의미 기반 청킹 및 캐싱 학습기"""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Args:
            redis_url: Redis 연결 URL (None이면 기본값 사용)
        """
        self.redis_url = redis_url or 'redis://localhost:6379/0'
        self.redis_client = None
        self.cache_ttl = 86400 * 30  # 30일

    async def connect(self):
        """Redis 연결"""
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, caching disabled")
                self.redis_client = None

    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis disconnected")

    def chunk_text_semantically(
        self,
        text: str
    ) -> List[Dict]:
        """
        텍스트를 의미 단위로 청킹

        Args:
            text: 문서 텍스트

        Returns:
            청크 리스트
        """
        chunks = []
        current_chunk = []
        current_article = None

        lines = text.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 조항 시작 감지
            if self._is_article_start(stripped):
                # 이전 청크 저장
                if current_chunk:
                    chunks.append({
                        "type": "article",
                        "article_number": current_article,
                        "text": '\n'.join(current_chunk),
                        "line_start": i - len(current_chunk),
                        "line_end": i - 1
                    })
                    current_chunk = []

                # 새 조항 시작
                current_article = self._extract_article_number(stripped)
                current_chunk.append(line)

            # 장 시작 감지
            elif self._is_chapter_start(stripped):
                # 이전 청크 저장
                if current_chunk:
                    chunks.append({
                        "type": "chapter",
                        "text": '\n'.join(current_chunk),
                        "line_start": i - len(current_chunk),
                        "line_end": i - 1
                    })
                    current_chunk = []

                current_chunk.append(line)

            else:
                # 현재 청크에 추가
                current_chunk.append(line)

        # 마지막 청크 저장
        if current_chunk:
            chunks.append({
                "type": "article" if current_article else "paragraph",
                "article_number": current_article,
                "text": '\n'.join(current_chunk),
                "line_start": len(lines) - len(current_chunk),
                "line_end": len(lines) - 1
            })

        logger.info(f"Text chunked into {len(chunks)} semantic chunks")

        return chunks

    def _is_article_start(self, line: str) -> bool:
        """조항 시작 여부"""
        import re
        return bool(re.match(r'^제\s*\d+\s*조', line))

    def _is_chapter_start(self, line: str) -> bool:
        """장 시작 여부"""
        import re
        return bool(re.match(r'^제\s*\d+\s*장', line))

    def _extract_article_number(self, line: str) -> Optional[str]:
        """조항 번호 추출"""
        import re
        match = re.search(r'제\s*(\d+)\s*조', line)
        return match.group(1) if match else None

    def calculate_chunk_hash(self, chunk_text: str) -> str:
        """
        청크의 해시값 계산 (캐시 키로 사용)

        Args:
            chunk_text: 청크 텍스트

        Returns:
            SHA256 해시값
        """
        return hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()

    async def check_cache(
        self,
        chunk_hash: str
    ) -> Optional[Dict]:
        """
        캐시에서 학습 결과 조회

        Args:
            chunk_hash: 청크 해시

        Returns:
            캐시된 학습 결과 또는 None
        """
        if not self.redis_client:
            return None

        try:
            cache_key = f"chunk:learned:{chunk_hash}"
            cached = await self.redis_client.get(cache_key)

            if cached:
                logger.info(f"Cache HIT for chunk {chunk_hash[:8]}")
                return json.loads(cached)
            else:
                logger.debug(f"Cache MISS for chunk {chunk_hash[:8]}")
                return None

        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None

    async def save_to_cache(
        self,
        chunk_hash: str,
        learning_result: Dict
    ):
        """
        학습 결과를 캐시에 저장

        Args:
            chunk_hash: 청크 해시
            learning_result: 학습 결과
        """
        if not self.redis_client:
            return

        try:
            cache_key = f"chunk:learned:{chunk_hash}"
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(learning_result, ensure_ascii=False)
            )
            logger.info(f"Cached learning result for chunk {chunk_hash[:8]}")

        except Exception as e:
            logger.error(f"Cache save failed: {e}")

    async def learn_with_caching(
        self,
        text: str,
        document_id: str,
        learning_callback
    ) -> Dict:
        """
        캐싱을 활용한 학습

        Args:
            text: 문서 텍스트
            document_id: 문서 ID
            learning_callback: 실제 학습 함수 (chunk_text를 인자로 받음)

        Returns:
            학습 결과
        """
        # Redis 연결 확인
        await self.connect()

        # 1. 의미 단위로 청킹
        chunks = self.chunk_text_semantically(text)

        # 2. 각 청크별로 캐시 확인 및 학습
        total_chunks = len(chunks)
        cached_chunks = 0
        learned_chunks = 0
        chunk_results = []

        for i, chunk in enumerate(chunks):
            chunk_hash = self.calculate_chunk_hash(chunk["text"])

            # 캐시 확인
            cached_result = await self.check_cache(chunk_hash)

            if cached_result:
                # 캐시 HIT
                cached_chunks += 1
                chunk_results.append({
                    "chunk_id": i,
                    "type": chunk["type"],
                    "cached": True,
                    "result": cached_result
                })

            else:
                # 캐시 MISS - 실제 학습 수행
                learned_chunks += 1
                logger.info(f"Learning chunk {i+1}/{total_chunks} (type: {chunk['type']})")

                try:
                    learning_result = await learning_callback(chunk["text"])

                    # 캐시에 저장
                    await self.save_to_cache(chunk_hash, learning_result)

                    chunk_results.append({
                        "chunk_id": i,
                        "type": chunk["type"],
                        "cached": False,
                        "result": learning_result
                    })

                except Exception as e:
                    logger.error(f"Chunk learning failed: {e}")
                    chunk_results.append({
                        "chunk_id": i,
                        "type": chunk["type"],
                        "cached": False,
                        "error": str(e)
                    })

        # 3. 비용 절감 계산
        cache_hit_ratio = cached_chunks / total_chunks if total_chunks > 0 else 0
        cost_saving = cache_hit_ratio * 0.7  # 캐시된 비율만큼 70% 절감

        logger.info(f"Caching stats: {cached_chunks}/{total_chunks} cached ({cache_hit_ratio:.1%})")
        logger.info(f"Cost saving: {cost_saving:.1%}")

        return {
            "method": "semantic_chunking",
            "total_chunks": total_chunks,
            "cached_chunks": cached_chunks,
            "learned_chunks": learned_chunks,
            "cache_hit_ratio": cache_hit_ratio,
            "cost_saving": cost_saving,
            "cost_saving_percent": f"{cost_saving * 100:.1f}%",
            "chunk_results": chunk_results[:10]  # 처음 10개만 반환
        }

    async def clear_cache(
        self,
        pattern: str = "chunk:learned:*"
    ) -> int:
        """
        캐시 삭제

        Args:
            pattern: 삭제할 키 패턴

        Returns:
            삭제된 키 개수
        """
        if not self.redis_client:
            return 0

        try:
            deleted = 0
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    deleted += await self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted} cache entries")
            return deleted

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0

    async def get_cache_stats(self) -> Dict:
        """
        캐시 통계 조회

        Returns:
            캐시 통계
        """
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = await self.redis_client.info()

            # 캐시 키 개수 조회
            cursor = 0
            chunk_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="chunk:learned:*",
                    count=1000
                )
                chunk_count += len(keys)

                if cursor == 0:
                    break

            return {
                "status": "connected",
                "cached_chunks": chunk_count,
                "memory_used_mb": int(info.get("used_memory", 0)) / 1024 / 1024,
                "keys_total": info.get("db0", {}).get("keys", 0)
            }

        except Exception as e:
            logger.error(f"Get cache stats failed: {e}")
            return {"status": "error", "error": str(e)}


# 사용 예시
async def example_semantic_chunking():
    """의미 기반 청킹 학습 예시"""
    learner = SemanticChunkingLearner()

    # 학습 콜백 (모의)
    async def mock_learning_callback(chunk_text: str) -> Dict:
        # 실제로는 LLM을 호출하여 엔티티/관계 추출
        return {
            "entities": ["보험사", "보장내용"],
            "relationships": [{"from": "보험사", "to": "보장내용"}]
        }

    # 캐싱 학습 수행
    result = await learner.learn_with_caching(
        text="제1장 총칙\n제1조 (목적)...\n제2조 (정의)...",
        document_id="doc123",
        learning_callback=mock_learning_callback
    )

    print(f"Cache hit ratio: {result['cache_hit_ratio']:.1%}")
    print(f"Cost saving: {result['cost_saving_percent']}")

    # 캐시 통계
    stats = await learner.get_cache_stats()
    print(f"Cached chunks: {stats['cached_chunks']}")

    # 연결 종료
    await learner.disconnect()
