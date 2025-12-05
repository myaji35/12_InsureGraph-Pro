"""
Smart Insurance Learner - Orchestrator

모든 학습 전략을 통합하여 최적의 방법 자동 선택
- 증분 학습 (Incremental Learning)
- 템플릿 기반 학습 (Template-based Learning)
- 의미 기반 청킹 및 캐싱 (Semantic Chunking & Caching)

보험사별 공통으로 적용 가능한 지능형 학습 알고리즘
"""
from typing import Dict, Optional
from loguru import logger

from .incremental_learner import IncrementalLearner
from .template_matcher import TemplateMatcher, InsuranceTemplateExtractor
from .chunk_learner import SemanticChunkingLearner


class SmartInsuranceLearner:
    """
    스마트 보험 학습기

    모든 보험사에 공통으로 적용 가능한 지능형 학습 알고리즘
    상황에 따라 최적의 학습 전략을 자동으로 선택
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Args:
            redis_url: Redis 연결 URL
        """
        # 전략 객체 초기화
        self.incremental_learner = IncrementalLearner()
        self.template_matcher = TemplateMatcher()
        self.template_extractor = InsuranceTemplateExtractor()
        self.chunk_learner = SemanticChunkingLearner(redis_url)

        # 통계
        self.stats = {
            "total_documents": 0,
            "full_learning": 0,
            "incremental_learning": 0,
            "template_learning": 0,
            "cached_learning": 0,
            "total_cost_saved": 0.0
        }

    async def learn_document(
        self,
        document_id: str,
        text: str,
        insurer: str,
        product_type: str,
        full_learning_callback=None
    ) -> Dict:
        """
        문서를 지능적으로 학습

        Args:
            document_id: 문서 ID
            text: 문서 텍스트
            insurer: 보험사
            product_type: 상품 유형
            full_learning_callback: 전체 학습 콜백 함수

        Returns:
            학습 결과
        """
        self.stats["total_documents"] += 1

        logger.info(f"[{document_id[:8]}] Smart learning started for {insurer} - {product_type}")

        # ==========================================
        # 전략 1: 템플릿 매칭 시도 (우선순위 가장 높음)
        # 95% 비용 절감 가능
        # ==========================================
        template_match = await self.template_matcher.match_template(
            text,
            insurer,
            product_type
        )

        if template_match and template_match.get("matched"):
            logger.info(f"[{document_id[:8]}] ✅ Template matched! Using template-based learning")

            # 변수만 학습
            learning_result = await self.template_matcher.learn_variables_only(
                template_match["variables"]
            )

            self.stats["template_learning"] += 1
            self.stats["total_cost_saved"] += 0.95

            return {
                "strategy": "template",
                "priority": 1,
                "match_score": template_match["match_score"],
                "cost_saving": 0.95,
                "cost_saving_percent": "95%",
                **learning_result
            }

        # ==========================================
        # 전략 2: 증분 학습 시도 (우선순위 2)
        # 80-90% 비용 절감 가능
        # ==========================================
        previous_version = await self.incremental_learner.check_previous_version(
            document_id,
            text,
            insurer,
            product_type
        )

        if previous_version:
            logger.info(f"[{document_id[:8]}] ✅ Previous version found! Trying incremental learning")

            # 실제 학습 콜백
            async def fallback_full_learning(full_text):
                if full_learning_callback:
                    return await full_learning_callback(full_text)
                return {"method": "full", "text_length": len(full_text)}

            incremental_result = await self.incremental_learner.learn_incrementally(
                document_id,
                text,
                previous_version,
                fallback_full_learning
            )

            # 증분 학습이 성공했다면
            if incremental_result["method"] == "incremental":
                self.stats["incremental_learning"] += 1
                self.stats["total_cost_saved"] += incremental_result["cost_saving"]

                return {
                    "strategy": "incremental",
                    "priority": 2,
                    **incremental_result
                }

        # ==========================================
        # 전략 3: 의미 기반 청킹 + 캐싱 (우선순위 3)
        # 70-80% 비용 절감 가능
        # ==========================================
        logger.info(f"[{document_id[:8]}] Using semantic chunking with caching")

        # 실제 청크 학습 콜백
        async def chunk_learning_callback(chunk_text: str) -> Dict:
            if full_learning_callback:
                return await full_learning_callback(chunk_text)
            # 기본 동작: 청크 해시만 반환
            return {
                "entities": [],
                "relationships": [],
                "chunk_hash": self.chunk_learner.calculate_chunk_hash(chunk_text)
            }

        chunking_result = await self.chunk_learner.learn_with_caching(
            text,
            document_id,
            chunk_learning_callback
        )

        self.stats["cached_learning"] += 1
        self.stats["total_cost_saved"] += chunking_result["cost_saving"]

        # 엔티티/관계 정보 집계
        total_entities = 0
        total_relationships = 0
        nodes_by_type = {}
        relationships_by_type = {}

        # chunking_result에서 learning_results 가져오기
        learning_results = chunking_result.get("learning_results", [])
        for result in learning_results:
            if isinstance(result.get("entities"), int):
                total_entities += result.get("entities", 0)
            if isinstance(result.get("relationships"), int):
                total_relationships += result.get("relationships", 0)

            # 노드 타입별 집계
            if "nodes_by_type" in result:
                for node_type, count in result["nodes_by_type"].items():
                    nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + count

            # 관계 타입별 집계
            if "relationships_by_type" in result:
                for rel_type, count in result["relationships_by_type"].items():
                    relationships_by_type[rel_type] = relationships_by_type.get(rel_type, 0) + count

        return {
            "strategy": "chunking",
            "priority": 3,
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "nodes_by_type": nodes_by_type,
            "relationships_by_type": relationships_by_type,
            **chunking_result
        }

    async def extract_and_cache_template(
        self,
        insurer: str,
        product_type: str,
        min_documents: int = 3
    ) -> Optional[Dict]:
        """
        보험사/상품 유형별 템플릿 추출 및 캐싱

        Args:
            insurer: 보험사
            product_type: 상품 유형
            min_documents: 최소 문서 수

        Returns:
            템플릿 정보 또는 None
        """
        logger.info(f"Extracting template for {insurer} - {product_type}")

        # 유사 문서들 찾기
        similar_docs = await self.incremental_learner.find_similar_documents(
            "",  # 빈 텍스트 (모든 문서 검색)
            insurer,
            limit=min_documents * 2
        )

        if len(similar_docs) < min_documents:
            logger.warning(f"Not enough documents ({len(similar_docs)}) to extract template")
            return None

        # 템플릿 추출
        template_info = await self.template_extractor.extract_template(
            similar_docs[:min_documents]
        )

        if template_info["template"]:
            # 템플릿 캐시에 저장
            self.template_matcher.cache_template(
                insurer,
                product_type,
                template_info
            )

            logger.info(f"✅ Template extracted and cached for {insurer} - {product_type}")

            return template_info

        return None

    def get_statistics(self) -> Dict:
        """
        학습 통계 조회

        Returns:
            학습 통계
        """
        total = self.stats["total_documents"]

        if total == 0:
            return {"status": "no_data"}

        avg_cost_saved = self.stats["total_cost_saved"] / total if total > 0 else 0

        return {
            "total_documents": total,
            "strategy_distribution": {
                "full_learning": self.stats["full_learning"],
                "incremental_learning": self.stats["incremental_learning"],
                "template_learning": self.stats["template_learning"],
                "cached_learning": self.stats["cached_learning"]
            },
            "total_cost_saved": self.stats["total_cost_saved"],
            "average_cost_saving_per_document": avg_cost_saved,
            "average_cost_saving_percent": f"{avg_cost_saved * 100:.1f}%"
        }

    async def optimize_insurer(
        self,
        insurer: str
    ) -> Dict:
        """
        특정 보험사의 모든 상품에 대해 템플릿 추출

        Args:
            insurer: 보험사명

        Returns:
            최적화 결과
        """
        logger.info(f"Optimizing all products for {insurer}")

        # TODO: DB에서 보험사의 모든 상품 유형 조회
        # 임시로 하드코딩
        product_types = [
            "종신보험",
            "정기보험",
            "연금보험",
            "CI보험",
            "건강보험"
        ]

        results = {}

        for product_type in product_types:
            template_info = await self.extract_and_cache_template(
                insurer,
                product_type,
                min_documents=3
            )

            results[product_type] = {
                "template_extracted": template_info is not None,
                "coverage_ratio": template_info["coverage_ratio"] if template_info else 0,
                "variable_count": template_info["variable_count"] if template_info else 0
            }

        logger.info(f"✅ Optimization completed for {insurer}")

        return {
            "insurer": insurer,
            "product_types_optimized": len([r for r in results.values() if r["template_extracted"]]),
            "product_types_total": len(product_types),
            "results": results
        }

    async def cleanup(self):
        """리소스 정리"""
        await self.chunk_learner.disconnect()
        logger.info("SmartInsuranceLearner resources cleaned up")


# 사용 예시
async def example_smart_learning():
    """스마트 학습 예시"""
    smart_learner = SmartInsuranceLearner()

    # 예시 1: 문서 학습
    result = await smart_learner.learn_document(
        document_id="doc123",
        text="제1장 총칙\n제1조 (목적)...",
        insurer="삼성화재",
        product_type="종신보험"
    )

    print(f"Strategy used: {result['strategy']}")
    print(f"Cost saving: {result['cost_saving_percent']}")

    # 예시 2: 보험사 전체 최적화
    optimization_result = await smart_learner.optimize_insurer("삼성화재")
    print(f"Optimized products: {optimization_result['product_types_optimized']}/{optimization_result['product_types_total']}")

    # 예시 3: 통계 조회
    stats = smart_learner.get_statistics()
    print(f"Average cost saving: {stats['average_cost_saving_percent']}")

    # 정리
    await smart_learner.cleanup()
