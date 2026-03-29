from pydantic import BaseModel, Field
from typing import Optional


class BankProduct(BaseModel):
    bank_name: str
    product_name: str
    scheme: str = Field(..., description="Which govt scheme this product implements (KCC/MUDRA/etc)")
    interest_rate: str
    processing_fee: Optional[str] = None
    processing_time_days: int
    special_benefits: Optional[str] = None
    branch_availability: Optional[str] = None


class BankProducts(BaseModel):
    products: list[BankProduct] = Field(..., description="Bank-specific products for matched schemes")
    comparison_summary: str = Field(..., description="2-sentence comparison of best options")
