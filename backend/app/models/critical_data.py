"""
Critical data models for exact extraction from insurance policies
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class AmountData(BaseModel):
    """Extracted monetary amount"""
    value: int = Field(..., description="Amount in Korean won (원)")
    original_text: str = Field(..., description="Original text that was matched")
    position: int = Field(..., description="Character position in text")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence (1.0 for rule-based)")


class PeriodData(BaseModel):
    """Extracted time period"""
    days: int = Field(..., description="Period in days")
    original_text: str = Field(..., description="Original text that was matched")
    original_unit: str = Field(..., description="Original unit (년/개월/주/일)")
    position: int = Field(..., description="Character position in text")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence")


class KCDCodeData(BaseModel):
    """Extracted KCD disease code"""
    code: str = Field(..., description="KCD code (e.g., C77, I21-I25)")
    original_text: str = Field(..., description="Original text that was matched")
    position: int = Field(..., description="Character position in text")
    is_valid: bool = Field(..., description="Whether code is valid (checked against KCD reference)")
    is_range: bool = Field(False, description="Whether this is a range (e.g., C00-C97)")
    start_code: Optional[str] = Field(None, description="Start code if range")
    end_code: Optional[str] = Field(None, description="End code if range")


class CriticalData(BaseModel):
    """Collection of all critical data extracted from a clause"""
    amounts: List[AmountData] = Field(default_factory=list, description="All monetary amounts found")
    periods: List[PeriodData] = Field(default_factory=list, description="All time periods found")
    kcd_codes: List[KCDCodeData] = Field(default_factory=list, description="All KCD codes found")

    def get_amount_values(self) -> List[int]:
        """Get list of amount values"""
        return [a.value for a in self.amounts]

    def get_period_days(self) -> List[int]:
        """Get list of period values in days"""
        return [p.days for p in self.periods]

    def get_kcd_code_strings(self) -> List[str]:
        """Get list of KCD code strings"""
        return [k.code for k in self.kcd_codes]

    def has_amounts(self) -> bool:
        """Check if any amounts were found"""
        return len(self.amounts) > 0

    def has_periods(self) -> bool:
        """Check if any periods were found"""
        return len(self.periods) > 0

    def has_kcd_codes(self) -> bool:
        """Check if any KCD codes were found"""
        return len(self.kcd_codes) > 0
