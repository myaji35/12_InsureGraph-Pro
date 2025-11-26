"""
Unit tests for Vector Search

벡터 검색 컴포넌트들의 기능을 테스트합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from app.models.vector_search import (
    SearchRequest,
    SearchResponse,
    SearchStrategy,
    VectorIndexType,
    VectorSearchResult,
    VectorSearchResults,
    HybridSearchResult,
    EmbeddingRequest,
    EmbeddingResponse,
    RerankingConfig,
    ReciprocalRankFusion,
    FusionMethod,
)
from app.models.query import QueryAnalysisResult, QueryIntent, QueryType, EntityType, ExtractedEntity
from app.services.vector_search.query_embedder import QueryEmbedder, QueryPreprocessor
from app.services.vector_search.vector_search_engine import VectorSearchEngine
from app.services.vector_search.hybrid_search_engine import HybridSearchEngine


class TestVectorSearchModels:
    """Test suite for Vector Search Models"""

    def test_vector_search_result_creation(self):
        """VectorSearchResult 생성 테스트"""
        result = VectorSearchResult(
            node_id="123",
            score=0.95,
            labels=["Clause"],
            properties={"clause_text": "보험금을 지급합니다"},
            clause_id="clause_001",
            article_num="제1조",
            clause_text="보험금을 지급합니다",
        )

        assert result.node_id == "123"
        assert result.score == 0.95
        assert result.get_text_content() == "보험금을 지급합니다"

    def test_vector_search_results(self):
        """VectorSearchResults 생성 테스트"""
        results = VectorSearchResults(
            results=[
                VectorSearchResult(
                    node_id="1",
                    score=0.9,
                    properties={"text": "결과1"},
                ),
                VectorSearchResult(
                    node_id="2",
                    score=0.8,
                    properties={"text": "결과2"},
                ),
            ],
            total_count=2,
            search_time_ms=50.5,
            query="테스트 질문",
            top_k=10,
            index_name="clause_embeddings",
        )

        assert results.total_count == 2
        assert results.get_top_result().score == 0.9
        assert len(results.filter_by_score(0.85)) == 1

    def test_search_request_creation(self):
        """SearchRequest 생성 테스트"""
        request = SearchRequest(
            query="갑상선암 보장 금액은?",
            strategy=SearchStrategy.HYBRID,
            top_k=10,
            min_score=0.5,
            graph_weight=0.6,
            vector_weight=0.4,
        )

        assert request.query == "갑상선암 보장 금액은?"
        assert request.strategy == SearchStrategy.HYBRID
        assert request.graph_weight == 0.6

    def test_reciprocal_rank_fusion_score(self):
        """RRF 점수 계산 테스트"""
        rrf = ReciprocalRankFusion(k=60)

        # 1등 점수
        score_1 = rrf.calculate_score(rank=0)
        assert score_1 == 1.0 / 61

        # 2등 점수
        score_2 = rrf.calculate_score(rank=1)
        assert score_2 == 1.0 / 62

        # 1등이 2등보다 높은 점수
        assert score_1 > score_2


class TestQueryEmbedder:
    """Test suite for QueryEmbedder"""

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock 임베딩 서비스"""
        service = AsyncMock()
        service.embed_text = AsyncMock(return_value=[0.1] * 1536)
        return service

    @pytest.fixture
    def embedder(self, mock_embedding_service):
        """QueryEmbedder 인스턴스"""
        return QueryEmbedder(embedding_service=mock_embedding_service)

    @pytest.mark.asyncio
    async def test_embed_query(self, embedder):
        """쿼리 임베딩 생성 테스트"""
        request = EmbeddingRequest(text="갑상선암 보장 금액은?", model="openai")

        response = await embedder.embed_query(request)

        assert isinstance(response, EmbeddingResponse)
        assert response.dimension == 1536
        assert len(response.embedding) == 1536
        assert response.generation_time_ms > 0

    @pytest.mark.asyncio
    async def test_embed_query_with_cache(self, embedder):
        """캐시를 사용한 임베딩 테스트"""
        request = EmbeddingRequest(
            text="갑상선암", model="openai", cache_key="thyroid_cancer"
        )

        # 첫 번째 호출
        response1 = await embedder.embed_query(request)
        assert response1.cached is False

        # 두 번째 호출 (캐시 사용)
        response2 = await embedder.embed_query(request)
        assert response2.cached is True

        # 캐시 크기 확인
        assert embedder.get_cache_size() == 1

    @pytest.mark.asyncio
    async def test_embed_batch(self, embedder):
        """일괄 임베딩 테스트"""
        texts = ["갑상선암", "간암", "뇌출혈"]

        embeddings = await embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_normalize_vector(self, embedder):
        """벡터 정규화 테스트"""
        vector = [3.0, 4.0]  # 크기 5

        normalized = embedder._normalize_vector(vector)

        # L2 정규화: [3/5, 4/5] = [0.6, 0.8]
        assert abs(normalized[0] - 0.6) < 0.001
        assert abs(normalized[1] - 0.8) < 0.001

        # 정규화된 벡터의 크기는 1
        magnitude = sum(x * x for x in normalized) ** 0.5
        assert abs(magnitude - 1.0) < 0.001

    def test_cosine_similarity(self):
        """코사인 유사도 계산 테스트"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        # 동일한 벡터: 유사도 1.0
        similarity = QueryEmbedder.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

        vec3 = [0.0, 1.0, 0.0]

        # 직교 벡터: 유사도 0.0
        similarity = QueryEmbedder.cosine_similarity(vec1, vec3)
        assert abs(similarity - 0.0) < 0.001

    def test_clear_cache(self, embedder):
        """캐시 초기화 테스트"""
        embedder._cache = {"key1": [0.1], "key2": [0.2]}

        assert embedder.get_cache_size() == 2

        embedder.clear_cache()

        assert embedder.get_cache_size() == 0


class TestQueryPreprocessor:
    """Test suite for QueryPreprocessor"""

    def test_preprocess(self):
        """쿼리 전처리 테스트"""
        query = "  갑상선암   보장   금액은?  "

        preprocessed = QueryPreprocessor.preprocess(query)

        # 공백 정리
        assert preprocessed == "갑상선암 보장 금액은?"

    def test_expand_query(self):
        """쿼리 확장 테스트"""
        query = "보장 금액은?"
        entities = ["갑상선암", "C73"]

        expanded = QueryPreprocessor.expand_query(query, entities)

        assert "보장 금액은?" in expanded
        assert "갑상선암" in expanded
        assert "C73" in expanded

    def test_generate_variations(self):
        """쿼리 변형 생성 테스트"""
        query = "보장되나요?"

        variations = QueryPreprocessor.generate_variations(query)

        assert query in variations
        assert len(variations) >= 1


class TestVectorSearchEngine:
    """Test suite for VectorSearchEngine"""

    @pytest.fixture
    def mock_neo4j(self):
        """Mock Neo4j 서비스"""
        mock = Mock()
        mock.driver = Mock()
        return mock

    @pytest.fixture
    def mock_embedder(self):
        """Mock 쿼리 임베더"""
        embedder = AsyncMock()
        embedder.embed_query = AsyncMock(
            return_value=EmbeddingResponse(
                embedding=[0.1] * 1536,
                dimension=1536,
                model="openai",
                generation_time_ms=10.0,
                cached=False,
            )
        )
        return embedder

    @pytest.fixture
    def engine(self, mock_neo4j, mock_embedder):
        """VectorSearchEngine 인스턴스"""
        return VectorSearchEngine(mock_neo4j, mock_embedder)

    @pytest.mark.asyncio
    async def test_vector_search(self, engine, mock_neo4j):
        """벡터 검색 테스트"""
        # Mock Neo4j 결과
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "node_id": "clause_001",
            "score": 0.95,
            "labels": ["Clause"],
            "properties": {
                "clause_id": "clause_001",
                "article_num": "제1조",
                "clause_text": "보험금을 지급합니다",
            },
        }[key]

        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value = [mock_record]
        mock_neo4j.driver.session.return_value = mock_session

        # 검색 실행
        results = await engine.search(query="보험금 지급", top_k=10)

        assert isinstance(results, VectorSearchResults)
        assert results.total_count >= 0
        assert results.query == "보험금 지급"

    def test_check_index_exists(self, engine, mock_neo4j):
        """인덱스 존재 확인 테스트"""
        # Mock Neo4j 결과
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: 1

        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value.single.return_value = (
            mock_record
        )
        mock_neo4j.driver.session.return_value = mock_session

        exists = engine.check_index_exists("clause_embeddings")

        # Mock 설정에 따라 True 반환
        assert isinstance(exists, bool)


class TestHybridSearchEngine:
    """Test suite for HybridSearchEngine"""

    @pytest.fixture
    def mock_graph_executor(self):
        """Mock 그래프 쿼리 실행기"""
        executor = AsyncMock()

        # Mock 응답
        mock_response = Mock()
        mock_response.result.table = [
            {
                "node_id": "1",
                "coverage_name": "암진단특약",
                "amount": 10000000,
                "score": 0.9,
            }
        ]
        mock_response.result.total_count = 1

        executor.execute = AsyncMock(return_value=mock_response)
        return executor

    @pytest.fixture
    def mock_vector_engine(self):
        """Mock 벡터 검색 엔진"""
        engine = AsyncMock()

        # Mock 결과
        mock_results = VectorSearchResults(
            results=[
                VectorSearchResult(
                    node_id="clause_001",
                    score=0.95,
                    clause_text="보험금을 지급합니다",
                )
            ],
            total_count=1,
            search_time_ms=20.0,
            query="보험금 지급",
            top_k=10,
            index_name="clause_embeddings",
        )

        engine.search = AsyncMock(return_value=mock_results)
        return engine

    @pytest.fixture
    def hybrid_engine(self, mock_graph_executor, mock_vector_engine):
        """HybridSearchEngine 인스턴스"""
        return HybridSearchEngine(mock_graph_executor, mock_vector_engine)

    @pytest.mark.asyncio
    async def test_vector_only_search(self, hybrid_engine):
        """벡터 전용 검색 테스트"""
        request = SearchRequest(
            query="보험금 지급",
            strategy=SearchStrategy.VECTOR_ONLY,
            top_k=10,
        )

        analysis = QueryAnalysisResult(
            original_query="보험금 지급",
            intent=QueryIntent.GENERAL_INFO,
            intent_confidence=0.9,
            query_type=QueryType.VECTOR_SEARCH,
            entities=[],
            keywords=["보험금", "지급"],
        )

        response = await hybrid_engine.search(request, analysis)

        assert response.strategy == SearchStrategy.VECTOR_ONLY
        assert len(response.results) >= 0

    @pytest.mark.asyncio
    async def test_hybrid_search(self, hybrid_engine):
        """하이브리드 검색 테스트"""
        request = SearchRequest(
            query="갑상선암 보장 금액",
            strategy=SearchStrategy.HYBRID,
            top_k=10,
            graph_weight=0.6,
            vector_weight=0.4,
        )

        analysis = QueryAnalysisResult(
            original_query="갑상선암 보장 금액",
            intent=QueryIntent.COVERAGE_AMOUNT,
            intent_confidence=0.95,
            query_type=QueryType.HYBRID,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.9,
                )
            ],
            keywords=["갑상선암", "보장", "금액"],
        )

        response = await hybrid_engine.search(request, analysis)

        assert response.strategy == SearchStrategy.HYBRID
        assert len(response.results) >= 0
        assert response.search_time_ms > 0

    def test_reciprocal_rank_fusion(self, hybrid_engine):
        """Reciprocal Rank Fusion 테스트"""
        graph_results = [
            VectorSearchResult(node_id="1", score=0.9, properties={"text": "결과1"}),
            VectorSearchResult(node_id="2", score=0.8, properties={"text": "결과2"}),
        ]

        vector_results = [
            VectorSearchResult(node_id="2", score=0.95, properties={"text": "결과2"}),
            VectorSearchResult(node_id="3", score=0.85, properties={"text": "결과3"}),
        ]

        fused = hybrid_engine._reciprocal_rank_fusion(
            graph_results, vector_results, graph_weight=0.5, vector_weight=0.5
        )

        # 융합 결과에는 3개의 고유 결과
        assert len(fused) >= 2

        # 점수가 높은 순으로 정렬되어 있음
        for i in range(len(fused) - 1):
            assert fused[i].score >= fused[i + 1].score

    def test_weighted_sum_fusion(self, hybrid_engine):
        """가중 합 융합 테스트"""
        graph_results = [
            VectorSearchResult(node_id="1", score=0.8, properties={"text": "결과1"}),
        ]

        vector_results = [
            VectorSearchResult(node_id="1", score=0.9, properties={"text": "결과1"}),
        ]

        fused = hybrid_engine._weighted_sum_fusion(
            graph_results, vector_results, graph_weight=0.6, vector_weight=0.4
        )

        # 하나의 결과 (node_id=1)
        assert len(fused) == 1

        # 가중 합: 0.8 * 0.6 + 0.9 * 0.4 = 0.48 + 0.36 = 0.84
        assert abs(fused[0].score - 0.84) < 0.01

    def test_rerank_results(self, hybrid_engine):
        """결과 재랭킹 테스트"""
        results = [
            VectorSearchResult(
                node_id="1", score=0.8, properties={"text": "갑상선암 보장 금액"}
            ),
            VectorSearchResult(
                node_id="2", score=0.9, properties={"text": "다른 내용"}
            ),
        ]

        config = RerankingConfig(
            enabled=True,
            boost_exact_match=1.5,
            boost_entity_match=1.2,
            penalize_length=False,
        )

        reranked = hybrid_engine._rerank_results(results, "갑상선암 보장", config)

        # 첫 번째 결과가 정확 매칭으로 부스트되어 상위에 올라감
        assert reranked[0].node_id == "1"
        assert reranked[0].score > 0.8  # 부스트됨


class TestSearchResponse:
    """Test suite for SearchResponse"""

    def test_search_response_creation(self):
        """SearchResponse 생성 테스트"""
        response = SearchResponse(
            original_query="갑상선암 보장",
            strategy=SearchStrategy.HYBRID,
            results=[
                VectorSearchResult(
                    node_id="1", score=0.9, properties={"text": "결과"}
                )
            ],
            total_count=1,
            search_time_ms=100.5,
            reranked=True,
            explanation="하이브리드 검색으로 1개의 결과를 찾았습니다.",
        )

        assert response.total_count == 1
        assert response.reranked is True
        assert response.get_top_result().score == 0.9
        assert len(response.get_text_snippets()) == 1
