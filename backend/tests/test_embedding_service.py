"""
Unit tests for Embedding Service

Tests vector embedding generation for semantic search.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.graph.embedding_service import (
    EmbeddingService,
    OpenAIEmbeddingService,
    UpstageEmbeddingService,
    MockEmbeddingService,
    create_embedding_service,
)


class TestMockEmbeddingService:
    """Test suite for MockEmbeddingService"""

    @pytest.fixture
    def embedding_service(self):
        """Create mock embedding service"""
        return MockEmbeddingService(dimension=1536)

    @pytest.mark.asyncio
    async def test_embed_single(self, embedding_service):
        """Test embedding generation for single text"""
        text = "회사는 피보험자가 암으로 진단확정된 경우 보험금을 지급합니다."
        embedding = await embedding_service.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_embed_batch(self, embedding_service):
        """Test embedding generation for multiple texts"""
        texts = [
            "회사는 피보험자가 암으로 진단확정된 경우 보험금을 지급합니다.",
            "대기기간은 90일입니다.",
            "보험금은 1억원입니다.",
        ]

        embeddings = await embedding_service.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    @pytest.mark.asyncio
    async def test_embed_deterministic(self, embedding_service):
        """Test that embeddings are deterministic"""
        text = "테스트 텍스트"

        embedding1 = await embedding_service.embed(text)
        embedding2 = await embedding_service.embed(text)

        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_embed_different_texts(self, embedding_service):
        """Test that different texts produce different embeddings"""
        text1 = "첫 번째 텍스트"
        text2 = "두 번째 텍스트"

        embedding1 = await embedding_service.embed(text1)
        embedding2 = await embedding_service.embed(text2)

        assert embedding1 != embedding2

    def test_dimension(self, embedding_service):
        """Test dimension retrieval"""
        assert embedding_service.dimension() == 1536

    @pytest.mark.asyncio
    async def test_custom_dimension(self):
        """Test custom dimension"""
        service = MockEmbeddingService(dimension=768)
        embedding = await service.embed("test")

        assert len(embedding) == 768
        assert service.dimension() == 768


class TestOpenAIEmbeddingService:
    """Test suite for OpenAIEmbeddingService"""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client"""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        return mock_client

    @pytest.mark.asyncio
    async def test_embed_single(self, mock_openai_client):
        """Test OpenAI embedding generation"""
        with patch("app.services.graph.embedding_service.AsyncOpenAI") as mock_openai:
            mock_openai.return_value = mock_openai_client

            service = OpenAIEmbeddingService(api_key="test_key")
            text = "Test text"
            embedding = await service.embed(text)

            assert isinstance(embedding, list)
            assert len(embedding) == 1536
            mock_openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_batch(self, mock_openai_client):
        """Test OpenAI batch embedding generation"""
        with patch("app.services.graph.embedding_service.AsyncOpenAI") as mock_openai:
            # Mock batch response
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1] * 1536),
                Mock(embedding=[0.2] * 1536),
                Mock(embedding=[0.3] * 1536),
            ]
            mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_openai_client

            service = OpenAIEmbeddingService(api_key="test_key")
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = await service.embed_batch(texts)

            assert len(embeddings) == 3
            mock_openai_client.embeddings.create.assert_called_once()

    def test_dimension(self):
        """Test OpenAI embedding dimension"""
        service = OpenAIEmbeddingService(api_key="test_key")
        assert service.dimension() == 1536

    def test_initialization_without_api_key(self):
        """Test that service raises error without API key"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError):
                OpenAIEmbeddingService()

    def test_initialization_from_env(self):
        """Test initialization from environment variable"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env_key"}):
            service = OpenAIEmbeddingService()
            assert service.api_key == "env_key"


class TestUpstageEmbeddingService:
    """Test suite for UpstageEmbeddingService"""

    @pytest.mark.asyncio
    async def test_embed_single(self):
        """Test Upstage embedding generation"""
        with patch("app.services.graph.embedding_service.httpx.AsyncClient") as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 4096}]
            }
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=Mock(post=AsyncMock(return_value=mock_response))
            )
            mock_client.return_value.__aexit__ = AsyncMock()

            service = UpstageEmbeddingService(api_key="test_key")
            text = "Test text"
            embedding = await service.embed(text)

            assert isinstance(embedding, list)
            assert len(embedding) == 4096

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test Upstage batch embedding generation"""
        with patch("app.services.graph.embedding_service.httpx.AsyncClient") as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1] * 4096},
                    {"embedding": [0.2] * 4096},
                ]
            }
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=Mock(post=AsyncMock(return_value=mock_response))
            )
            mock_client.return_value.__aexit__ = AsyncMock()

            service = UpstageEmbeddingService(api_key="test_key")
            texts = ["Text 1", "Text 2"]
            embeddings = await service.embed_batch(texts)

            assert len(embeddings) == 2

    def test_dimension(self):
        """Test Upstage embedding dimension"""
        service = UpstageEmbeddingService(api_key="test_key")
        assert service.dimension() == 4096

    def test_initialization_without_api_key(self):
        """Test that service raises error without API key"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError):
                UpstageEmbeddingService()

    def test_initialization_from_env(self):
        """Test initialization from environment variable"""
        with patch.dict("os.environ", {"UPSTAGE_API_KEY": "env_key"}):
            service = UpstageEmbeddingService()
            assert service.api_key == "env_key"


class TestEmbeddingServiceFactory:
    """Test suite for embedding service factory"""

    def test_create_openai_service(self):
        """Test creating OpenAI service"""
        service = create_embedding_service("openai", api_key="test_key")
        assert isinstance(service, OpenAIEmbeddingService)

    def test_create_upstage_service(self):
        """Test creating Upstage service"""
        service = create_embedding_service("upstage", api_key="test_key")
        assert isinstance(service, UpstageEmbeddingService)

    def test_create_mock_service(self):
        """Test creating mock service"""
        service = create_embedding_service("mock", dimension=768)
        assert isinstance(service, MockEmbeddingService)
        assert service.dimension() == 768

    def test_create_unknown_provider(self):
        """Test that unknown provider raises error"""
        with pytest.raises(ValueError):
            create_embedding_service("unknown_provider")

    def test_create_with_kwargs(self):
        """Test factory with additional kwargs"""
        service = create_embedding_service("mock", dimension=512)
        assert service.dimension() == 512


class TestEmbeddingServiceAbstract:
    """Test suite for abstract EmbeddingService"""

    def test_abstract_methods(self):
        """Test that abstract methods cannot be instantiated"""
        with pytest.raises(TypeError):
            EmbeddingService()
