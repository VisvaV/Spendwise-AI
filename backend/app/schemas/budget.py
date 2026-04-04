from pydantic import BaseModel
from typing import Optional

class BudgetBase(BaseModel):
    department_id: int
    fiscal_quarter: int
    fiscal_year: int
    total_amount: float
    alert_threshold: float = 0.8

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    reserved_amount: float
    consumed_amount: float

    class Config:
        from_attributes = True
