"""
FP Customer Models
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class FPCustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None  # 시
    district: Optional[str] = None  # 군구
    tags: List[str] = Field(default_factory=list)
    status: str = "prospect"  # active, inactive, prospect
    notes: Optional[str] = None


class FPCustomerCreate(FPCustomerBase):
    pass


class FPCustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class FPCustomer(FPCustomerBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsultationBase(BaseModel):
    customer_id: UUID
    consultation_date: datetime
    consultation_type: str  # phone, meeting, email
    subject: Optional[str] = None
    content: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class ConsultationCreate(ConsultationBase):
    pass


class Consultation(ConsultationBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerProductBase(BaseModel):
    customer_id: UUID
    product_name: str
    product_type: Optional[str] = None  # life, health, property
    insurer: Optional[str] = None
    policy_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    premium: Optional[float] = None
    coverage_amount: Optional[float] = None
    status: str = "active"
    notes: Optional[str] = None


class CustomerProductCreate(CustomerProductBase):
    pass


class CustomerProduct(CustomerProductBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class FPCustomerWithDetails(FPCustomer):
    """고객 + 상담이력 + 상품정보"""
    consultations: List[Consultation] = []
    products: List[CustomerProduct] = []
    consultation_count: int = 0
    product_count: int = 0
    last_contact_date: Optional[datetime] = None


class ProductMatchingRequest(BaseModel):
    """상품 매칭 분석 요청"""
    customer_id: UUID
    insurer: str
    product_type: str  # life, health, property


class ProductMatchingResponse(BaseModel):
    """AI 매칭 분석 결과"""
    customer_id: UUID
    customer_name: str
    insurer: str
    product_type: str
    matching_score: float  # 0-100
    reasons: List[str]
    recommendations: List[str]
