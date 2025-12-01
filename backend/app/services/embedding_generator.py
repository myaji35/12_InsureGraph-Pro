"""
Embedding Generation Service

Generates vector embeddings for insurance policy text using OpenAI's text-embedding-3-small model.
Each article, paragraph, and subclause gets its own embedding for semantic search.
"""
from dataclasses import dataclass
from typing import List, Optional
import hashlib
from openai import OpenAI
from app.core.config import settings
from app.services.legal_structure_parser import Article, Paragraph, Subclause


@dataclass
class TextEmbedding:
    """Represents a text embedding with metadata"""
    text: str
    embedding: List[float]
    text_hash: str  # MD5 hash for caching
    source_type: str  # "article", "paragraph", "subclause"
    source_id: str  # Unique identifier (e.g., "article_10", "paragraph_10_1")
    char_count: int

    @property
    def dimension(self) -> int:
        return len(self.embedding)


@dataclass
class EmbeddingResult:
    """Result of embedding generation for a document"""
    embeddings: List[TextEmbedding]
    total_embeddings: int
    total_tokens: int
    model: str

    def get_by_source_id(self, source_id: str) -> Optional[TextEmbedding]:
        """Get embedding by source ID"""
        for emb in self.embeddings:
            if emb.source_id == source_id:
                return emb
        return None

    def get_by_type(self, source_type: str) -> List[TextEmbedding]:
        """Get all embeddings of a specific type"""
        return [emb for emb in self.embeddings if emb.source_type == source_type]


class EmbeddingGenerator:
    """
    Generates embeddings for legal documents using OpenAI API.

    Features:
    - Hierarchical embedding: articles, paragraphs, subclauses
    - Batch processing for efficiency
    - Text hashing for cache/dedup
    - Token counting
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        use_mock: bool = False,
    ):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model to use
            batch_size: Number of texts per API call
            use_mock: Use mock embeddings for testing (default: False)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.batch_size = batch_size
        self.use_mock = use_mock or (self.api_key == "your-openai-api-key")

        if not self.use_mock:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def _compute_hash(self, text: str) -> str:
        """Compute MD5 hash of text for caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Use mock embeddings for testing
        if self.use_mock:
            import random
            random.seed(42)
            return [[random.random() for _ in range(1536)] for _ in texts]

        response = self.client.embeddings.create(
            input=texts,
            model=self.model,
        )

        # Extract embeddings in the same order as input
        embeddings = [data.embedding for data in response.data]
        return embeddings

    def generate_for_articles(self, articles: List[Article]) -> EmbeddingResult:
        """
        Generate embeddings for all articles and their hierarchical content.

        Creates embeddings for:
        1. Full article text (제N조 전체)
        2. Each paragraph (①, ②, ...)
        3. Each subclause (1., 2., 가., 나., ...)

        Args:
            articles: List of parsed articles

        Returns:
            EmbeddingResult with all embeddings
        """
        texts_to_embed = []
        metadata = []

        # Collect all texts with metadata
        for article in articles:
            # 1. Article-level embedding
            article_text = self._format_article_text(article)
            texts_to_embed.append(article_text)
            metadata.append({
                "source_type": "article",
                "source_id": f"article_{article.article_num}",
                "text": article_text,
            })

            # 2. Paragraph-level embeddings
            for para in article.paragraphs:
                para_text = self._format_paragraph_text(article, para)
                texts_to_embed.append(para_text)
                metadata.append({
                    "source_type": "paragraph",
                    "source_id": f"paragraph_{article.article_num}_{para.paragraph_num}",
                    "text": para_text,
                })

                # 3. Subclause-level embeddings
                for sub in para.subclauses:
                    sub_text = self._format_subclause_text(article, para, sub)
                    texts_to_embed.append(sub_text)
                    metadata.append({
                        "source_type": "subclause",
                        "source_id": f"subclause_{article.article_num}_{para.paragraph_num}_{sub.subclause_num}",
                        "text": sub_text,
                    })

        # Generate embeddings in batches
        all_embeddings = []
        total_tokens = 0

        for i in range(0, len(texts_to_embed), self.batch_size):
            batch_texts = texts_to_embed[i:i + self.batch_size]
            batch_embeddings = self._batch_embed(batch_texts)
            all_embeddings.extend(batch_embeddings)

            # Estimate tokens (rough: 1 token ≈ 4 chars)
            total_tokens += sum(len(text) // 4 for text in batch_texts)

        # Create TextEmbedding objects
        embeddings = []
        for meta, embedding in zip(metadata, all_embeddings):
            text_emb = TextEmbedding(
                text=meta["text"],
                embedding=embedding,
                text_hash=self._compute_hash(meta["text"]),
                source_type=meta["source_type"],
                source_id=meta["source_id"],
                char_count=len(meta["text"]),
            )
            embeddings.append(text_emb)

        return EmbeddingResult(
            embeddings=embeddings,
            total_embeddings=len(embeddings),
            total_tokens=total_tokens,
            model=self.model,
        )

    def _format_article_text(self, article: Article) -> str:
        """Format article for embedding (includes title and full content)"""
        title = f"[{article.title}]" if article.title else ""
        parts = [f"제{article.article_num}조 {title}"]

        # Add article text if exists
        if article.text:
            parts.append(article.text)

        # Add all paragraphs
        for para in article.paragraphs:
            parts.append(f"{para.paragraph_num} {para.text}")
            for sub in para.subclauses:
                parts.append(f"{sub.subclause_num}. {sub.text}")

        return "\n".join(parts)

    def _format_paragraph_text(self, article: Article, paragraph: Paragraph) -> str:
        """Format paragraph for embedding (includes article context)"""
        title = f"[{article.title}]" if article.title else ""
        return f"제{article.article_num}조 {title}\n{paragraph.paragraph_num} {paragraph.text}"

    def _format_subclause_text(
        self, article: Article, paragraph: Paragraph, subclause: Subclause
    ) -> str:
        """Format subclause for embedding (includes article + paragraph context)"""
        title = f"[{article.title}]" if article.title else ""
        return (
            f"제{article.article_num}조 {title}\n"
            f"{paragraph.paragraph_num} {paragraph.text}\n"
            f"{subclause.subclause_num}. {subclause.text}"
        )


# Singleton instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create singleton embedding generator instance"""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


if __name__ == "__main__":
    # Test with sample data
    from app.services.legal_structure_parser import get_legal_parser

    sample_text = """
제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.
"""

    print("=" * 70)
    print("🧪 Embedding Generator Test")
    print("=" * 70)

    # Parse text
    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    print(f"\n📄 Parsed {parsed.total_articles} articles")

    # Generate embeddings
    generator = get_embedding_generator()
    result = generator.generate_for_articles(parsed.articles)

    print(f"\n✅ Generated {result.total_embeddings} embeddings")
    print(f"   Model: {result.model}")
    print(f"   Estimated tokens: {result.total_tokens:,}")
    print(f"   Embedding dimension: {result.embeddings[0].dimension}")

    print(f"\n📊 Breakdown:")
    print(f"   - Articles: {len(result.get_by_type('article'))}")
    print(f"   - Paragraphs: {len(result.get_by_type('paragraph'))}")
    print(f"   - Subclauses: {len(result.get_by_type('subclause'))}")

    print(f"\n🔍 Sample embedding:")
    sample = result.embeddings[0]
    print(f"   Source: {sample.source_id}")
    print(f"   Type: {sample.source_type}")
    print(f"   Text: {sample.text[:100]}...")
    print(f"   Vector (first 5): {sample.embedding[:5]}")

    print("\n" + "=" * 70)
    print("✅ Embedding generation test complete!")
    print("=" * 70)
