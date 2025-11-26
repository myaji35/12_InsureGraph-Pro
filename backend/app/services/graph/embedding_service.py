"""
Embedding Service

Generates vector embeddings for semantic search.
Supports OpenAI and Upstage Solar embedding models.
"""
import os
from typing import List, Optional
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """Abstract embedding service"""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension"""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service using text-embedding-3-small"""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding service

        Args:
            api_key: OpenAI API key (defaults to env OPENAI_API_KEY)
            model: Embedding model name
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._dimension = 1536  # text-embedding-3-small dimension

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # OpenAI supports batch embedding (up to 2048 texts)
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise

    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


class UpstageEmbeddingService(EmbeddingService):
    """Upstage Solar embedding service"""

    def __init__(self, api_key: Optional[str] = None, model: str = "solar-embedding-1-large"):
        """
        Initialize Upstage embedding service

        Args:
            api_key: Upstage API key (defaults to env UPSTAGE_API_KEY)
            model: Embedding model name
        """
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        self.model = model
        self._dimension = 4096  # solar-embedding-1-large dimension

        if not self.api_key:
            raise ValueError("Upstage API key not provided")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            import httpx

            url = "https://api.upstage.ai/v1/solar/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "input": text,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                embedding = result["data"][0]["embedding"]
                return embedding

        except Exception as e:
            logger.error(f"Upstage embedding failed: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            import httpx

            url = "https://api.upstage.ai/v1/solar/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "input": texts,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                return embeddings

        except Exception as e:
            logger.error(f"Upstage batch embedding failed: {e}")
            raise

    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing"""

    def __init__(self, dimension: int = 1536):
        """
        Initialize mock embedding service

        Args:
            dimension: Embedding dimension
        """
        self._dimension = dimension

    async def embed(self, text: str) -> List[float]:
        """Generate mock embedding"""
        import hashlib

        # Generate deterministic embedding from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        import random

        random.seed(seed)
        embedding = [random.random() for _ in range(self._dimension)]

        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension


def create_embedding_service(
    provider: str = "openai", **kwargs
) -> EmbeddingService:
    """
    Factory function to create embedding service

    Args:
        provider: 'openai', 'upstage', or 'mock'
        **kwargs: Additional arguments for the service

    Returns:
        EmbeddingService instance
    """
    if provider == "openai":
        return OpenAIEmbeddingService(**kwargs)
    elif provider == "upstage":
        return UpstageEmbeddingService(**kwargs)
    elif provider == "mock":
        return MockEmbeddingService(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
