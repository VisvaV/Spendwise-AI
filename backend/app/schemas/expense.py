from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExpenseBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "INR"
    category: str
    expense_date: datetime
    receipt_s3_url: Optional[str] = None
    business_justification: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    employee_id: int
    status: str
    submitted_at: Optional[datetime]
    risk_score: Optional[float]
    ai_category: Optional[str]
    duplicate_flag: bool

    class Config:
        from_attributes = True
