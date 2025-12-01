"""
Customer and CustomerPolicy Models

Story 3.4: Customer Portfolio Management
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class Gender(str, Enum):
    """Gender enum"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class PolicyStatus(str, Enum):
    """Policy status enum"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class PolicyType(str, Enum):
    """Policy type enum"""
    LIFE = "life"
    HEALTH = "health"
    CAR = "car"
    HOME = "home"
    ACCIDENT = "accident"
    OTHER = "other"


# Customer Models

class CustomerBase(BaseModel):
    """Base customer model"""
    name: str = Field(..., min_length=1, max_length=100)
    birth_year: int = Field(..., ge=1900, le=2024)
    gender: Gender
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    occupation: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    consent_given: bool = False


class CustomerCreate(CustomerBase):
    """Create customer request"""
    pass


class CustomerUpdate(BaseModel):
    """Update customer request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_year: Optional[int] = Field(None, ge=1900, le=2024)
    gender: Optional[Gender] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    occupation: Optional[str] = Field(None, max_length=100)
    last_contact_date: Optional[datetime] = None
    notes: Optional[str] = None
    consent_given: Optional[bool] = None


class Customer(CustomerBase):
    """Customer response model"""
    id: UUID
    fp_user_id: UUID
    last_contact_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    age: int = 0
    policy_count: int = 0
    
    class Config:
        from_attributes = True


# Customer Policy Models

class CustomerPolicyBase(BaseModel):
    """Base customer policy model"""
    policy_name: str = Field(..., min_length=1, max_length=255)
    insurer: str = Field(..., min_length=1, max_length=100)
    policy_type: Optional[PolicyType] = None
    coverage_amount: Optional[int] = Field(None, ge=0)
    premium_amount: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class CustomerPolicyCreate(CustomerPolicyBase):
    """Create customer policy request"""
    customer_id: UUID


class CustomerPolicyUpdate(BaseModel):
    """Update customer policy request"""
    policy_name: Optional[str] = Field(None, min_length=1, max_length=255)
    insurer: Optional[str] = Field(None, min_length=1, max_length=100)
    policy_type: Optional[PolicyType] = None
    coverage_amount: Optional[int] = Field(None, ge=0)
    premium_amount: Optional[int] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[PolicyStatus] = None
    notes: Optional[str] = None


class CustomerPolicy(CustomerPolicyBase):
    """Customer policy response model"""
    id: UUID
    customer_id: UUID
    status: PolicyStatus
    document_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Extended models with relationships

class CustomerWithPolicies(Customer):
    """Customer with policies"""
    policies: List[CustomerPolicy] = []


# List response models

class CustomerListResponse(BaseModel):
    """Customer list response"""
    customers: List[Customer]
    total: int
    page: int
    page_size: int


# Coverage summary models

class CoverageSummary(BaseModel):
    """Coverage summary for a customer"""
    total_coverage: int = 0
    total_premium: int = 0
    active_policies: int = 0
    expired_policies: int = 0
    
    # Coverage by type
    coverage_by_type: dict[str, int] = {}
    
    # Gap analysis
    gaps: List[str] = []
    recommendations: List[str] = []


# Query filters

class CustomerFilter(BaseModel):
    """Customer filter for list queries"""
    search: Optional[str] = None  # Search name, email
    gender: Optional[Gender] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    has_policies: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
