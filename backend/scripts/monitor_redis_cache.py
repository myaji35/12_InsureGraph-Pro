"""
Redis 캐시 모니터링 유틸리티

SemanticChunkingLearner의 Redis 캐시 상태를 모니터링하고 관리
"""
import asyncio
from typing import Dict, List
from loguru import logger
import redis.asyncio as redis
from datetime import datetime


class RedisCacheMonitor:
    """Redis 캐시 모니터링 및 관리 유틸리티"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Args:
            redis_url: Redis 연결 URL
        """
        self.redis_url = redis_url
        self.redis_client = None

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
                logger.error(f"Redis connection failed: {e}")
                raise

    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis disconnected")

    async def get_overall_stats(self) -> Dict:
        """전체 캐시 통계 조회"""
        try:
            info = await self.redis_client.info()

            # 청크 캐시 키 개수
            chunk_count = 0
            cursor = 0
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
                "memory_peak_mb": int(info.get("used_memory_peak", 0)) / 1024 / 1024,
                "keys_total": info.get("db0", {}).get("keys", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }

        except Exception as e:
            logger.error(f"Failed to get overall stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """캐시 적중률 계산"""
        total = hits + misses
        if total == 0:
            return 0.0
        return hits / total

    async def get_chunk_samples(self, limit: int = 10) -> List[Dict]:
        """캐시된 청크 샘플 조회"""
        samples = []

        try:
            cursor = 0
            count = 0

            while count < limit:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="chunk:learned:*",
                    count=100
                )

                for key in keys:
                    if count >= limit:
                        break

                    try:
                        value = await self.redis_client.get(key)
                        ttl = await self.redis_client.ttl(key)

                        # 키 해시 추출
                        chunk_hash = key.split(":")[-1]

                        samples.append({
                            "chunk_hash": chunk_hash[:16] + "...",  # 처음 16자만
                            "ttl_seconds": ttl,
                            "ttl_days": ttl / 86400 if ttl > 0 else 0,
                            "value_length": len(value) if value else 0
                        })

                        count += 1

                    except Exception as e:
                        logger.warning(f"Failed to get sample for key {key}: {e}")
                        continue

                if cursor == 0:
                    break

            return samples

        except Exception as e:
            logger.error(f"Failed to get chunk samples: {e}")
            return []

    async def analyze_cache_efficiency(self) -> Dict:
        """캐시 효율성 분석"""
        stats = await self.get_overall_stats()

        if stats["status"] != "connected":
            return stats

        # 메모리당 키 수
        memory_mb = stats["memory_used_mb"]
        keys = stats["keys_total"]
        avg_key_size_kb = (memory_mb * 1024 / keys) if keys > 0 else 0

        # 캐시 효율성 평가
        efficiency_score = 0
        recommendations = []

        # 적중률 평가
        hit_rate = stats["hit_rate"]
        if hit_rate > 0.7:
            efficiency_score += 40
        elif hit_rate > 0.5:
            efficiency_score += 25
            recommendations.append("캐시 적중률이 낮습니다. 더 많은 문서를 처리하여 캐시 효율을 높이세요.")
        else:
            efficiency_score += 10
            recommendations.append("캐시 적중률이 매우 낮습니다. 템플릿 추출 또는 증분 학습을 활용하세요.")

        # 메모리 사용량 평가
        if memory_mb < 100:
            efficiency_score += 30
        elif memory_mb < 500:
            efficiency_score += 20
        else:
            efficiency_score += 10
            recommendations.append(f"메모리 사용량이 높습니다 ({memory_mb:.1f}MB). 오래된 캐시 정리를 고려하세요.")

        # 키 개수 평가
        if keys > 100:
            efficiency_score += 30
            recommendations.append(f"캐시가 잘 활용되고 있습니다 ({keys}개 키).")
        elif keys > 50:
            efficiency_score += 20
        else:
            efficiency_score += 10
            recommendations.append("캐시 키가 적습니다. 더 많은 문서 처리가 필요합니다.")

        return {
            "efficiency_score": efficiency_score,
            "efficiency_grade": self._get_grade(efficiency_score),
            "hit_rate": hit_rate,
            "memory_used_mb": memory_mb,
            "keys_total": keys,
            "avg_key_size_kb": avg_key_size_kb,
            "recommendations": recommendations
        }

    def _get_grade(self, score: int) -> str:
        """효율성 점수를 등급으로 변환"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 70:
            return "B (Good)"
        elif score >= 50:
            return "C (Fair)"
        else:
            return "D (Poor)"

    async def cleanup_expired_keys(self) -> int:
        """만료된 키 정리 (강제)"""
        deleted = 0

        try:
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="chunk:learned:*",
                    count=100
                )

                for key in keys:
                    ttl = await self.redis_client.ttl(key)

                    # TTL이 1일 미만인 키 삭제
                    if 0 < ttl < 86400:
                        await self.redis_client.delete(key)
                        deleted += 1

                if cursor == 0:
                    break

            logger.info(f"Cleaned up {deleted} expired keys")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    async def print_report(self):
        """모니터링 리포트 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("Redis Cache Monitoring Report")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 전체 통계
        stats = await self.get_overall_stats()

        if stats["status"] != "connected":
            logger.error(f"Redis connection failed: {stats.get('error')}")
            return

        logger.info("\n[Overall Statistics]")
        logger.info(f"  Status: {stats['status']}")
        logger.info(f"  Cached chunks: {stats['cached_chunks']}")
        logger.info(f"  Total keys: {stats['keys_total']}")
        logger.info(f"  Memory used: {stats['memory_used_mb']:.2f} MB")
        logger.info(f"  Memory peak: {stats['memory_peak_mb']:.2f} MB")
        logger.info(f"  Uptime: {stats['uptime_seconds'] / 3600:.1f} hours")
        logger.info(f"  Connected clients: {stats['connected_clients']}")
        logger.info(f"  Total commands: {stats['total_commands_processed']}")
        logger.info(f"  Cache hits: {stats['hits']}")
        logger.info(f"  Cache misses: {stats['misses']}")
        logger.info(f"  Hit rate: {stats['hit_rate']:.1%}")

        # 효율성 분석
        efficiency = await self.analyze_cache_efficiency()

        logger.info("\n[Cache Efficiency Analysis]")
        logger.info(f"  Efficiency score: {efficiency['efficiency_score']}/100")
        logger.info(f"  Efficiency grade: {efficiency['efficiency_grade']}")
        logger.info(f"  Average key size: {efficiency['avg_key_size_kb']:.2f} KB")

        if efficiency['recommendations']:
            logger.info("\n[Recommendations]")
            for i, rec in enumerate(efficiency['recommendations'], 1):
                logger.info(f"  {i}. {rec}")

        # 샘플 조회
        samples = await self.get_chunk_samples(limit=5)

        if samples:
            logger.info("\n[Cache Sample (5 entries)]")
            for i, sample in enumerate(samples, 1):
                logger.info(f"  {i}. Hash: {sample['chunk_hash']}, "
                           f"TTL: {sample['ttl_days']:.1f} days, "
                           f"Size: {sample['value_length']} bytes")

        logger.info("\n" + "=" * 80)


async def main():
    """메인 실행"""
    monitor = RedisCacheMonitor()

    try:
        await monitor.connect()

        # 리포트 출력
        await monitor.print_report()

    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        await monitor.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
