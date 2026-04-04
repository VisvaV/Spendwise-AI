from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.ocr import perform_ocr
from app.services.categorization import categorizer
from app.services.fraud import calculate_risk_score

router = APIRouter()

class OCRRequest(BaseModel):
    receipt_image_url: str
    claimed_amount: float

class CategorizeRequest(BaseModel):
    title: str
    description: Optional[str] = None

class FraudRequest(BaseModel):
    employee_id: int
    amount: float
    category: str
    merchant: str
    date: str

@router.post("/ocr")
def run_ocr(req: OCRRequest):
    return perform_ocr(req.receipt_image_url, req.claimed_amount)

@router.post("/categorize")
def run_categorization(req: CategorizeRequest):
    return categorizer.categorize(req.title, req.description)

@router.post("/fraud-score")
def run_fraud_scoring(req: FraudRequest):
    return calculate_risk_score(
        req.employee_id, req.amount, req.category, req.merchant, req.date
    )
