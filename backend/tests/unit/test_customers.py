"""
Unit Tests for Customer Management API

Task E: Backend Unit Tests
"""
import pytest
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal


class TestCustomerModels:
    """Test Customer Pydantic models."""

    def test_customer_create_valid(self):
        """Test creating valid CustomerCreate model."""
        from app.models.customer import CustomerCreate, Gender

        data = CustomerCreate(
            name="김철수",
            birth_year=1985,
            gender=Gender.M,
            phone="010-1234-5678",
            email="kim@example.com",
            occupation="회사원",
            consent_given=True,
        )

        assert data.name == "김철수"
        assert data.birth_year == 1985
        assert data.gender == Gender.M
        assert data.consent_given is True

    def test_customer_create_consent_required(self):
        """Test that consent_given is required and defaults to False."""
        from app.models.customer import CustomerCreate, Gender

        data = CustomerCreate(
            name="이영희",
            birth_year=1990,
            gender=Gender.F,
        )

        # consent_given should default to False if not provided
        assert data.consent_given is False


class TestCustomerPolicyModels:
    """Test Customer Policy models."""

    def test_policy_create_valid(self):
        """Test creating valid CustomerPolicyCreate model."""
        from app.models.customer import CustomerPolicyCreate, PolicyType, PolicyStatus

        data = CustomerPolicyCreate(
            policy_type=PolicyType.CANCER,
            insurer="삼성생명",
            policy_number="1234567890",
            coverage_amount=Decimal("100000000"),  # 1억
            premium=Decimal("50000"),  # 5만원
            start_date=date(2023, 1, 1),
            end_date=date(2033, 1, 1),
            status=PolicyStatus.ACTIVE,
        )

        assert data.policy_type == PolicyType.CANCER
        assert data.insurer == "삼성생명"
        assert data.coverage_amount == Decimal("100000000")
        assert data.status == PolicyStatus.ACTIVE


class TestCoverageSummary:
    """Test Coverage Summary models."""

    def test_coverage_summary(self):
        """Test CoverageSummary model."""
        from app.models.customer import CoverageSummary

        summary = CoverageSummary(
            total_coverage_amount=Decimal("300000000"),
            total_monthly_premium=Decimal("150000"),
            coverage_types=["암보험", "실손보험", "종신보험"],
            gaps=["치아보험 미가입", "운전자보험 미가입"],
            recommendations=["치아보험 추천", "운전자보험 추천"],
        )

        assert summary.total_coverage_amount == Decimal("300000000")
        assert len(summary.coverage_types) == 3
        assert len(summary.gaps) == 2
        assert "치아보험 추천" in summary.recommendations


class TestCustomerFilters:
    """Test Customer Filter models."""

    def test_customer_filter(self):
        """Test CustomerFilter model."""
        from app.models.customer import CustomerFilter, Gender

        filter_data = CustomerFilter(
            search="김",
            gender=Gender.M,
            min_age=30,
            max_age=50,
        )

        assert filter_data.search == "김"
        assert filter_data.gender == Gender.M
        assert filter_data.min_age == 30
        assert filter_data.max_age == 50


@pytest.mark.asyncio
class TestCustomerAPI:
    """Test Customer API endpoints (integration-style)."""

    async def test_customer_list_response_schema(self):
        """Test customer list response schema."""
        from app.models.customer import CustomerListResponse, CustomerResponse, Gender

        customers = [
            CustomerResponse(
                id=uuid4(),
                name="김철수",
                birth_year=1985,
                gender=Gender.M,
                age=39,
                policy_count=3,
                created_at=datetime.utcnow(),
            )
        ]

        response = CustomerListResponse(
            items=customers,
            total=1,
            page=1,
            page_size=20,
            has_more=False,
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert response.has_more is False
        assert response.items[0].name == "김철수"


# Fixtures
@pytest.fixture
def sample_customer_data():
    """Sample customer data."""
    return {
        "name": "박영희",
        "birth_year": 1990,
        "gender": "F",
        "phone": "010-9876-5432",
        "email": "park@example.com",
        "occupation": "자영업",
        "notes": "우량 고객",
        "consent_given": True,
    }


@pytest.fixture
def sample_policy_data():
    """Sample policy data."""
    return {
        "policy_type": "cancer",
        "insurer": "한화생명",
        "policy_number": "ABC123456",
        "coverage_amount": "50000000",
        "premium": "30000",
        "start_date": "2024-01-01",
        "end_date": "2034-01-01",
        "status": "active",
    }


@pytest.fixture
def sample_customer_with_policies():
    """Sample customer with policies."""
    return {
        "id": str(uuid4()),
        "name": "최민수",
        "birth_year": 1980,
        "gender": "M",
        "age": 44,
        "phone": "010-1111-2222",
        "email": "choi@example.com",
        "policy_count": 2,
        "policies": [
            {
                "id": str(uuid4()),
                "policy_type": "cancer",
                "insurer": "삼성생명",
                "coverage_amount": "100000000",
                "premium": "50000",
                "status": "active",
            },
            {
                "id": str(uuid4()),
                "policy_type": "health",
                "insurer": "KB손해보험",
                "coverage_amount": "30000000",
                "premium": "40000",
                "status": "active",
            },
        ],
        "created_at": datetime.utcnow().isoformat(),
    }
