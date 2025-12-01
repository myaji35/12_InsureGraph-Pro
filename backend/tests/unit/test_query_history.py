"""
Unit Tests for Query History API

Task E: Backend Unit Tests
"""
import pytest
from uuid import uuid4
from datetime import datetime


class TestQueryHistoryModels:
    """Test Query History Pydantic models."""

    def test_query_history_create_valid(self):
        """Test creating valid QueryHistoryCreate model."""
        from app.models.query_history import QueryHistoryCreate

        data = QueryHistoryCreate(
            query_text="암보험 보장 내용은?",
            intent="coverage_check",
            answer="암보험은...",
            confidence=0.95,
            execution_time_ms=1500,
        )

        assert data.query_text == "암보험 보장 내용은?"
        assert data.intent == "coverage_check"
        assert data.confidence == 0.95
        assert data.execution_time_ms == 1500

    def test_query_history_create_minimal(self):
        """Test creating minimal QueryHistoryCreate model."""
        from app.models.query_history import QueryHistoryCreate

        data = QueryHistoryCreate(
            query_text="보험료는 얼마인가요?",
        )

        assert data.query_text == "보험료는 얼마인가요?"
        assert data.intent is None
        assert data.customer_id is None


class TestQueryHistoryStats:
    """Test Query History Statistics."""

    def test_stats_model(self):
        """Test QueryHistoryStats model."""
        from app.models.query_history import QueryHistoryStats

        stats = QueryHistoryStats(
            total_queries=100,
            queries_today=10,
            queries_this_week=45,
            queries_this_month=80,
            avg_confidence=0.85,
            avg_execution_time_ms=2000,
            top_intents=[
                {"intent": "search", "count": 50},
                {"intent": "coverage_check", "count": 30},
            ],
            queries_by_customer=[
                {"customer_id": str(uuid4()), "customer_name": "김철수", "query_count": 15}
            ],
        )

        assert stats.total_queries == 100
        assert stats.queries_today == 10
        assert len(stats.top_intents) == 2
        assert stats.top_intents[0]["intent"] == "search"


class TestQueryHistoryFilters:
    """Test Query History Filters."""

    def test_filters_model(self):
        """Test QueryHistoryFilters model."""
        from app.models.query_history import QueryHistoryFilters

        customer_id = str(uuid4())
        filters = QueryHistoryFilters(
            customer_id=customer_id,
            intent="search",
            search="보험",
            page=2,
            page_size=20,
        )

        assert filters.customer_id == customer_id
        assert filters.intent == "search"
        assert filters.search == "보험"
        assert filters.page == 2
        assert filters.page_size == 20


@pytest.mark.asyncio
class TestQueryHistoryAPI:
    """Test Query History API endpoints (integration-style)."""

    async def test_create_query_history_schema(self):
        """Test query history creation data schema."""
        from app.models.query_history import QueryHistoryCreate

        # Valid data
        data = QueryHistoryCreate(
            query_text="test query",
            intent="search",
            answer="test answer",
            confidence=0.9,
        )
        assert data.query_text == "test query"

    async def test_list_response_schema(self):
        """Test query history list response schema."""
        from app.models.query_history import QueryHistoryListResponse, QueryHistoryResponse

        response = QueryHistoryListResponse(
            items=[
                QueryHistoryResponse(
                    id=str(uuid4()),
                    query_text="test",
                    created_at=datetime.utcnow().isoformat(),
                )
            ],
            total=1,
            page=1,
            page_size=20,
            has_more=False,
        )

        assert response.total == 1
        assert len(response.items) == 1
        assert response.has_more is False


# Fixtures for testing
@pytest.fixture
def sample_query_history_data():
    """Sample query history data."""
    return {
        "query_text": "암보험 보장 범위는?",
        "intent": "coverage_check",
        "answer": "암보험은 암 진단 시 진단금과 치료비를 보장합니다.",
        "confidence": 0.92,
        "source_documents": [
            {"node_id": "node_1", "text": "암보험 약관 제1조", "article_num": "제1조"}
        ],
        "reasoning_path": {
            "graph_paths_count": 2,
            "paths": [{"path_length": 3, "relevance_score": 0.9}],
        },
        "execution_time_ms": 1850,
    }


@pytest.fixture
def sample_query_history_list():
    """Sample query history list."""
    return [
        {
            "id": str(uuid4()),
            "query_text": "보험료는 얼마인가요?",
            "intent": "search",
            "answer_preview": "보험료는 가입 조건에 따라...",
            "confidence": 0.88,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "query_text": "해지 환급금은?",
            "intent": "search",
            "answer_preview": "해지 환급금은 납입 기간과...",
            "confidence": 0.91,
            "created_at": datetime.utcnow().isoformat(),
        },
    ]
